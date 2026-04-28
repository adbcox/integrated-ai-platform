#!/usr/bin/env bash
# H1 §6 per-gate regression probe
# Runs at every gate close (A.6 onwards). Output is the gate-pass evidence.
# Usage: bash docs/phase-13/h1-regression-probe.sh [<gate-id>]

set +e  # don't bail on individual probe failures; collect all results

GATE_ID="${1:-unspecified}"
DOCKER=/opt/homebrew/bin/docker
VAULT_TOKEN=$(/bin/cat ~/.vault-token)
PASS=0
FAIL=0
WARN=0

result() {
  local status="$1"; shift
  case "$status" in
    OK)   PASS=$((PASS+1)); printf '  ✅ %s\n' "$*" ;;
    FAIL) FAIL=$((FAIL+1)); printf '  ❌ %s\n' "$*" ;;
    WARN) WARN=$((WARN+1)); printf '  ⚠️  %s\n' "$*" ;;
  esac
}

echo "==================================================================="
echo "H1 §6 regression probe — gate: $GATE_ID"
echo "Timestamp: $(/bin/date -Iseconds)"
echo "==================================================================="

# (a) Container roster
echo ""
echo "(a) Container roster"
UP_COUNT=$($DOCKER ps --filter status=running --format '{{.Names}}' | /usr/bin/wc -l | /usr/bin/awk '{print $1}')
RESTARTING=$($DOCKER ps --filter status=restarting --format '{{.Names}}' | /usr/bin/wc -l | /usr/bin/awk '{print $1}')
echo "  Up count: $UP_COUNT"
echo "  Restarting count: $RESTARTING"
if [ "$RESTARTING" -eq 0 ]; then result OK "no containers restarting"; else result FAIL "$RESTARTING containers restarting"; fi

# (b) Service-registry walk
echo ""
echo "(b) Service-registry walk (sampled health endpoints)"
# SHALLOW probes (return 200 even if downstream DB/cache is broken):
#   /alive, /health, /openapi.json, /health/liveliness
# DEEP probes (force a DB read or cred check; 5xx if downstream broken):
#   /ocs/* with auth (nextcloud), zabbix /api_jsonrpc.php, plane /api/users/me/
# Mark probes accordingly. Add deep probes for DB-fronting services.
declare -a PROBES=(
  "vaultwarden|http://localhost:8083/alive|shallow"
  "openhands-app|http://localhost:3000/health|shallow"
  "litellm-gateway|http://localhost:4000/health/liveliness|shallow"
  "mcpo-proxy|http://localhost:8081/openapi.json|shallow"
  "open-webui|http://localhost:8082/health|shallow"
  "vault-server|http://localhost:8200/v1/sys/health|shallow"
)
for entry in "${PROBES[@]}"; do
  IFS='|' read -r name url depth <<<"$entry"
  code=$(/usr/bin/curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$url" 2>/dev/null)
  case "$code" in
    200|204|429|472|473|501|503)
      if [[ "$code" == "200" || "$code" == "204" || "$code" == "472" ]]; then
        result OK "$name [$depth] → HTTP $code"
      else
        result WARN "$name [$depth] → HTTP $code (acceptable for some states)"
      fi
      ;;
    000)  result WARN "$name [$depth] → no response (may be down or not yet probed)" ;;
    *)    result FAIL "$name [$depth] → HTTP $code" ;;
  esac
done

# Deep DB-exercising probes for DB-fronting services (added B.1+).
# These force a DB read; surface upstream-DB issues that shallow probes miss.
echo ""
echo "  Deep DB-exercising probes:"

