#!/bin/bash
# Refresh Strava OAuth token and update Vault.
# Cron: */30 * * * * ~/repos/integrated-ai-platform/scripts/refresh-strava-token.sh >> /var/log/strava-refresh.log 2>&1

set -euo pipefail

VAULT_PATH="secret/strava/oauth"
VAULT_CONTAINER="vault-server"
ROOT_TOKEN_FILE=~/vault-init-keys.txt

vault_get() {
  local path=$1 field=$2
  local token
  token=$(grep "Initial Root Token" "$ROOT_TOKEN_FILE" | awk '{print $NF}')
  docker exec -e VAULT_TOKEN="$token" "$VAULT_CONTAINER" vault kv get -field="$field" "$path" 2>/dev/null
}

vault_put() {
  local path=$1; shift
  local token
  token=$(grep "Initial Root Token" "$ROOT_TOKEN_FILE" | awk '{print $NF}')
  docker exec -e VAULT_TOKEN="$token" "$VAULT_CONTAINER" vault kv put "$path" "$@" 2>/dev/null
}

REFRESH_TOKEN=$(vault_get "$VAULT_PATH" refresh_token 2>/dev/null || true)
CLIENT_ID=$(vault_get "$VAULT_PATH" client_id 2>/dev/null || true)
CLIENT_SECRET=$(vault_get "$VAULT_PATH" client_secret 2>/dev/null || true)

if [ -z "${REFRESH_TOKEN:-}" ] || [ -z "${CLIENT_ID:-}" ]; then
  echo "$(date) ❌ Strava credentials not in Vault at $VAULT_PATH"
  echo "  Store with: vault kv put $VAULT_PATH client_id=XXX client_secret=XXX refresh_token=XXX"
  exit 1
fi

RESPONSE=$(curl -sf -X POST https://www.strava.com/oauth/token \
  -d client_id="$CLIENT_ID" \
  -d client_secret="$CLIENT_SECRET" \
  -d refresh_token="$REFRESH_TOKEN" \
  -d grant_type=refresh_token)

NEW_ACCESS_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['access_token'])")
NEW_REFRESH_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['refresh_token'])")
EXPIRES_AT=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['expires_at'])")

if [ -z "$NEW_ACCESS_TOKEN" ] || [ "$NEW_ACCESS_TOKEN" = "null" ]; then
  echo "$(date) ❌ Token refresh failed: $RESPONSE"
  exit 1
fi

vault_put "$VAULT_PATH" \
  client_id="$CLIENT_ID" \
  client_secret="$CLIENT_SECRET" \
  access_token="$NEW_ACCESS_TOKEN" \
  refresh_token="$NEW_REFRESH_TOKEN" \
  expires_at="$EXPIRES_AT"

echo "$(date) ✅ Strava token refreshed (expires: $(python3 -c "import datetime; print(datetime.datetime.fromtimestamp($EXPIRES_AT).isoformat())"))"
