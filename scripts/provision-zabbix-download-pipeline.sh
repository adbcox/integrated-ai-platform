#!/usr/bin/env bash
# D-17-105 — Provision Zabbix monitoring for download pipeline health.
# Idempotent-ish: creates/updates hostgroup, template, macros, items, triggers.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "${ROOT_DIR}/scripts/lib/vault-admin-token.sh"

ZABBIX_API_URL="${ZABBIX_API_URL:-http://127.0.0.1:10080/api_jsonrpc.php}"
TARGET_HOST_NAME="${TARGET_HOST_NAME:-mac-mini}"
GROUP_NAME="${GROUP_NAME:-Download Pipeline}"
TEMPLATE_NAME="${TEMPLATE_NAME:-Template Download Pipeline HTTP}"

log() { printf '[d-17-105] %s\n' "$*"; }

VAULT_TOKEN="$(resolve_admin_vault_token)"
ZABBIX_TOKEN="$(docker exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server vault kv get -field=api_token secret/zabbix/exporter)"

zbx() {
  local method="$1"
  local params_json="$2"
  local resp
  resp="$(curl -sS \
    -H 'Content-Type: application/json-rpc' \
    -H "Authorization: Bearer ${ZABBIX_TOKEN}" \
    -d "{\"jsonrpc\":\"2.0\",\"method\":\"${method}\",\"params\":${params_json},\"id\":1}" \
    "${ZABBIX_API_URL}")"
  if echo "${resp}" | jq -e '.error' >/dev/null 2>&1; then
    echo "${resp}" >&2
    return 1
  fi
  printf '%s' "${resp}"
}

get_arr_key() {
  local c="$1"
  docker exec "$c" sh -lc "sed -n 's:.*<ApiKey>\\(.*\\)</ApiKey>.*:\\1:p' /config/config.xml | head -n1"
}

get_bazarr_key() {
  docker exec bazarr sh -lc "sed -n 's/^  apikey: //p' /config/config/config.yaml | head -n1"
}

ensure_group() {
  local gid
  gid="$(zbx hostgroup.get "{\"output\":[\"groupid\"],\"filter\":{\"name\":[\"${GROUP_NAME}\"]}}" | jq -r '.result[0].groupid // empty')"
  if [ -z "${gid}" ]; then
    gid="$(zbx hostgroup.create "{\"name\":\"${GROUP_NAME}\"}" | jq -r '.result.groupids[0]')"
    log "created hostgroup ${GROUP_NAME} (${gid})"
  fi
  printf '%s' "${gid}"
}

ensure_host() {
  local hid
  hid="$(zbx host.get "{\"output\":[\"hostid\"],\"filter\":{\"host\":[\"${TARGET_HOST_NAME}\"]}}" | jq -r '.result[0].hostid // empty')"
  if [ -z "${hid}" ]; then
    log "ERROR: host ${TARGET_HOST_NAME} not found in Zabbix"
    exit 1
  fi
  printf '%s' "${hid}"
}

ensure_macro() {
  local hostid="$1" macro="$2" value="$3"
  local existing
  existing="$(zbx usermacro.get "{\"output\":[\"hostmacroid\",\"macro\"],\"hostids\":[\"${hostid}\"],\"filter\":{\"macro\":\"${macro}\"}}" | jq -r '.result[0].hostmacroid // empty')"
  if [ -z "${existing}" ]; then
    zbx usermacro.create "{\"hostid\":\"${hostid}\",\"macro\":\"${macro}\",\"value\":\"${value}\"}" >/dev/null
  else
    zbx usermacro.update "{\"hostmacroid\":\"${existing}\",\"value\":\"${value}\"}" >/dev/null
  fi
}

ensure_item() {
  local hostid="$1" name="$2" key="$3" url="$4" header="$5" ptype="$6" pparams="$7"
  local itemid
  itemid="$(zbx item.get "{\"output\":[\"itemid\"],\"hostids\":[\"${hostid}\"],\"filter\":{\"key_\":\"${key}\"}}" | jq -r '.result[0].itemid // empty')"
  local payload
  payload="$(jq -nc \
    --arg hostid "${hostid}" \
    --arg name "${name}" \
    --arg key "${key}" \
    --arg url "${url}" \
    --arg header "${header}" \
    --arg pparams "${pparams}" \
    --argjson ptype "${ptype}" \
    '{
      hostid:$hostid,name:$name,key_:$key,
      type:19,value_type:3,delay:"5m",url:$url,request_method:0,retrieve_mode:0,
      headers:[{name:"X-Api-Key",value:$header}],
      preprocessing:[{type:$ptype,params:$pparams,error_handler:0,error_handler_params:""}]
    }')"
  if [ -z "${itemid}" ]; then
    zbx item.create "${payload}" >/dev/null
  else
    zbx item.update "$(echo "${payload}" | jq --arg itemid "${itemid}" 'del(.hostid) + {itemid:$itemid}')" >/dev/null
  fi
}

