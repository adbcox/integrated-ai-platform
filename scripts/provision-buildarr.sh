#!/usr/bin/env bash
# D-17-44 — provision Vault policy and AppRole for Buildarr config-as-code substrate.
#
# Idempotent: safe to re-run. No secrets generated here — Buildarr reads
# existing secret/arr/{radarr,prowlarr,sonarr,sportarr} paths provisioned by D-17-38.
#
# Doctrine: hash-only verification, no value display. D-17-38 credential pattern.
# Run from repo root on Mac Mini.

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
source "$(dirname "$0")/lib/vault-admin-token.sh"
VAULT_TOKEN=$(resolve_admin_vault_token) || exit 2
SERVICE=buildarr
APPROLE_DIR="/Users/admin/.vault-approle/${SERVICE}"
SECRETS_DIR="/Users/admin/.vault-agent-secrets/${SERVICE}"
POLICY_FILE="config/vault-policies/${SERVICE}-policy.hcl"

log() { printf '[provision-buildarr] %s\n' "$*"; }

if [ ! -r "${POLICY_FILE}" ]; then
  log "ERROR: policy file ${POLICY_FILE} not found (run from repo root)"
  exit 1
fi

# ── Step 1: write policy ──────────────────────────────────────────────
log "step 1: writing Vault policy ${SERVICE}"
${DOCKER} cp "${POLICY_FILE}" vault-server:/tmp/${SERVICE}-policy.hcl
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault policy write ${SERVICE} /tmp/${SERVICE}-policy.hcl

# ── Step 2: create AppRole ────────────────────────────────────────────
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

# ── Step 4: secrets directory ─────────────────────────────────────────
log "step 4: ensuring secrets directory exists"
mkdir -p "${SECRETS_DIR}"
chmod 0700 "${SECRETS_DIR}"
log "  ${SECRETS_DIR}: ready"

# ── Step 5: verify AppRole can read arr secrets (hash-only) ──────────
log "step 5: smoke-testing AppRole read access"
ROLE_ID=$(cat "${APPROLE_DIR}/role-id")
SECRET_ID=$(cat "${APPROLE_DIR}/secret-id")
TEST_TOKEN=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault write -format=json auth/approle/login \
    role_id="${ROLE_ID}" secret_id="${SECRET_ID}" 2>/dev/null \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['auth']['client_token'])")
unset ROLE_ID SECRET_ID

for path in secret/arr/radarr secret/arr/prowlarr secret/arr/sonarr secret/arr/sportarr; do
  RESULT=$(${DOCKER} exec -e VAULT_TOKEN="${TEST_TOKEN}" vault-server \
    vault kv get -format=json "${path}" 2>&1)
  if echo "$RESULT" | grep -q '"api_key"'; then
    HASH=$(echo "$RESULT" | python3 -c "
import sys, json, hashlib
d=json.load(sys.stdin)
v=d['data']['data']['api_key']
print(hashlib.md5(v.encode()).hexdigest()[:12])
")
    log "  ${path}#api_key: readable; md5[12]: ${HASH}"
  else
    log "  ERROR: ${path} not readable or missing api_key"
    exit 1
  fi
done
unset TEST_TOKEN

log "provision-buildarr complete"
