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
# WARNING: `vault kv put` REPLACES the version with only this field.
# Use vault_kv_patch_stdin to add/update a single field on a path
# that already has other fields (e.g. secret/netbox/admin once it
# carries password + username + email).
vault_kv_put_stdin() {
  local path="$1"
  local key="$2"
  ${DOCKER} exec -i -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    sh -c "vault kv put ${path} ${key}=- >/dev/null"
}

# ── Helper: patch a single field on an existing KV path via stdin ──
# Usage: vault_kv_patch_stdin <path> <key> <value-on-stdin>
# Uses `vault kv patch` (KVv2) which preserves other fields on the path.
vault_kv_patch_stdin() {
  local path="$1"
  local key="$2"
  ${DOCKER} exec -i -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    sh -c "vault kv patch ${path} ${key}=- >/dev/null"
}

# ── Helper: provision-or-skip a literal secret (value not random) ──
# $1 path, $2 key, $3 literal-value, $4 mode = "put" or "patch"
# "put" creates the path with this single field (replacing any prior).
# "patch" adds/updates the field on an existing path without disturbing
# its other fields. Use "patch" for fields added to an existing path.
# Idempotent: if the field is already present with the same value,
# no write happens; the sha256 prefix is logged for verification.
provision_literal_secret() {
  local path="$1" key="$2" val="$3" mode="${4:-patch}"
  local existing
  existing=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault kv get -field="${key}" "${path}" 2>/dev/null || true)

  if [ "${existing}" = "${val}" ]; then
    local hash
    hash=$(printf '%s' "${val}" | sha256_prefix)
    log "  ${path}#${key}: present and matches; sha256[12]: ${hash}"
    return 0
  fi

  if [ "${mode}" = "put" ]; then
    printf '%s' "${val}" | vault_kv_put_stdin "${path}" "${key}"
  else
    printf '%s' "${val}" | vault_kv_patch_stdin "${path}" "${key}"
  fi
  local hash
  hash=$(printf '%s' "${val}" | sha256_prefix)
  log "  ${path}#${key}: written (${mode}); sha256[12]: ${hash}"
}

# ── Helper: capture sha256 prefix of a value piped on stdin ──
# Used for hash-only verification: write happens, return prefix only.
sha256_prefix() {
  /usr/bin/shasum -a 256 | /usr/bin/awk '{print substr($1,1,12)}'
}

# ── Helper: provision-or-skip a single random secret ──
# $1 path, $2 key, $3 byte-count, $4 rotate-env-var-name
# Treats values starting with "PLACEHOLDER_" as absent so legacy
# placeholder content is overwritten on re-run (migration path from
# the original C2.7-deferred posture to the upstream-entrypoint flow).
provision_random_secret() {
  local path="$1" key="$2" bytes="$3" rotate_var="$4"
  local rotate_val
  rotate_val="${!rotate_var:-0}"

  local existing
  existing=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault kv get -field="${key}" "${path}" 2>/dev/null || true)

  case "${existing}" in
    PLACEHOLDER_*) existing="" ;;
  esac

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

# ── Step 6: NetBox admin user (password + username + email) ───────────
# Per C2 discovery #5: netbox-docker's docker-entrypoint.sh runs
# super_user.py automatically when SKIP_SUPERUSER is unset/false.
# super_user.py reads SUPERUSER_NAME, SUPERUSER_EMAIL,
# SUPERUSER_PASSWORD, SUPERUSER_API_TOKEN from env (which we render
# from these Vault keys). All three live on secret/netbox/admin so
# they rotate as a unit; api_token lives separately to keep
# rotation independent.
log "step 6: NetBox admin (password + username + email)"

# Password — random, idempotent. Use "put" the FIRST time (creates
# the path); subsequent runs find it present and the helper no-ops.
# This preserves the existing field-shape behaviour.
provision_random_secret "secret/netbox/admin" "password" 24 "NETBOX_ROTATE_ADMIN_PASSWORD"

# Username and email — literals, patched onto the same path.
# super_user.py defaults: SUPERUSER_NAME=admin, SUPERUSER_EMAIL=admin@example.com.
# Platform convention: <service>.internal addresses; using
# admin@netbox.internal so emailed reports/notifications resolve
# in-domain rather than collide with external example.com.
provision_literal_secret "secret/netbox/admin" "username" "admin" "patch"
provision_literal_secret "secret/netbox/admin" "email" "admin@netbox.internal" "patch"

# ── Step 7: API token (40-char hex, populated upfront) ────────────────
# Per C2 discovery #5: super_user.py creates the Token alongside the
# user using SUPERUSER_API_TOKEN as the literal token value. The token
# value goes into Vault FIRST so credentials.env renders it for the
# entrypoint. After redeploy, C2.7 verification fetches it back from
# Vault and confirms a 200 against /api/status/.
provision_random_secret "secret/netbox/api_token" "token" 20 "NETBOX_ROTATE_API_TOKEN"
# 20 bytes -> 40-char hex, matching super_user.py's default token width.

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