ensure_trapper() {
  local hostid="$1" name="$2" key="$3"
  local itemid
  itemid="$(zbx item.get "{\"output\":[\"itemid\",\"type\"],\"hostids\":[\"${hostid}\"],\"filter\":{\"key_\":\"${key}\"}}" | jq -r '.result[0].itemid // empty')"
  local payload
  payload="$(jq -nc --arg hostid "${hostid}" --arg name "${name}" --arg key "${key}" \
    '{hostid:$hostid,name:$name,key_:$key,type:2,value_type:3,delay:"0"}')"
  if [ -z "${itemid}" ]; then
    zbx item.create "${payload}" >/dev/null
  else
    # Only update if currently not a trapper (avoid clobbering lastvalue)
    local cur_type
    cur_type="$(zbx item.get "{\"output\":[\"type\"],\"hostids\":[\"${hostid}\"],\"filter\":{\"key_\":\"${key}\"}}" | jq -r '.result[0].type // ""')"
    if [ "${cur_type}" != "2" ]; then
      zbx item.update "$(echo "${payload}" | jq --arg itemid "${itemid}" 'del(.hostid) + {itemid:$itemid}')" >/dev/null
    fi
  fi
}

ensure_trigger() {
  local desc="$1" expr="$2" priority="$3"
  local trig
  trig="$(zbx trigger.get "{\"output\":[\"triggerid\"],\"filter\":{\"description\":[\"${desc}\"]}}" | jq -r '.result[0].triggerid // empty')"
  if [ -z "${trig}" ]; then
    zbx trigger.create "{\"description\":\"${desc}\",\"expression\":\"${expr}\",\"priority\":${priority}}" >/dev/null
  else
    zbx trigger.update "{\"triggerid\":\"${trig}\",\"expression\":\"${expr}\",\"priority\":${priority}}" >/dev/null
  fi
}

