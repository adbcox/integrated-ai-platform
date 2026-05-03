#!/usr/bin/env bash
# D-17-50 — functional-probe-based Prowlarr↔consumer resync sweep.
#
# Doctrine pivot (2026-05-03): Sonarr/Radarr consumer-side Prowlarr indexer
# apiKeys can validly differ from Prowlarr master key (two-key model). Remediation
# trigger is functional auth failure (HTTP 401), not hash mismatch.

set -euo pipefail

LOG_DIR="/Users/admin/.platform-logs"
HEARTBEAT="$LOG_DIR/arr-apikey-sweep.heartbeat"
STATUS_JSON="$LOG_DIR/arr-apikey-sweep.status.json"
MAX_AGE_SEC=5400  # hourly schedule + 30m grace

mkdir -p "$LOG_DIR"

PROWLARR_HOST="http://localhost:9696"

consumers=("sonarr:8989:sonarr" "radarr:7878:radarr" "sportarr:1867:sportarr")

sha12() { printf %s "$1" | shasum -a 256 | awk '{print substr($1,1,12)}'; }

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

xml_apikey_from_container() {
  local container="$1"
  docker exec "$container" sh -lc "sed -n 's:.*<ApiKey>\\(.*\\)</ApiKey>.*:\\1:p' /config/config.xml | head -n1"
}

json_get() {
  local url="$1" key="$2"
  curl -sS -H "X-Api-Key: $key" "$url"
}

probe_release() {
  local hostport="$1" key="$2"
  local url="http://localhost:${hostport}/api/v3/release?query=test"
  local body
  body=$(mktemp)
  local code
  code=$(curl -sS -o "$body" -w "%{http_code}" "$url" -H "X-Api-Key: $key" || true)
  local count="-1"
  if [ "$code" = "200" ]; then
    count=$(python3 - <<'PY' "$body"
import json,sys
try:
 d=json.load(open(sys.argv[1]))
 print(len(d) if isinstance(d,list) else -1)
except Exception:
 print(-2)
PY
)
  fi
  rm -f "$body"
  printf '%s %s\n' "$code" "$count"
}

recreate_application() {
  local app_name="$1" consumer_key="$2" prowlarr_key="$3"

  local apps_json app_id payload resp new_id
  apps_json=$(json_get "$PROWLARR_HOST/api/v1/applications" "$prowlarr_key")
  app_id=$(python3 - <<'PY' "$apps_json" "$app_name"
import json,sys
apps=json.loads(sys.argv[1]); name=sys.argv[2].lower()
for a in apps:
    if (a.get('name') or '').lower()==name:
        print(a.get('id',''))
        break
PY
)
  if [ -z "$app_id" ]; then
    log "WARN app-not-found name=$app_name"
    return 1
  fi

  payload=$(python3 - <<'PY' "$apps_json" "$app_id" "$consumer_key"
import json,sys
apps=json.loads(sys.argv[1]); app_id=int(sys.argv[2]); ckey=sys.argv[3]
a=next(x for x in apps if x.get('id')==app_id)
field_map={f.get('name'):f.get('value') for f in a.get('fields',[])}
out={
  'name': a.get('name'),
  'syncLevel': a.get('syncLevel'),
  'implementation': a.get('implementation'),
  'configContract': a.get('configContract'),
  'tags': a.get('tags',[]),
  'fields': []
}
ordered=['prowlarrUrl','baseUrl','apiKey','syncCategories','animeSyncCategories','syncRejectBlocklistedTorrentHashesWhileGrabbing']
for n in ordered:
    v=ckey if n=='apiKey' else field_map.get(n)
    if v is not None:
        out['fields'].append({'name':n,'value':v})
print(json.dumps(out))
PY
)

  curl -sS -X DELETE -H "X-Api-Key: $prowlarr_key" "$PROWLARR_HOST/api/v1/applications/$app_id" >/dev/null
  resp=$(curl -sS -X POST -H "X-Api-Key: $prowlarr_key" -H 'Content-Type: application/json' -d "$payload" "$PROWLARR_HOST/api/v1/applications")
  new_id=$(python3 - <<'PY' "$resp"
import json,sys
try:
 d=json.loads(sys.argv[1]); print(d.get('id',''))
except Exception:
 print('')
PY
)
  if [ -z "$new_id" ]; then
    log "ERROR recreate-failed app=$app_name"
    return 1
  fi
  log "INFO recreated app=$app_name old_id=$app_id new_id=$new_id"
  return 0
}

