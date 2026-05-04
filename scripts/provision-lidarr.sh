#!/usr/bin/env bash
# D-17-87 — provision Vault policy/AppRole for Lidarr integration substrate.
# Hash-only verification: sha256[:12], never print raw credential values.

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
source "$(dirname "$0")/lib/vault-admin-token.sh"
VAULT_TOKEN=$(resolve_admin_vault_token) || exit 2
SERVICE=lidarr
APPROLE_DIR="/Users/admin/.vault-approle/${SERVICE}"
SECRETS_DIR="/Users/admin/.vault-agent-secrets/${SERVICE}"
POLICY_FILE="config/vault-policies/${SERVICE}-policy.hcl"

log() { printf '[provision-lidarr] %s\n' "$*"; }

sha12() {
  python3 - <<'PY' "$1"
import hashlib,sys
print(hashlib.sha256(sys.argv[1].encode()).hexdigest()[:12])
PY
}

if [ ! -r "${POLICY_FILE}" ]; then
  log "ERROR: policy file ${POLICY_FILE} not found (run from repo root)"
  exit 1
fi

log "step 1: writing Vault policy ${SERVICE}"
${DOCKER} cp "${POLICY_FILE}" vault-server:/tmp/${SERVICE}-policy.hcl
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault policy write ${SERVICE} /tmp/${SERVICE}-policy.hcl >/dev/null

log "step 2: creating/updating AppRole ${SERVICE}"
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault write auth/approle/role/${SERVICE} \
    token_policies=${SERVICE} token_ttl=1h token_max_ttl=4h secret_id_ttl=0 >/dev/null

mkdir -p "${APPROLE_DIR}" "${SECRETS_DIR}"
chmod 0700 "${APPROLE_DIR}" "${SECRETS_DIR}"

if [ ! -s "${APPROLE_DIR}/role-id" ]; then
  ${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault read -field=role_id auth/approle/role/${SERVICE}/role-id > "${APPROLE_DIR}/role-id"
  chmod 0600 "${APPROLE_DIR}/role-id"
fi

if [ ! -s "${APPROLE_DIR}/secret-id" ]; then
  ${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault write -force -field=secret_id auth/approle/role/${SERVICE}/secret-id > "${APPROLE_DIR}/secret-id"
  chmod 0600 "${APPROLE_DIR}/secret-id"
fi

log "step 3: AppRole read test (hash-only)"
ROLE_ID=$(cat "${APPROLE_DIR}/role-id")
SECRET_ID=$(cat "${APPROLE_DIR}/secret-id")
TEST_TOKEN=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault write -format=json auth/approle/login role_id="${ROLE_ID}" secret_id="${SECRET_ID}" 2>/dev/null \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['auth']['client_token'])")

PROWLARR_VAL=$(${DOCKER} exec -e VAULT_TOKEN="${TEST_TOKEN}" vault-server \
  vault kv get -field=api_key secret/arr/prowlarr)
log "  secret/arr/prowlarr readable sha256[:12]=$(sha12 "${PROWLARR_VAL}")"

LIDARR_VAL=$(${DOCKER} exec -e VAULT_TOKEN="${TEST_TOKEN}" vault-server \
  vault kv get -field=api_key secret/arr/lidarr 2>/dev/null || true)
if [ -n "${LIDARR_VAL}" ]; then
  log "  secret/arr/lidarr readable sha256[:12]=$(sha12 "${LIDARR_VAL}")"
else
  log "  secret/arr/lidarr not present yet (expected pre-first-boot)"
fi

unset ROLE_ID SECRET_ID TEST_TOKEN PROWLARR_VAL LIDARR_VAL
log "provision-lidarr complete"
