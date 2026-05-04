#!/usr/bin/env bash
# HISTORICAL REFERENCE — bootstrap-era script from D-17-04
# WP-17-04-01.
# OpenProject is already deployed; canonical ongoing operations are:
#   - scripts/openproject-mint-admin-token.sh
#   - scripts/openproject-mint-iap-sync-token.sh
#   - scripts/openproject-bootstrap-ext-id-field.sh
#   - scripts/openproject-bootstrap-enrichment-fields.sh
#   - scripts/openproject-sync-from-framework.py
#   - scripts/openproject-enrich-from-framework.py
# Keep for forensic/rebuild reference only. Do not treat as the
# default operational path for new work.
#
# D-17-04 WP-17-04-01 — provision Vault policy, AppRole, and credentials for
# OpenProject (the canonical PM substrate replacing Plane CE).
#
# Idempotent: safe to re-run. Will not regenerate existing secret values
# unless OPENPROJECT_ROTATE_<KEY>=1 is set.
#
# Run on Mac Mini. Doctrine: hash-only verification, no value display.
# Credentials never appear on stdout, in argv, or in shell variables that
# could be logged.

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
# Resolve admin Vault token via shared helper (handles post-rebuild key
# files, ~/.vault-token migration, and env override). Replaces the
# previous direct read of ~/.vault-token which broke after the
# 2026-04-30 KV rebuild left that file stale.
source "$(dirname "$0")/lib/vault-admin-token.sh"
VAULT_TOKEN=$(resolve_admin_vault_token) || exit 2
SERVICE=openproject
APPROLE_DIR="/Users/admin/.vault-approle/${SERVICE}"
SECRETS_BASE="/Users/admin/.vault-agent-secrets"
POLICY_FILE="config/vault-policies/${SERVICE}-policy.hcl"

SECRETS_DIRS=(
  "${SECRETS_BASE}/openproject"
)

log() { printf '[provision-openproject] %s\n' "$*"; }

if [ ! -r "${POLICY_FILE}" ]; then
  log "ERROR: policy file ${POLICY_FILE} not found (run from repo root)"
  exit 1
fi

gen_secret() { /usr/bin/openssl rand -hex "${1:-32}"; }

vault_kv_put_stdin() {
  local path="$1" key="$2"
  ${DOCKER} exec -i -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    sh -c "vault kv put ${path} ${key}=- >/dev/null"
}

vault_kv_patch_stdin() {
  local path="$1" key="$2"
  ${DOCKER} exec -i -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    sh -c "vault kv patch ${path} ${key}=- >/dev/null"
}

sha256_prefix() { /usr/bin/shasum -a 256 | /usr/bin/awk '{print substr($1,1,12)}'; }

provision_literal_secret() {
  local path="$1" key="$2" val="$3" mode="${4:-patch}"
  local existing
  existing=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault kv get -field="${key}" "${path}" 2>/dev/null || true)
  if [ "${existing}" = "${val}" ]; then
    local hash; hash=$(printf '%s' "${val}" | sha256_prefix)
    log "  ${path}#${key}: present and matches; sha256[12]: ${hash}"
    return 0
  fi
  if [ "${mode}" = "put" ]; then
    printf '%s' "${val}" | vault_kv_put_stdin "${path}" "${key}"
  else
    printf '%s' "${val}" | vault_kv_patch_stdin "${path}" "${key}"
  fi
  local hash; hash=$(printf '%s' "${val}" | sha256_prefix)
  log "  ${path}#${key}: written (${mode}); sha256[12]: ${hash}"
}

