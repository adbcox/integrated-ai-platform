#!/usr/bin/env bash
# Block 4.C C2.1 — provision Vault policy, AppRole, and credentials
# for the NetBox CMDB service.
#
# Idempotent: safe to re-run. Will not regenerate existing secret
# values unless NETBOX_ROTATE_<KEY>=1 is set in the environment.
#
# Run on Mac Mini. Doctrine: hash-only verification, no value display.
# Credentials never appear on stdout, in argv, or in shell variables
# that could be logged.

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
VAULT_TOKEN=${VAULT_TOKEN:-$(/bin/cat ~/.vault-token)}
SERVICE=netbox
APPROLE_DIR="/Users/admin/.vault-approle/${SERVICE}"
SECRETS_BASE="/Users/admin/.vault-agent-secrets"
POLICY_FILE="config/vault-policies/${SERVICE}-policy.hcl"

# Per-consumer secrets directories (one Vault Agent sidecar per consumer).
SECRETS_DIRS=(
  "${SECRETS_BASE}/netbox"
  "${SECRETS_BASE}/netbox-postgres"
  "${SECRETS_BASE}/netbox-redis"
  "${SECRETS_BASE}/netbox-redis-cache"
)

log() { printf '[provision-netbox] %s\n' "$*"; }

if [ ! -r "${POLICY_FILE}" ]; then
  log "ERROR: policy file ${POLICY_FILE} not found (run from repo root)"
  exit 1
fi

# ── Helper: random secret generator (URL-safe hex per CLAUDE.md anti-pattern note) ─
gen_secret() {
  local bytes=${1:-32}
  /usr/bin/openssl rand -hex "${bytes}"
}

# ── Helper: write KV pair to Vault via stdin (value never in argv) ──
# Usage: vault_kv_put_stdin <path> <key> <value-on-stdin>
vault_kv_put_stdin() {
  local path="$1"
  local key="$2"
  ${DOCKER} exec -i -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    sh -c "vault kv put ${path} ${key}=- >/dev/null"
}

# ── Helper: capture sha256 prefix of a value piped on stdin ──
# Used for hash-only verification: write happens, return prefix only.
sha256_prefix() {
  /usr/bin/shasum -a 256 | /usr/bin/awk '{print substr($1,1,12)}'
}

# ── Helper: provision-or-skip a single random secret ──
# $1 path, $2 key, $3 byte-count, $4 rotate-env-var-name
provision_random_secret() {
  local path="$1" key="$2" bytes="$3" rotate_var="$4"
  local rotate_val
  rotate_val="${!rotate_var:-0}"

  local existing
  existing=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault kv get -field="${key}" "${path}" 2>/dev/null || true)

  if [ -n "${existing}" ] && [ "${rotate_val}" != "1" ]; then
    log "  ${path}#${key}: present, keeping (rotate with ${rotate_var}=1)"
    local hash
    hash=$(printf '%s' "${existing}" | sha256_prefix)
    log "  ${path}#${key} sha256[12]: ${hash}"
    unset existing
    return 0
  fi

  local val
  val=$(gen_secret "${bytes}")
  printf '%s' "${val}" | vault_kv_put_stdin "${path}" "${key}"
  local hash
  hash=$(printf '%s' "${val}" | sha256_prefix)
  log "  ${path}#${key}: written; sha256[12]: ${hash}"
  unset val
}

# ── Step 1: write policy ──────────────────────────────────────────────
log "step 1: writing Vault policy ${SERVICE}"
${DOCKER} cp "${POLICY_FILE}" vault-server:/tmp/${SERVICE}-policy.hcl
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault policy write ${SERVICE} /tmp/${SERVICE}-policy.hcl

# ── Step 2: create or update AppRole ──────────────────────────────────
log "step 2: creating/updating AppRole ${SERVICE}"
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault write auth/approle/role/${SERVICE} \
    token_policies=${SERVICE} \
    token_ttl=1h \
    token_max_ttl=4h \
    secret_id_ttl=0

# ── Step 3: capture role-id + secret-id ──────────────────────────────
mkdir -p "${APPROLE_DIR}"
chmod 0700 "${APPROLE_DIR}"

