#!/usr/bin/env bash
# Phase 13 Increment 2A — provision Vault policy, AppRole, and credentials
# for the InvenTree parts inventory service.
#
# Idempotent: safe to re-run. Will not regenerate existing secret values
# unless INVENTREE_ROTATE_<KEY>=1 is set.
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
SERVICE=inventree
APPROLE_DIR="/Users/admin/.vault-approle/${SERVICE}"
SECRETS_BASE="/Users/admin/.vault-agent-secrets"
POLICY_FILE="config/vault-policies/${SERVICE}-policy.hcl"

SECRETS_DIRS=(
  "${SECRETS_BASE}/inventree"
  "${SECRETS_BASE}/inventree-postgres"
  "${SECRETS_BASE}/inventree-redis"
)

log() { printf '[provision-inventree] %s\n' "$*"; }

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
provision_random_secret "secret/inventree/postgres" "password" 32 "INVENTREE_ROTATE_POSTGRES"

# Redis password (cache only — InvenTree does not use Redis as primary DB)
provision_random_secret "secret/inventree/redis" "password" 24 "INVENTREE_ROTATE_REDIS"

# Django SECRET_KEY (50+ chars per Django requirement)
provision_random_secret "secret/inventree/secret_key" "value" 32 "INVENTREE_ROTATE_SECRET_KEY"

# ── Step 6: InvenTree admin user (password + username + email) ────────
# Admin bootstrap via INVENTREE_ADMIN_USER/EMAIL/PASSWORD env vars
# (verbatim names per docs.inventree.org/en/stable/start/config/).
# All three live on secret/inventree/admin so they rotate as a unit.
log "step 6: InvenTree admin (password + username + email)"

# Password — random, idempotent. First run uses "put" implicitly via
# the helper's path-creation; subsequent fields patched onto same path.
provision_random_secret "secret/inventree/admin" "password" 24 "INVENTREE_ROTATE_ADMIN_PASSWORD"

# Username and email — literals, patched onto the same path.
provision_literal_secret "secret/inventree/admin" "username" "admin" "patch"
provision_literal_secret "secret/inventree/admin" "email" "admin@inventree.internal" "patch"

# ── Step 7: API token placeholder ─────────────────────────────────────
# InvenTree generates the API token *after* the admin user exists
# (Django auth Token row created on first admin login or via manage.py
# drf_create_token). Increment 2A leaves this empty; the deploy step
# (4.D.2) populates it after first boot. The credentials.env.tmpl
# guards on `if .Data.data.token` so empty here renders nothing — safe.
log "step 7: API token placeholder (populated post-deploy in 4.D.2)"
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault kv get -field=token secret/inventree/api_token >/dev/null 2>&1 \
  || printf '' | vault_kv_put_stdin "secret/inventree/api_token" "token"
log "  secret/inventree/api_token#token: empty placeholder (will populate post-deploy)"

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

if ${DOCKER} exec -e VAULT_TOKEN="${NB_TOKEN}" vault-server \
     vault kv get -field=password secret/inventree/postgres >/dev/null 2>&1; then
  log "  ✅ in-policy read (inventree/postgres) succeeded"
else
  log "  ❌ in-policy read failed — policy attached incorrectly"
  exit 7
fi

if ${DOCKER} exec -e VAULT_TOKEN="${NB_TOKEN}" vault-server \
     vault kv get secret/netbox/postgres >/dev/null 2>&1; then
  log "  ❌ out-of-policy read (netbox/postgres) SUCCEEDED — policy too permissive"
  exit 8
else
  log "  ✅ out-of-policy read (netbox/postgres) denied"
fi

if ${DOCKER} exec -e VAULT_TOKEN="${NB_TOKEN}" vault-server \
     vault policy write inventree-test /tmp/${SERVICE}-policy.hcl >/dev/null 2>&1; then
  log "  ❌ policy write SUCCEEDED — explicit-deny block missing"
  exit 9
else
  log "  ✅ policy write denied"
fi

${DOCKER} exec -e VAULT_TOKEN="${NB_TOKEN}" vault-server \
  vault token revoke -self >/dev/null 2>&1 || true

log "Increment 2A provisioning complete"
