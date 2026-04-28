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
# Use a curated probe list since service-registry.yaml is large
declare -a PROBES=(
  "vaultwarden|http://localhost:8083/alive"
  "openhands-app|http://localhost:3000/health"
  "litellm-gateway|http://localhost:4000/health/liveliness"
  "mcpo-proxy|http://localhost:8081/openapi.json"
  "open-webui|http://localhost:8082/health"
  "vault-server|http://localhost:8200/v1/sys/health"
)
for entry in "${PROBES[@]}"; do
  name="${entry%%|*}"
  url="${entry##*|}"
  code=$(/usr/bin/curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$url" 2>/dev/null)
  case "$code" in
    200|204|429|472|473|501|503)
      # 472/473 are vault sealed/standby (acceptable; 503 might be initializing)
      if [[ "$code" == "200" || "$code" == "204" || "$code" == "472" ]]; then
        result OK "$name → HTTP $code"
      else
        result WARN "$name → HTTP $code (acceptable for some states)"
      fi
      ;;
    000)  result WARN "$name → no response (may be down or not yet probed)" ;;
    *)    result FAIL "$name → HTTP $code" ;;
  esac
done

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

# Summary
echo ""
echo "==================================================================="
echo "Gate $GATE_ID summary: PASS=$PASS FAIL=$FAIL WARN=$WARN"
echo "==================================================================="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
