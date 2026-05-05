#!/usr/bin/env bash
# D-17-119 — QNAP Syncthing REST collector + Zabbix sender.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "${ROOT_DIR}/scripts/lib/vault-admin-token.sh"

QNAP_URL="${QNAP_URL:-http://192.168.10.201:8384}"
ZABBIX_HOST="${ZABBIX_HOST:-qnap-ts-x72}"
ZABBIX_SERVER="${ZABBIX_SERVER:-127.0.0.1}"
ZABBIX_PORT="${ZABBIX_PORT:-10051}"
FOLDER_ID="${FOLDER_ID:-is5fj-3grur}"

log() { printf '[qnap-syncthing] %s\n' "$*"; }

VAULT_TOKEN="$(resolve_admin_vault_token)"
SYNC_KEY="$(docker exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server vault kv get -field=api_key secret/syncthing/qnap)"

curl_json() {
  local path="$1"
  curl -sS -m 5 -H "X-API-Key: ${SYNC_KEY}" "${QNAP_URL}${path}"
}

tmp="$(mktemp)"
trap 'rm -f "${tmp}"' EXIT

alive=0
folder_state=3
need_files=0
need_bytes=0
uptime=0

if ping_json="$(curl_json /rest/system/ping)"; then
  if echo "${ping_json}" | jq -e '.ping == "pong"' >/dev/null 2>&1; then
    alive=1
  fi
fi

if status_json="$(curl_json "/rest/db/status?folder=${FOLDER_ID}")"; then
  folder_state="$(echo "${status_json}" | jq -r 'if ((.state // "error") | ascii_downcase) == "idle" then "0" elif ((.state // "error") | ascii_downcase) == "syncing" then "1" elif ((.state // "error") | ascii_downcase) == "scanning" then "2" elif ((.state // "error") | ascii_downcase) == "error" then "3" else "255" end')"
  need_files="$(echo "${status_json}" | jq -r '.needFiles // 0')"
  need_bytes="$(echo "${status_json}" | jq -r '.needBytes // 0')"
fi

if uptime_json="$(curl_json /rest/system/status)"; then
  uptime="$(echo "${uptime_json}" | jq -r '.uptime // 0')"
fi

cat > "${tmp}" <<EOF
${ZABBIX_HOST} d17119.qnap.syncthing.rest.alive ${alive}
${ZABBIX_HOST} d17119.qnap.syncthing.folder.state ${folder_state}
${ZABBIX_HOST} d17119.qnap.syncthing.folder.need_files ${need_files}
${ZABBIX_HOST} d17119.qnap.syncthing.folder.need_bytes ${need_bytes}
${ZABBIX_HOST} d17119.qnap.syncthing.system.uptime ${uptime}
EOF

zabbix_sender -z "${ZABBIX_SERVER}" -p "${ZABBIX_PORT}" -i "${tmp}" >/dev/null
log "sent qnap syncthing metrics (alive=${alive}, state=${folder_state}, need_files=${need_files}, need_bytes=${need_bytes}, uptime=${uptime})"