force_sync() {
  local prowlarr_key="$1"
  local cmd id status=""
  cmd=$(curl -sS -X POST -H "X-Api-Key: $prowlarr_key" -H 'Content-Type: application/json' -d '{"name":"ApplicationIndexerSync","forceSync":true}' "$PROWLARR_HOST/api/v1/command")
  id=$(python3 - <<'PY' "$cmd"
import json,sys
print(json.loads(sys.argv[1]).get('id',''))
PY
)
  if [ -z "$id" ]; then
    log "ERROR sync-command-create-failed"
    return 1
  fi
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    status=$(curl -sS -H "X-Api-Key: $prowlarr_key" "$PROWLARR_HOST/api/v1/command/$id" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status",""))')
    [ "$status" = "completed" ] && break
    sleep 2
  done
  log "INFO sync status=$status cmd_id=$id"
  [ "$status" = "completed" ]
}

row_hash_report() {
  local hostport="$1" key="$2" app="$3"
  python3 - <<'PY' "$hostport" "$key" "$app"
import json,sys,urllib.request,hashlib
hp,key,app=sys.argv[1],sys.argv[2],sys.argv[3]
req=urllib.request.Request(f'http://localhost:{hp}/api/v3/indexer',headers={'X-Api-Key':key})
arr=json.loads(urllib.request.urlopen(req).read().decode())
for i in arr:
    name=i.get('name','')
    if '(Prowlarr)' not in name:
        continue
    fields={f.get('name'):f.get('value') for f in i.get('fields',[])}
    api=fields.get('apiKey','')
    h=hashlib.sha256(api.encode()).hexdigest()[:12] if api else 'missing'
    print(f"row_hash app={app} indexer={name} api_sha12={h} baseUrl={fields.get('baseUrl','')}")
PY
}

main() {
  local prowlarr_key
  prowlarr_key=$(xml_apikey_from_container prowlarr)
  if [ -z "$prowlarr_key" ]; then
    log "ERROR missing-prowlarr-key"
    exit 1
  fi

  local now_epoch
  now_epoch=$(date +%s)
  local recreates=0 probe_failures=0

  for row in "${consumers[@]}"; do
    IFS=':' read -r app hostport container <<< "$row"
    local ckey
    ckey=$(xml_apikey_from_container "$container")
    if [ -z "$ckey" ]; then
      log "ERROR missing-consumer-key app=$app"
      probe_failures=$((probe_failures+1))
      continue
    fi

    local key_hash
    key_hash=$(sha12 "$ckey")
    read -r code count < <(probe_release "$hostport" "$ckey")
    log "probe app=$app code=$code results=$count consumer_key_sha12=$key_hash"

    if [ "$code" = "401" ]; then
      log "WARN auth-failure app=$app trigger=recreate"
      if recreate_application "$app" "$ckey" "$prowlarr_key"; then
        recreates=$((recreates+1))
        force_sync "$prowlarr_key" || true
        read -r code2 count2 < <(probe_release "$hostport" "$ckey")
        log "post_recreate_probe app=$app code=$code2 results=$count2"
      else
        probe_failures=$((probe_failures+1))
      fi
    fi

    row_hash_report "$hostport" "$ckey" "$app"
  done

  touch "$HEARTBEAT"
  cat > "$STATUS_JSON" <<JSON
{
  "timestamp_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "epoch": $now_epoch,
  "max_age_sec": $MAX_AGE_SEC,
  "recreates": $recreates,
  "probe_failures": $probe_failures
}
JSON

  log "done recreates=$recreates probe_failures=$probe_failures heartbeat=$HEARTBEAT status=$STATUS_JSON"
}

main "$@"
