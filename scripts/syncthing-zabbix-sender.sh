#!/usr/bin/env bash
# D-17-105 — Option B: SSH-side Syncthing probe + Zabbix trapper push.
#
# Runs on Mac Mini and executes QNAP loopback API probes over SSH:
#   curl http://127.0.0.1:8384/rest/...
# Then pushes metrics to Zabbix via zabbix_sender for host "mac-mini".

set -euo pipefail

ZABBIX_SERVER="127.0.0.1"
ZABBIX_PORT="10051"
ZABBIX_HOST="mac-mini"
KEY_CACHE="${HOME}/.cache/syncthing-qnap-apikey"

log() { printf '[syncthing-zabbix-sender] %s\n' "$*"; }

resolve_sync_key() {
  if [ -s "${KEY_CACHE}" ]; then
    cat "${KEY_CACHE}"
    return 0
  fi
  source scripts/lib/vault-admin-token.sh
  local vt
  vt="$(resolve_admin_vault_token)"
  local k
  k="$(docker exec -e VAULT_TOKEN="${vt}" vault-server vault kv get -field=api_key secret/syncthing/qnap 2>/dev/null || true)"
  if [ -n "${k}" ]; then
    mkdir -p "$(dirname "${KEY_CACHE}")"
    umask 077
    printf '%s' "${k}" > "${KEY_CACHE}"
  fi
  printf '%s' "${k}"
}

SYNC_KEY="$(resolve_sync_key)"
[ -n "${SYNC_KEY}" ] || { log "ERROR: missing Syncthing API key"; exit 1; }

source scripts/lib/vault-admin-token.sh
VT="$(resolve_admin_vault_token)"
QNAP_USER="$(docker exec -e VAULT_TOKEN="${VT}" vault-server vault kv get -field=user secret/qnap/admin)"
QNAP_PASS="$(docker exec -e VAULT_TOKEN="${VT}" vault-server vault kv get -field=password secret/qnap/admin)"

SSH_BASE=(
  sshpass -p "${QNAP_PASS}" ssh
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile=/dev/null
  -o ConnectTimeout=8
  -p 22
  "${QNAP_USER}@192.168.10.201"
)

remote_api() {
  local ep="$1"
  "${SSH_BASE[@]}" "curl -sf --connect-timeout 5 -H 'X-API-Key: ${SYNC_KEY}' 'http://127.0.0.1:8384${ep}'" 2>/dev/null || true
}

STATS_JSON="$(remote_api '/rest/stats/folder')"
STATUS_JSON="$(remote_api '/rest/db/status?folder=is5fj-3grur')"
STATUS_RT_JSON="$(remote_api '/rest/db/status?folder=3qukn-rfdel')"

if [ -z "${STATS_JSON}" ] || [ -z "${STATUS_JSON}" ]; then
  STATE=2
  LAST_COMPLETED_TS=0
  ERRORS_TOTAL=-1
  MAX_STALE_H=-1
else
  read -r STATE LAST_COMPLETED_TS ERRORS_TOTAL MAX_STALE_H <<EOF
$(python3 - <<'PY' "${STATS_JSON}" "${STATUS_JSON}" "${STATUS_RT_JSON}"
import datetime, json, sys
stats = json.loads(sys.argv[1])
sab = json.loads(sys.argv[2])
rt  = json.loads(sys.argv[3]) if sys.argv[3].strip() else {}
now = datetime.datetime.now(datetime.timezone.utc)

state_map = {"idle":0, "syncing":1, "scanning":1, "cleaning":1, "pulling":1}
st = (sab.get("state") or "error").lower()
state = state_map.get(st, 2)

errs = int(sab.get("errors", 0)) + int(sab.get("pullErrors", 0))
errs += int(rt.get("errors", 0)) + int(rt.get("pullErrors", 0))

max_h = 0
last_ts = 0
for _, v in stats.items():
    lf = (v or {}).get("lastFile", {})
    at = lf.get("at")
    if not at:
        continue
    ts = datetime.datetime.fromisoformat(at.replace("Z", "+00:00"))
    epoch = int(ts.timestamp())
    if epoch > last_ts:
        last_ts = epoch
    h = int((now - ts).total_seconds() // 3600)
    if h > max_h:
        max_h = h

print(state, last_ts, errs, max_h)
PY
)
EOF
fi

log "state=${STATE} last_completed_ts=${LAST_COMPLETED_TS} errors_total=${ERRORS_TOTAL} max_stale_h=${MAX_STALE_H}"

TMP="$(mktemp)"
cat > "${TMP}" <<EOF
${ZABBIX_HOST} d17105.syncthing.qnap.state ${STATE}
${ZABBIX_HOST} d17105.syncthing.qnap.last_completed_ts ${LAST_COMPLETED_TS}
${ZABBIX_HOST} d17105.syncthing.qnap.errors_total ${ERRORS_TOTAL}
${ZABBIX_HOST} d17105.syncthing.qnap.max_stale_h ${MAX_STALE_H}
EOF
/usr/local/bin/zabbix_sender -z "${ZABBIX_SERVER}" -p "${ZABBIX_PORT}" -i "${TMP}" >/dev/null 2>&1 || {
  rm -f "${TMP}"
  log "ERROR: zabbix_sender failed"
  exit 1
}
rm -f "${TMP}"

log "sent to Zabbix"
