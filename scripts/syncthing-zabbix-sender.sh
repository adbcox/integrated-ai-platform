#!/usr/bin/env bash
# D-17-105 — Push Syncthing QNAP metrics to Zabbix via zabbix_sender.
# Runs on the Mac Mini HOST (not in Docker) so it can reach QNAP :8384 directly.
# Invoked by launchd com.iap.syncthing-zabbix-sender (every 5 minutes).
#
# Why host-side: zabbix-server runs in Docker (zabbix-net/172.25.0.x); that subnet
# is rejected by QNAP QTS when connecting to Syncthing :8384. Mac Mini host
# (192.168.10.145) reaches QNAP fine. Trapper items receive the pushed values.

set -euo pipefail

ZABBIX_SERVER="127.0.0.1"
ZABBIX_PORT="10051"
ZABBIX_HOST="mac-mini"

SYNC_URL="http://192.168.10.201:8384"
VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"

log() { printf '[syncthing-zabbix-sender] %s\n' "$*"; }

# ── Resolve Vault token (prefer rendered secrets file, fall back to token file) ──
resolve_sync_key() {
  local creds_file="/Users/admin/.vault-agent-secrets/cleanuparr/credentials.env"
  # Syncthing QNAP key is not rendered by any current sidecar; use Vault directly
  local token_file="/Users/admin/vault-init-keys-NEW-20260430.txt"
  local vault_token
  vault_token="$(grep 'Root Token' "$token_file" 2>/dev/null | awk '{print $NF}')"
  if [ -z "$vault_token" ]; then
    vault_token="$(cat /Users/admin/.vault-token 2>/dev/null)"
  fi
  docker exec -e VAULT_TOKEN="$vault_token" vault-server \
    vault kv get -field=api_key secret/syncthing/qnap 2>/dev/null
}

SYNC_KEY="$(resolve_sync_key)"
if [ -z "$SYNC_KEY" ]; then
  log "ERROR: could not resolve Syncthing QNAP API key from Vault"
  exit 1
fi

# ── Collect staleness metric (max hours since last file sync across all folders) ──
STATS_JSON="$(curl -sf --connect-timeout 5 \
  -H "X-API-Key: $SYNC_KEY" \
  "${SYNC_URL}/rest/stats/folder" 2>/dev/null)"

if [ -z "$STATS_JSON" ]; then
  log "WARNING: stats/folder returned empty — skipping staleness push"
  MAX_STALE_H="-1"
else
  MAX_STALE_H="$(python3 -c "
import sys, json, datetime
d = json.loads('''$STATS_JSON''')
now = datetime.datetime.now(datetime.timezone.utc)
max_h = 0
for k, v in d.items():
    lf = (v or {}).get('lastFile', {})
    t = (lf or {}).get('at')
    if t:
        try:
            ts = datetime.datetime.fromisoformat(t.replace('Z','+00:00'))
            h = (now - ts).total_seconds() / 3600
            if h > max_h:
                max_h = h
        except Exception:
            pass
print(int(max_h))
" 2>/dev/null || echo "-1")"
fi

# ── Collect error count for sabnzbd-complete folder (is5fj-3grur) ──
STATUS_JSON="$(curl -sf --connect-timeout 5 \
  -H "X-API-Key: $SYNC_KEY" \
  "${SYNC_URL}/rest/db/status?folder=is5fj-3grur" 2>/dev/null)"

if [ -z "$STATUS_JSON" ]; then
  log "WARNING: db/status returned empty — skipping errors push"
  ERRORS_TOTAL="-1"
else
  ERRORS_TOTAL="$(python3 -c "
import sys, json
d = json.loads('''$STATUS_JSON''')
print(int(d.get('errors', 0)) + int(d.get('pullErrors', 0)))
" 2>/dev/null || echo "-1")"
fi

log "max_stale_h=$MAX_STALE_H errors_total=$ERRORS_TOTAL"

# ── Push via zabbix_sender ──
/usr/local/bin/zabbix_sender \
  -z "$ZABBIX_SERVER" \
  -p "$ZABBIX_PORT" \
  -s "$ZABBIX_HOST" \
  -k "d17105.syncthing.qnap.max_stale_h" \
  -o "$MAX_STALE_H" 2>/dev/null

/usr/local/bin/zabbix_sender \
  -z "$ZABBIX_SERVER" \
  -p "$ZABBIX_PORT" \
  -s "$ZABBIX_HOST" \
  -k "d17105.syncthing.qnap.errors_total" \
  -o "$ERRORS_TOTAL" 2>/dev/null

log "sent to Zabbix"
