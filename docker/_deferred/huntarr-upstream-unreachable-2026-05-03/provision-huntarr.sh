#!/usr/bin/env bash
# D-17-49 — provision Vault policy/AppRole for Huntarr.
# Hash-only verification: sha256[:12], never print raw credential values.

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
source "$(dirname "$0")/lib/vault-admin-token.sh"
VAULT_TOKEN=$(resolve_admin_vault_token) || exit 2
SERVICE=huntarr
APPROLE_DIR="/Users/admin/.vault-approle/${SERVICE}"
SECRETS_DIR="/Users/admin/.vault-agent-secrets/${SERVICE}"
POLICY_FILE="config/vault-policies/${SERVICE}-policy.hcl"

log() { printf '[provision-huntarr] %s\n' "$*"; }

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

for p in secret/arr/sonarr secret/arr/radarr; do
  v=$(${DOCKER} exec -e VAULT_TOKEN="${TEST_TOKEN}" vault-server vault kv get -field=api_key "${p}")
  h=$(python3 -c "import hashlib,sys; print(hashlib.sha256(sys.argv[1].encode()).hexdigest()[:12])" "$v")
  log "  ${p} readable sha256[:12]=${h}"
done

unset ROLE_ID SECRET_ID TEST_TOKEN
log "provision-huntarr complete"
