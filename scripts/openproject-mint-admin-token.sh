#!/usr/bin/env bash
# 17.D WP-01 T1.7 — mint OpenProject admin API token via Rails service
# and rotate into Vault at secret/openproject/api#token.
#
# Replaces the prior operator-UI workflow (My Account → Access tokens
# → Generate). OpenProject 15 has APITokens::CreateService server-side,
# so this is fully programmatic; no GUI required.
#
# Idempotent: if secret/openproject/api#token already validates against
# /api/v3/users/me, exit 0 without minting. Otherwise mint a fresh
# token, rotate Vault, verify.
#
# Doctrine:
#   - Hash-only verification (sha256[12]); never display token values
#   - Token never passes through argv (env or stdin only)
#   - Token never lands in shell history (no user paste)
#   - Run on Mac Mini
#
# WP-04 prerequisite (still applies, see docker/openproject/README.md
# "Connector authoring prerequisites"): the token minted here is
# admin-scoped. WP-04 must replace it with an iap-sync user-scoped
# token before the connector ships.

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
CONTAINER=openproject
TOKEN_NAME="iap-vault"        # APITokens::CreateContract requires presence
SECRET_PATH="secret/openproject/api"  # pragma: allowlist secret
VERIFY_URL="http://192.168.10.145:8086/api/v3/users/me"

source "$(dirname "$0")/lib/vault-admin-token.sh"
VAULT_TOKEN=$(resolve_admin_vault_token) || exit 2

log() { printf '[mint-admin-token] %s\n' "$*" >&2; }

sha256_prefix() { /usr/bin/shasum -a 256 | /usr/bin/awk '{print substr($1,1,12)}'; }

# verify_token: returns 0 iff the token in $1 successfully authenticates
# against /api/v3/users/me as an admin-capable user. Uses HTTP basic
# auth with username "apikey" (OpenProject API auth scheme). Token
# passed via env to curl's --user-agent? No — basic auth needs the
# credential pair. We construct the header ourselves to keep the token
# out of curl's argv, then pipe it into curl via stdin --config.
verify_token() {
    local token="$1"
    local b64_creds
    b64_creds=$(printf 'apikey:%s' "$token" | /usr/bin/base64)
    # --config reads curl args from stdin; the Authorization header
    # therefore never lands in argv / ps listings.
    local http_code
    http_code=$(printf 'header = "Authorization: Basic %s"\n' "$b64_creds" \
        | /usr/bin/curl -sS -o /dev/null -w '%{http_code}' \
            --config - \
            "$VERIFY_URL" || true)
    [ "$http_code" = "200" ]
}

# ── Step 1: idempotency check ─────────────────────────────────────────
log "step 1: checking existing token in Vault"
EXISTING=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault kv get -field=token "${SECRET_PATH}" 2>/dev/null || true)

if [ -n "${EXISTING}" ]; then
    EXISTING_HASH=$(printf '%s' "${EXISTING}" | sha256_prefix)
    log "  existing token present; sha256[12]=${EXISTING_HASH}"
    if verify_token "${EXISTING}"; then
        log "  ✅ existing token validates against ${VERIFY_URL}"
        log "  no action required (idempotent exit)"
        unset EXISTING
        exit 0
    fi
    log "  ⚠️  existing token is invalid (rebuild / rotation needed); will mint fresh"
fi
unset EXISTING

# ── Step 2: mint via Rails runner inside openproject container ────────
log "step 2: minting fresh API token via APITokens::CreateService"