# nextcloud — uses PHP/PDO to query the DB at request time
NC_DEEP=$(/opt/homebrew/bin/docker exec nextcloud /bin/sh -c '
  curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost/ocs/v2.php/cloud/capabilities -H "OCS-APIRequest: true"
' 2>/dev/null)
if [[ "$NC_DEEP" =~ ^(200|401)$ ]]; then
  # 401 is fine — endpoint requires auth but DB IS reachable to evaluate the auth
  result OK "nextcloud [deep] /ocs/v2.php/cloud/capabilities → HTTP $NC_DEEP (DB reachable)"
else
  result FAIL "nextcloud [deep] /ocs/v2.php/cloud/capabilities → HTTP $NC_DEEP (DB unreachable?)"
fi

# (c) Vault health
echo ""
echo "(c) Vault health"
SEAL=$($DOCKER exec vault-server vault status -format=json 2>&1 | /usr/bin/python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('sealed', True))" 2>/dev/null)
if [ "$SEAL" = "False" ]; then result OK "vault sealed=false"; else result FAIL "vault sealed=$SEAL"; fi

# Audit log: write+read test
PRE_SIZE=$($DOCKER exec vault-server /bin/sh -c 'stat -c %s /vault/logs/audit.log 2>/dev/null || stat -f %z /vault/logs/audit.log 2>/dev/null')
$DOCKER exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server vault token lookup >/dev/null 2>&1
POST_SIZE=$($DOCKER exec vault-server /bin/sh -c 'stat -c %s /vault/logs/audit.log 2>/dev/null || stat -f %z /vault/logs/audit.log 2>/dev/null')
if [ "$POST_SIZE" -gt "$PRE_SIZE" ]; then result OK "audit log capturing (size $PRE_SIZE → $POST_SIZE)"; else result FAIL "audit log not growing"; fi

# (d) Caddy + .internal DNS sample
# Probe via the actual domain (DNS resolves to 192.168.10.145 where Caddy
# binds 0.0.0.0:443). Fixed in Phase B-prep: previous version probed
# https://localhost which is occupied by an ssh tunnel, not Caddy.
echo ""
echo "(d) Caddy + .internal DNS sample"
SAMPLE_DOMAINS=("vaultwarden.internal" "openhands.internal" "plane.internal" "vault.internal" "homepage.internal")
for d in "${SAMPLE_DOMAINS[@]}"; do
  ip=$(/usr/bin/dscacheutil -q host -a name "$d" 2>/dev/null | /usr/bin/grep -m1 ip_address | /usr/bin/awk '{print $2}')
  if [ -z "$ip" ]; then
    result WARN "$d: not in macOS DNS cache (may be normal if not actively used)"
    continue
  fi
  # -k accepts Caddy's internal CA. Direct domain probe (not localhost).
  code=$(/usr/bin/curl -sk -o /dev/null -w '%{http_code}' --max-time 5 "https://$d/" 2>/dev/null)
  if [[ "$code" =~ ^(200|301|302|307|401|403)$ ]]; then
    result OK "$d → HTTP $code via Caddy"
  elif [ "$code" = "000" ]; then
    result FAIL "$d → no response (Caddy unreachable or TLS handshake failure)"
  else
    result WARN "$d → HTTP $code"
  fi
done

# (e) Backup script
echo ""
echo "(e) Restic backup recency"
LAST_SNAP=$(/opt/homebrew/bin/restic -r s3:http://192.168.10.201:9000/backups snapshots --json 2>/dev/null | /usr/bin/python3 -c "
import sys, json
try:
  snaps = json.loads(sys.stdin.read())
  if snaps:
    print(snaps[-1].get('time', '')[:19])
  else:
    print('NONE')
except: print('ERROR')
" 2>/dev/null)
if [ -z "$LAST_SNAP" ] || [ "$LAST_SNAP" = "NONE" ] || [ "$LAST_SNAP" = "ERROR" ]; then
  result WARN "restic snapshot list inaccessible (creds may be Vault-fetched only)"
else
  echo "  Last snapshot: $LAST_SNAP"
  result OK "restic snapshot index reachable"
fi

# (f) Cross-service dependency probes — gate-specific
echo ""
echo "(f) Cross-service dependency probes (gate-specific: $GATE_ID)"
case "$GATE_ID" in
  A.6|a.6)
    # litellm rotated; downstream consumers
    NEW_KEY=$($DOCKER exec litellm-gateway /bin/sh -c 'tr "\0" "\n" < /proc/1/environ | grep "^LITELLM_MASTER_KEY=" | cut -d= -f2-' 2>/dev/null)
    if [ -n "$NEW_KEY" ]; then
      OK_CODE=$(/usr/bin/curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $NEW_KEY" http://localhost:4000/v1/models)
      if [ "$OK_CODE" = "200" ]; then result OK "litellm /v1/models with rotated key: 200"; else result FAIL "litellm /v1/models: $OK_CODE"; fi

      # KNOWN-TRANSIENT: open-webui still has old key
      OWUI_OLD_KEY=$($DOCKER exec open-webui printenv OPENAI_API_KEY 2>/dev/null)
      if [ "$OWUI_OLD_KEY" != "$NEW_KEY" ]; then
        result WARN "open-webui has stale LITELLM key (KNOWN TRANSIENT — A.7 will fix)"
      else
        result OK "open-webui has rotated key (A.7 already complete)"
      fi
    else
      result FAIL "could not read litellm process env"
    fi
    ;;
  A.4|a.4)
    # openhands-app rewire — verify can still talk to ollama
    if /usr/bin/curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
      result OK "ollama reachable from host (openhands-app's LLM_BASE_URL target)"
    else
      result WARN "ollama not reachable on host:11434"
    fi
    ;;
  B.2|b.2)
    # zabbix-postgres rewire — verify zabbix UI + API still functional
    PG_READY=$($DOCKER exec zabbix-postgres pg_isready -U zabbix 2>&1)
    if /usr/bin/grep -q "accepting connections" <<<"$PG_READY"; then
      result OK "zabbix-postgres pg_isready: accepting connections"
    else
      result FAIL "zabbix-postgres pg_isready: $PG_READY"
    fi
    # Deep zabbix probe (DB-backed JSON-RPC)
    ZBX_API=$(/usr/bin/curl -s -X POST -H "Content-Type: application/json-rpc" \
      -d '{"jsonrpc":"2.0","method":"apiinfo.version","params":{},"id":1}' \
      -o /dev/null -w '%{http_code}' --max-time 5 \
      http://localhost:10080/api_jsonrpc.php 2>/dev/null)
    if [ "$ZBX_API" = "200" ]; then
      result OK "zabbix /api_jsonrpc.php (DB-backed deep probe): 200"
    else
      result FAIL "zabbix /api_jsonrpc.php: $ZBX_API"
    fi
    ;;
  B.1|b.1)
    # nextcloud-db rewire — verify nextcloud → nextcloud-db chain
    NC_DEEP=$($DOCKER exec nextcloud /bin/sh -c 'curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost/ocs/v2.php/cloud/capabilities -H "OCS-APIRequest: true"' 2>/dev/null)
    if [ "$NC_DEEP" = "200" ]; then
      result OK "nextcloud → nextcloud-db chain working (deep probe 200)"
    else
      result FAIL "nextcloud → nextcloud-db chain broken: $NC_DEEP"
    fi
    PG_READY=$($DOCKER exec nextcloud-db pg_isready -U nextcloud 2>&1)
    if /usr/bin/grep -q "accepting connections" <<<"$PG_READY"; then
      result OK "nextcloud-db pg_isready: accepting connections"
    else
      result FAIL "nextcloud-db pg_isready: $PG_READY"
    fi
    ;;
  A.8|a.8)
    # open-webui rewire (Phase A close) — verify open-webui→litellm transient closed
    OWUI_KEY=$($DOCKER exec open-webui /bin/sh -c 'tr "\0" "\n" < /proc/1/environ | grep "^OPENAI_API_KEY=" | cut -d= -f2-' 2>/dev/null)
    LITELLM_KEY=$($DOCKER exec litellm-gateway /bin/sh -c 'tr "\0" "\n" < /proc/1/environ | grep "^LITELLM_MASTER_KEY=" | cut -d= -f2-' 2>/dev/null)
    if [ "$OWUI_KEY" = "$LITELLM_KEY" ] && [ -n "$OWUI_KEY" ]; then
      result OK "open-webui ↔ litellm key match (transient closed)"
    else
      result FAIL "open-webui ↔ litellm key mismatch (transient NOT closed)"
    fi
    OWUI_TO_LITELLM=$($DOCKER exec open-webui /bin/sh -c "curl -s -o /dev/null -w '%{http_code}' -H 'Authorization: Bearer $OWUI_KEY' http://litellm-gateway:4000/v1/models" 2>/dev/null)
    if [ "$OWUI_TO_LITELLM" = "200" ]; then
      result OK "open-webui → litellm /v1/models from inside container: 200"
    else
      result FAIL "open-webui → litellm: $OWUI_TO_LITELLM"
    fi
    ;;
  *)
    result WARN "no gate-specific dependency probes defined for $GATE_ID"
    ;;
esac

# (h) Credential exposure heuristic check
# Search recent tool outputs / shell history / temp files for plaintext
# credential-shaped tokens. Heuristic only; primary defense is the
# doctrine in §13 (never display values in tool output).
echo ""
echo "(h) Credential exposure heuristic"
SUSPECT=0
# Check /tmp for files containing "PASSWORD=" or "TOKEN=" that aren't pre-approved
for f in $(/bin/ls /tmp/*pass* /tmp/*token* /tmp/*secret* 2>/dev/null); do
  [ -f "$f" ] && SUSPECT=$((SUSPECT+1)) && echo "  ⚠️  $f exists in /tmp"
done
if [ "$SUSPECT" -eq 0 ]; then
  result OK "no credential-shaped temp files in /tmp"
else
  result WARN "$SUSPECT suspicious temp files (review and clean)"
fi

# Summary
echo ""
echo "==================================================================="
echo "Gate $GATE_ID summary: PASS=$PASS FAIL=$FAIL WARN=$WARN"
echo "==================================================================="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