main() {
  local groupid hostid sab_url sab_key sab_base
  local sync_qnap_url sync_qnap_key
  local zbx_http_base="http://192.168.10.145"
  groupid="$(ensure_group)"
  hostid="$(ensure_host)"

  # Host grouping/template linking can be permission-scoped; monitoring items are host-level.
  zbx hostgroup.get "{\"output\":[\"groupid\"],\"filter\":{\"groupid\":[\"${groupid}\"]}}" >/dev/null

  local sonarr_key radarr_key lidarr_key prowlarr_key bazarr_key
  sonarr_key="$(get_arr_key sonarr)"
  radarr_key="$(get_arr_key radarr)"
  lidarr_key="$(get_arr_key lidarr)"
  prowlarr_key="$(get_arr_key prowlarr)"
  bazarr_key="$(get_bazarr_key)"

  sab_url="$(docker exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server vault kv get -field=url secret/seedbox/sabnzbd)"
  sab_key="$(docker exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server vault kv get -field=api_key secret/seedbox/sabnzbd)"
  sync_qnap_url="$(docker exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server vault kv get -field=web_url secret/syncthing/qnap 2>/dev/null || true)"
  sync_qnap_key="$(docker exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server vault kv get -field=api_key secret/syncthing/qnap 2>/dev/null || true)"
  if [[ "${sab_url}" == */api ]]; then
    sab_base="${sab_url}"
  else
    sab_base="${sab_url%/}/api"
  fi

  ensure_macro "${hostid}" '{$SONARR_API_KEY}' "${sonarr_key}"
  ensure_macro "${hostid}" '{$RADARR_API_KEY}' "${radarr_key}"
  ensure_macro "${hostid}" '{$LIDARR_API_KEY}' "${lidarr_key}"
  ensure_macro "${hostid}" '{$PROWLARR_API_KEY}' "${prowlarr_key}"
  ensure_macro "${hostid}" '{$BAZARR_API_KEY}' "${bazarr_key}"
  ensure_macro "${hostid}" '{$SABNZBD_API_KEY}' "${sab_key}"
  if [ -n "${sync_qnap_key}" ]; then
    ensure_macro "${hostid}" '{$SYNCTHING_QNAP_API_KEY}' "${sync_qnap_key}"
  fi
  ensure_macro "${hostid}" '{$PIPE_STUCK_HOURS}' "2"
  ensure_macro "${hostid}" '{$PIPE_DISK_MIN_PCT}' "10"
  ensure_macro "${hostid}" '{$PIPE_IMPORT_FAIL_PCT}' "5"
  ensure_macro "${hostid}" '{$PIPE_SYNC_STALE_HOURS}' "48"

  ensure_item "${hostid}" "Sonarr queue depth" "d17105.sonarr.queue_depth" "${zbx_http_base}:8989/api/v3/queue?page=1&pageSize=1" '{$SONARR_API_KEY}' 12 '$.totalRecords'
  ensure_item "${hostid}" "Radarr queue depth" "d17105.radarr.queue_depth" "${zbx_http_base}:7878/api/v3/queue?page=1&pageSize=1" '{$RADARR_API_KEY}' 12 '$.totalRecords'
  ensure_item "${hostid}" "Lidarr queue depth" "d17105.lidarr.queue_depth" "${zbx_http_base}:8686/api/v1/queue?page=1&pageSize=1" '{$LIDARR_API_KEY}' 12 '$.totalRecords'
  ensure_item "${hostid}" "Sonarr health issue count" "d17105.sonarr.health_count" "${zbx_http_base}:8989/api/v3/health" '{$SONARR_API_KEY}' 21 'var a=JSON.parse(value); return Array.isArray(a)?a.length:0;'
  ensure_item "${hostid}" "Radarr health issue count" "d17105.radarr.health_count" "${zbx_http_base}:7878/api/v3/health" '{$RADARR_API_KEY}' 21 'var a=JSON.parse(value); return Array.isArray(a)?a.length:0;'
  ensure_item "${hostid}" "Lidarr health issue count" "d17105.lidarr.health_count" "${zbx_http_base}:8686/api/v1/health" '{$LIDARR_API_KEY}' 21 'var a=JSON.parse(value); return Array.isArray(a)?a.length:0;'
  ensure_item "${hostid}" "Prowlarr health issue count" "d17105.prowlarr.health_count" "${zbx_http_base}:9696/api/v1/health" '{$PROWLARR_API_KEY}' 21 'var a=JSON.parse(value); return Array.isArray(a)?a.length:0;'
  ensure_item "${hostid}" "SABnzbd queue depth" "d17105.sab.queue_depth" "${sab_base}?mode=queue&output=json&apikey={\$SABNZBD_API_KEY}" '{$SABNZBD_API_KEY}' 12 '$.queue.noofslots'
  # SABnzbd failed jobs: JSONPath $.history.noofslots on mode=history&failed_only=1 response
  # (noofslots = count of returned slots; failed_only=1 filters to failures only)
  ensure_item "${hostid}" "SABnzbd failed jobs" "d17105.sab.failed_jobs" "${sab_base}?mode=history&output=json&apikey={\$SABNZBD_API_KEY}&failed_only=1&limit=100" '{$SABNZBD_API_KEY}' 12 '$.history.noofslots'

  # Syncthing items are Zabbix Trapper (type=2) — data pushed by scripts/syncthing-zabbix-sender.sh
  # running on the Mac Mini host (Docker containers cannot reach QNAP:8384 due to subnet filtering).
  ensure_trapper "${hostid}" "Syncthing QNAP state" "d17105.syncthing.qnap.state"
  ensure_trapper "${hostid}" "Syncthing QNAP last completed ts" "d17105.syncthing.qnap.last_completed_ts"
  ensure_trapper "${hostid}" "Syncthing QNAP max staleness hours" "d17105.syncthing.qnap.max_stale_h"
  ensure_trapper "${hostid}" "Syncthing QNAP folder errors total" "d17105.syncthing.qnap.errors_total"

  ensure_trigger "D-17-105: Sonarr queue depth high" "min(/${TARGET_HOST_NAME}/d17105.sonarr.queue_depth,2h)>0" 3
  ensure_trigger "D-17-105: Radarr queue depth high" "min(/${TARGET_HOST_NAME}/d17105.radarr.queue_depth,2h)>0" 3
  ensure_trigger "D-17-105: Lidarr queue depth high" "min(/${TARGET_HOST_NAME}/d17105.lidarr.queue_depth,2h)>0" 3
  ensure_trigger "D-17-105: Arr health issues present" "last(/${TARGET_HOST_NAME}/d17105.sonarr.health_count)>0 or last(/${TARGET_HOST_NAME}/d17105.radarr.health_count)>0 or last(/${TARGET_HOST_NAME}/d17105.lidarr.health_count)>0 or last(/${TARGET_HOST_NAME}/d17105.prowlarr.health_count)>0" 3
  ensure_trigger "D-17-105: SABnzbd failed jobs detected" "last(/${TARGET_HOST_NAME}/d17105.sab.failed_jobs)>0" 3
  # Syncthing triggers always present — trapper items receive data from syncthing-zabbix-sender.sh
  ensure_trigger "D-17-105: Syncthing staleness > 48h" "last(/${TARGET_HOST_NAME}/d17105.syncthing.qnap.max_stale_h)>{\$PIPE_SYNC_STALE_HOURS}" 3
  ensure_trigger "D-17-105: Syncthing folder errors present" "last(/${TARGET_HOST_NAME}/d17105.syncthing.qnap.errors_total)>0" 3
  ensure_trigger "D-17-105: Syncthing state error" "last(/${TARGET_HOST_NAME}/d17105.syncthing.qnap.state)=2" 3

  log "provision complete"
  log "Syncthing: trapper items — push via scripts/syncthing-zabbix-sender.sh (launchd com.iap.syncthing-zabbix-sender)"
}

main "$@"