# Rails one-liner. Outputs ONLY the plaintext token to stdout on
# success; errors to stderr; exits non-zero on any failure. The token
# only exists in @plain_value during the request that mints it (it's
# hashed on save), so we capture it inline.
#
# token_name uses a timestamp suffix so re-mints after invalidation
# don't trip the CreateContract uniqueness validation.
MINT_RUBY=$(cat <<'RUBY'
# OpenProject emits an INFO line ("Increasing database pool size to
# N to match max threads") to STDOUT during Rails boot — before any
# user code runs. Rails.logger.level=FATAL doesn't help (the message
# is from OpenProject, not Rails.logger). We bracket the token in a
# sentinel and extract it shell-side; this is robust to any boot
# chatter the runner emits.
TOKEN_SENTINEL_BEGIN = "__IAP_TOKEN_BEGIN__"
TOKEN_SENTINEL_END   = "__IAP_TOKEN_END__"
begin
  admin = User.where(admin: true).order(:id).first
  unless admin
    STDERR.puts "ERROR: no admin user found"
    exit 2
  end
  name = "iap-vault-#{Time.now.utc.strftime('%Y%m%d%H%M%S')}"
  result = APITokens::CreateService.new(user: admin).call(token_name: name)
  unless result.success?
    STDERR.puts "ERROR: APITokens::CreateService failed: #{result.errors.full_messages.join('; ')}"
    exit 3
  end
  plain = result.result.plain_value
  if plain.nil? || plain.empty?
    STDERR.puts "ERROR: plain_value empty after mint (model save path bug?)"
    exit 4
  end
  STDOUT.write("#{TOKEN_SENTINEL_BEGIN}#{plain}#{TOKEN_SENTINEL_END}")
rescue => e
  STDERR.puts "ERROR: #{e.class}: #{e.message}"
  exit 5
end
RUBY
)

# rails runner reads the script from argv. The ARG itself contains no
# secret (Ruby source only); the secret is in stdout. We capture stdout
# into a shell var without echoing.
#
# IMPORTANT: `docker exec` does NOT inherit env from the container's
# entrypoint shell — DATABASE_URL is set by sourcing /vault/secrets/
# credentials.env in the entrypoint, so a bare `docker exec` Rails
# process has no DB config and falls back to a Unix socket. Source
# credentials.env inside the exec so Rails can connect.
RAW_OUT=$(${DOCKER} exec "${CONTAINER}" \
    sh -c 'set -a && . /vault/secrets/credentials.env && set +a && exec bundle exec rails runner "$1"' \
    -- "${MINT_RUBY}" 2>/tmp/mint-err.$$) || {
    log "❌ rails runner failed (exit $?). stderr:"
    /bin/cat /tmp/mint-err.$$ >&2 || true
    /bin/rm -f /tmp/mint-err.$$
    exit 6
}
/bin/rm -f /tmp/mint-err.$$

# Extract token from sentinel-bracketed output (boot logging emits to
# stdout before our STDOUT.write fires).
NEW_TOKEN=$(printf '%s' "${RAW_OUT}" | /usr/bin/sed -n 's/.*__IAP_TOKEN_BEGIN__\(.*\)__IAP_TOKEN_END__.*/\1/p')
unset RAW_OUT

if [ -z "${NEW_TOKEN}" ]; then
    log "❌ rails runner returned no token between sentinels"
    exit 7
fi

NEW_HASH=$(printf '%s' "${NEW_TOKEN}" | sha256_prefix)
log "  ✅ token minted; sha256[12]=${NEW_HASH}"

# ── Step 3: write to Vault via stdin (token never in argv) ────────────
log "step 3: rotating into ${SECRET_PATH}#token"
printf '%s' "${NEW_TOKEN}" | ${DOCKER} exec -i \
    -e VAULT_TOKEN="${VAULT_TOKEN}" \
    vault-server \
    sh -c "vault kv patch ${SECRET_PATH} token=- >/dev/null"

# ── Step 4: verify the freshly-rotated token ──────────────────────────
log "step 4: verifying token against ${VERIFY_URL}"
if verify_token "${NEW_TOKEN}"; then
    log "  ✅ /api/v3/users/me returned 200 — token live"
else
    log "  ❌ verification failed; token in Vault but not authenticating"
    log "     (check openproject container logs; token sha256[12]=${NEW_HASH})"
    unset NEW_TOKEN
    exit 8
fi

unset NEW_TOKEN
log "T1.7 complete — secret/openproject/api#token populated and verified"