provision_random_secret() {
  local path="$1" key="$2" bytes="$3" rotate_var="$4"
  local rotate_val; rotate_val="${!rotate_var:-0}"
  local existing
  existing=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault kv get -field="${key}" "${path}" 2>/dev/null || true)
  case "${existing}" in PLACEHOLDER_*) existing="" ;; esac
  if [ -n "${existing}" ] && [ "${rotate_val}" != "1" ]; then
    log "  ${path}#${key}: present, keeping (rotate with ${rotate_var}=1)"
    local hash; hash=$(printf '%s' "${existing}" | sha256_prefix)
    log "  ${path}#${key} sha256[12]: ${hash}"
    unset existing
    return 0
  fi
  local val; val=$(gen_secret "${bytes}")
  printf '%s' "${val}" | vault_kv_put_stdin "${path}" "${key}"
  local hash; hash=$(printf '%s' "${val}" | sha256_prefix)
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

# Postgres password
provision_random_secret "secret/openproject/db" "password" 32 "OPENPROJECT_ROTATE_DB_PASSWORD"
provision_literal_secret "secret/openproject/db" "username" "openproject" "patch"

# Rails SECRET_KEY_BASE (Rails requires 64+ hex chars)
provision_random_secret "secret/openproject/secret_key" "value" 64 "OPENPROJECT_ROTATE_SECRET_KEY"

# ── Step 6: OpenProject admin user (password + email) ─────────────────
# OpenProject seeds admin user on first boot from
# OPENPROJECT_SEED_ADMIN_USER_PASSWORD env var.
log "step 6: OpenProject admin (password + email)"

provision_random_secret "secret/openproject/admin" "password" 24 "OPENPROJECT_ROTATE_ADMIN_PASSWORD"
provision_literal_secret "secret/openproject/admin" "email" "admin@openproject.internal" "patch"

# ── Step 7: API token placeholder ─────────────────────────────────────
# OpenProject generates the API token after the admin user logs in
# (My Account → Access tokens → Generate). WP-17-04-01 leaves this empty;
# step 1.5 of WP-17-04-01 populates it after first boot. The
# credentials.env.tmpl guards on `if .Data.data.token` so empty
# renders nothing — safe.
log "step 7: API token placeholder (populated post-deploy)"
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault kv get -field=token secret/openproject/api >/dev/null 2>&1 \
  || printf '' | vault_kv_put_stdin "secret/openproject/api" "token"
log "  secret/openproject/api#token: empty placeholder (will populate post-deploy)"

# ── Step 8: verify policy isolation ───────────────────────────────────
log "step 8: verifying isolation (read in-policy + denied out-of-policy)"
ROLE_ID=$(/bin/cat "${APPROLE_DIR}/role-id")
SECRET_ID=$(/bin/cat "${APPROLE_DIR}/secret-id")

OP_TOKEN=$(${DOCKER} exec vault-server vault write -field=token \
  auth/approle/login role_id="${ROLE_ID}" secret_id="${SECRET_ID}")

if [ -z "${OP_TOKEN}" ]; then
  log "  ❌ AppRole login failed"
  exit 6
fi

if ${DOCKER} exec -e VAULT_TOKEN="${OP_TOKEN}" vault-server \
     vault kv get -field=password secret/openproject/db >/dev/null 2>&1; then
  log "  ✅ in-policy read (openproject/db) succeeded"
else
  log "  ❌ in-policy read failed — policy attached incorrectly"
  exit 7
fi

if ${DOCKER} exec -e VAULT_TOKEN="${OP_TOKEN}" vault-server \
     vault kv get secret/plane/db >/dev/null 2>&1; then
  log "  ❌ out-of-policy read (plane/db) SUCCEEDED — policy too permissive"
  exit 8
else
  log "  ✅ out-of-policy read (plane/db) denied"
fi

if ${DOCKER} exec -e VAULT_TOKEN="${OP_TOKEN}" vault-server \
     vault policy write openproject-test /tmp/${SERVICE}-policy.hcl >/dev/null 2>&1; then
  log "  ❌ policy write SUCCEEDED — explicit-deny block missing"
  exit 9
else
  log "  ✅ policy write denied"
fi

${DOCKER} exec -e VAULT_TOKEN="${OP_TOKEN}" vault-server \
  vault token revoke -self >/dev/null 2>&1 || true

log "D-17-04 WP-17-04-01 OpenProject provisioning complete"