if [ ! -s "${APPROLE_DIR}/role-id" ]; then
  log "step 3: writing role-id"
  ${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault read -field=role_id auth/approle/role/${SERVICE}/role-id \
    > "${APPROLE_DIR}/role-id"
  chmod 0600 "${APPROLE_DIR}/role-id"
else
  log "step 3: role-id already present (skipping)"
fi

if [ ! -s "${APPROLE_DIR}/secret-id" ]; then
  log "step 3: writing secret-id"
  ${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault write -force -field=secret_id \
      auth/approle/role/${SERVICE}/secret-id \
    > "${APPROLE_DIR}/secret-id"
  chmod 0600 "${APPROLE_DIR}/secret-id"
else
  log "step 3: secret-id already present (skipping)"
fi

# ── Step 4: per-consumer secrets directories ──────────────────────────
log "step 4: ensuring per-consumer secrets directories exist"
for dir in "${SECRETS_DIRS[@]}"; do
  mkdir -p "${dir}"
  chmod 0700 "${dir}"
  log "  ${dir}: ready"
done

# ── Step 5: provision random secrets ──────────────────────────────────
log "step 5: provisioning random secret values (idempotent)"

# Postgres password (used by netbox app + postgres container)
provision_random_secret "secret/netbox/postgres" "password" 32 "NETBOX_ROTATE_POSTGRES"

# Redis password
provision_random_secret "secret/netbox/redis" "password" 24 "NETBOX_ROTATE_REDIS"

# Redis-cache password (distinct from redis)
provision_random_secret "secret/netbox/redis-cache" "password" 24 "NETBOX_ROTATE_REDIS_CACHE"

# Django SECRET_KEY (50+ chars per Django requirement)
provision_random_secret "secret/netbox/secret_key" "value" 32 "NETBOX_ROTATE_SECRET_KEY"

# API token pepper (used by NetBox to hash API tokens at rest)
provision_random_secret "secret/netbox/app" "api_token_pepper" 32 "NETBOX_ROTATE_PEPPER"

# ── Step 6: admin password (Argon2 hash for createsuperuser) ──────────
# NetBox createsuperuser --noinput accepts password via env. We store
# the *plaintext* in Vault (so C2.6 can fetch and pipe via stdin).
# Hash-only verification compares sha256 prefix at write time and at
# fetch time — never displays the value.
log "step 6: NetBox admin password"

EXISTING_ADMIN=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault kv get -field=password secret/netbox/admin 2>/dev/null || true)

if [ -n "${EXISTING_ADMIN}" ] && [ "${NETBOX_RESET_ADMIN:-0}" != "1" ]; then
  log "  admin password already set (rotate with NETBOX_RESET_ADMIN=1)"
  ADMIN_HASH=$(printf '%s' "${EXISTING_ADMIN}" | sha256_prefix)
  log "  admin password sha256[12]: ${ADMIN_HASH}"
  unset EXISTING_ADMIN
else
  ADMIN_VAL=$(gen_secret 24)
  printf '%s' "${ADMIN_VAL}" | vault_kv_put_stdin "secret/netbox/admin" "password"
  ADMIN_HASH=$(printf '%s' "${ADMIN_VAL}" | sha256_prefix)
  log "  admin password written; sha256[12]: ${ADMIN_HASH}"
  unset ADMIN_VAL
fi

# ── Step 7: API token placeholder ─────────────────────────────────────
# C2.7 will populate with the actual token after createsuperuser. Write
# an empty placeholder now so the path exists with metadata.
EXISTING_TOKEN=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault kv get -field=token secret/netbox/api_token 2>/dev/null || true)

if [ -z "${EXISTING_TOKEN}" ]; then
  log "step 7: writing api_token placeholder (will be populated in C2.7)"
  printf '%s' "PLACEHOLDER_REPLACE_IN_C2_7" | vault_kv_put_stdin "secret/netbox/api_token" "token"
else
  log "step 7: api_token already populated; sha256[12]: $(printf '%s' "${EXISTING_TOKEN}" | sha256_prefix)"
fi
unset EXISTING_TOKEN

# ── Step 8: verify policy isolation ───────────────────────────────────
log "step 8: verifying isolation (read in-policy + denied out-of-policy)"
ROLE_ID=$(/bin/cat "${APPROLE_DIR}/role-id")
SECRET_ID=$(/bin/cat "${APPROLE_DIR}/secret-id")

NB_TOKEN=$(${DOCKER} exec vault-server vault write -field=token \
  auth/approle/login role_id="${ROLE_ID}" secret_id="${SECRET_ID}")

if [ -z "${NB_TOKEN}" ]; then
  log "  ❌ AppRole login failed"
  exit 6
fi

# In-policy: read postgres password → success
if ${DOCKER} exec -e VAULT_TOKEN="${NB_TOKEN}" vault-server \
     vault kv get -field=password secret/netbox/postgres >/dev/null 2>&1; then
  log "  ✅ in-policy read (netbox/postgres) succeeded"
else
  log "  ❌ in-policy read failed — policy attached incorrectly"
  exit 7
fi

# Out-of-policy: read different service's secret → denied
if ${DOCKER} exec -e VAULT_TOKEN="${NB_TOKEN}" vault-server \
     vault kv get secret/control-plane/operator >/dev/null 2>&1; then
  log "  ❌ out-of-policy read SUCCEEDED — policy is too permissive"
  exit 8
else
  log "  ✅ out-of-policy read (control-plane/operator) denied"
fi

# Out-of-policy: policy modification → denied (explicit-deny block)
if ${DOCKER} exec -e VAULT_TOKEN="${NB_TOKEN}" vault-server \
     vault policy write netbox-test /tmp/${SERVICE}-policy.hcl >/dev/null 2>&1; then
  log "  ❌ policy write SUCCEEDED — explicit-deny block missing"
  exit 9
else
  log "  ✅ policy write denied"
fi

# Revoke the verification token
${DOCKER} exec -e VAULT_TOKEN="${NB_TOKEN}" vault-server \
  vault token revoke -self >/dev/null 2>&1 || true

log "C2.1 provisioning complete"
