#!/usr/bin/env bash
# D-17-46 — provision scraparr Vault policy/AppRole + sync arr API keys from live services.
# Hash-only verification: sha256[:12], never print raw credential values.

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
source "$(dirname "$0")/lib/vault-admin-token.sh"
VAULT_TOKEN=$(resolve_admin_vault_token) || exit 2
SERVICE=scraparr
APPROLE_DIR="/Users/admin/.vault-approle/${SERVICE}"
SECRETS_DIR="/Users/admin/.vault-agent-secrets/${SERVICE}"
POLICY_FILE="config/vault-policies/${SERVICE}-policy.hcl"

log() { printf '[provision-scraparr] %s\n' "$*"; }

if [ ! -r "$POLICY_FILE" ]; then
  log "ERROR: policy file not found: $POLICY_FILE"
  exit 1
fi

harvest_api_key() {
  local svc="$1"
  ${DOCKER} exec "$svc" sh -lc "sed -n 's:.*<ApiKey>\\(.*\\)</ApiKey>.*:\\1:p' /config/config.xml | head -n1"
}

sha12() {
  python3 - <<'PY' "$1"
import hashlib,sys
print(hashlib.sha256(sys.argv[1].encode()).hexdigest()[:12])
PY
}

vault_get_api_key() {
  local path="$1"
  ${DOCKER} exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
    vault kv get -field=api_key "$path" 2>/dev/null || true
}

vault_put_api_key() {
  local path="$1" value="$2"
  ${DOCKER} exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
    vault kv patch "$path" api_key="$value" >/dev/null
}

sync_secret() {
  local svc="$1" path="$2"
  local live vault live_h vault_h
  live=$(harvest_api_key "$svc")
  live_h=$(sha12 "$live")
  vault=$(vault_get_api_key "$path")
  if [ -n "$vault" ]; then
    vault_h=$(sha12 "$vault")
  else
    vault_h="<missing>"
  fi

  if [ "$live_h" != "$vault_h" ]; then
    vault_put_api_key "$path" "$live"
    log "synced $path from running $svc (live=$live_h, old=$vault_h)"
  else
    log "$path already matches running $svc (sha256[:12]=$live_h)"
  fi
}

log "step 1: sync Vault arr keys from live services"
sync_secret sonarr secret/arr/sonarr
sync_secret radarr secret/arr/radarr
sync_secret prowlarr secret/arr/prowlarr

log "step 2: write Vault policy ${SERVICE}"
${DOCKER} cp "$POLICY_FILE" vault-server:/tmp/${SERVICE}-policy.hcl
${DOCKER} exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault policy write ${SERVICE} /tmp/${SERVICE}-policy.hcl >/dev/null

log "step 3: create/update AppRole ${SERVICE}"
${DOCKER} exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault write auth/approle/role/${SERVICE} \
    token_policies=${SERVICE} token_ttl=1h token_max_ttl=4h secret_id_ttl=0 >/dev/null

mkdir -p "$APPROLE_DIR" "$SECRETS_DIR"
chmod 0700 "$APPROLE_DIR" "$SECRETS_DIR"

if [ ! -s "$APPROLE_DIR/role-id" ]; then
  ${DOCKER} exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
    vault read -field=role_id auth/approle/role/${SERVICE}/role-id > "$APPROLE_DIR/role-id"
  chmod 0600 "$APPROLE_DIR/role-id"
fi

if [ ! -s "$APPROLE_DIR/secret-id" ]; then
  ${DOCKER} exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
    vault write -force -field=secret_id auth/approle/role/${SERVICE}/secret-id > "$APPROLE_DIR/secret-id"
  chmod 0600 "$APPROLE_DIR/secret-id"
fi

log "step 4: AppRole smoke test (hash-only)"
ROLE_ID=$(cat "$APPROLE_DIR/role-id")
SECRET_ID=$(cat "$APPROLE_DIR/secret-id")
TEST_TOKEN=$(${DOCKER} exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault write -format=json auth/approle/login role_id="$ROLE_ID" secret_id="$SECRET_ID" 2>/dev/null \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['auth']['client_token'])")

for p in secret/arr/sonarr secret/arr/radarr secret/arr/prowlarr; do
  v=$(${DOCKER} exec -e VAULT_TOKEN="$TEST_TOKEN" vault-server vault kv get -field=api_key "$p")
  log "  $p readable sha256[:12]=$(sha12 "$v")"
done

unset ROLE_ID SECRET_ID TEST_TOKEN
log "provision-scraparr complete"
