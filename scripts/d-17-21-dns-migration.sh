#!/usr/bin/env bash
# D-17-21 — Migrate DNS authority from Unbound to Dnsmasq.
#
# Steps:
#   1. Snapshot current Unbound + Dnsmasq state
#   2. Add 38 Unbound .internal overrides + 12 missing records to Dnsmasq
#   3. Apply Dnsmasq config; validate resolution on port 53053
#   4. Stop + disable Unbound
#   5. Move Dnsmasq from port 53053 → 53
#   6. Apply Dnsmasq config; validate resolution on port 53
#   7. Final smoke check (all 50 records resolve via :53)
#
# Halts on any error. Snapshots written to ~/.platform-logs/d-17-21/.

set -euo pipefail

LOG_DIR="$HOME/.platform-logs/d-17-21"
mkdir -p "$LOG_DIR"
TS=$(date +%Y%m%d-%H%M%S)

# ── Load OPNsense API credentials via Vault AppRole ───────────────────────────
ROLE_ID=$(cat ~/.vault-approle/opnsense-api-reader/role-id)
SECRET_ID=$(cat ~/.vault-approle/opnsense-api-reader/secret-id)
LOGIN=$(curl -s -X POST -d "{\"role_id\":\"$ROLE_ID\",\"secret_id\":\"$SECRET_ID\"}" \
    http://127.0.0.1:8200/v1/auth/approle/login)
VT=$(echo "$LOGIN" | jq -r ".auth.client_token")
KEY=$(curl -s -H "X-Vault-Token: $VT" \
    "http://127.0.0.1:8200/v1/secret/data/opnsense/api" | jq -r ".data.data.api_key")
SEC=$(curl -s -H "X-Vault-Token: $VT" \
    "http://127.0.0.1:8200/v1/secret/data/opnsense/api" | jq -r ".data.data.api_secret")
unset VT
[ -n "$KEY" ] && [ -n "$SEC" ] || { echo "ABORT: cannot load OPNsense API key"; exit 1; }

API="https://192.168.10.1/api"
CURL=(curl -s -k -u "$KEY:$SEC")

api_get()  { "${CURL[@]}" "$API$1"; }
api_post() { "${CURL[@]}" -X POST -H "Content-Type: application/json" -d "$2" "$API$1"; }

# ── Step 1 — Snapshots ────────────────────────────────────────────────────────
echo ">>> Step 1: Snapshot Unbound + Dnsmasq state"
api_get /unbound/settings/searchHostOverride?searchPhrase=\&current=1\&rowCount=200 \
    > "$LOG_DIR/unbound-overrides-pre-$TS.json"
api_get /dnsmasq/settings/searchHost \
    > "$LOG_DIR/dnsmasq-hosts-pre-$TS.json"
api_get /unbound/settings/get \
    > "$LOG_DIR/unbound-settings-pre-$TS.json"
api_get /dnsmasq/settings/get \
    > "$LOG_DIR/dnsmasq-settings-pre-$TS.json"

UNBOUND_COUNT=$(jq '.rows | length' "$LOG_DIR/unbound-overrides-pre-$TS.json")
DNSMASQ_COUNT=$(jq '.rows | length' "$LOG_DIR/dnsmasq-hosts-pre-$TS.json")
DNSMASQ_PORT_PRE=$(jq -r '.dnsmasq.port' "$LOG_DIR/dnsmasq-settings-pre-$TS.json")
echo "  Unbound .internal overrides: $UNBOUND_COUNT"
echo "  Dnsmasq host entries: $DNSMASQ_COUNT"
echo "  Dnsmasq current port: $DNSMASQ_PORT_PRE"
echo "  Snapshots: $LOG_DIR/*-pre-$TS.json"

# ── Step 2 — Build merged record list (38 Unbound + 12 missing) ─────────────
echo ""
echo ">>> Step 2: Build migration record list"

# Pull existing Dnsmasq hosts (so we don't double-add)
EXISTING_DNSMASQ_FQDNS=$(jq -r '.rows[] | "\(.host).\(.domain)"' "$LOG_DIR/dnsmasq-hosts-pre-$TS.json" | sort -u)

# Source records from Unbound
jq -r '.rows[] | "\(.hostname)|\(.domain)|\(.server)|\(.description)"' "$LOG_DIR/unbound-overrides-pre-$TS.json" \
    > "$LOG_DIR/from-unbound-$TS.txt"

# Add 12 missing records: 11 NXDOMAIN Caddy sites + mac-studio.internal
cat > "$LOG_DIR/additional-$TS.txt" <<EOF
architecture|internal|192.168.10.145|Caddy front (D-17-21 add)
docs|internal|192.168.10.145|Caddy front (D-17-21 add)
homeassistant|internal|192.168.10.141|Home Assistant hub (D-17-21 add)
inventree|internal|192.168.10.145|Caddy front (D-17-21 add)
loki|internal|192.168.10.145|Caddy front (D-17-21 add)
mac-studio|internal|192.168.10.142|Mac Studio compute node (D-17-21 add)
mcp-xindex|internal|192.168.10.145|Caddy front (D-17-21 add)
netbox|internal|192.168.10.145|Caddy front (D-17-21 add)
openproject|internal|192.168.10.145|Caddy front (D-17-21 add)
physical-architecture|internal|192.168.10.145|Caddy front (D-17-21 add)
structurizr|internal|192.168.10.145|Caddy front (D-17-21 add)
xindex|internal|192.168.10.145|Caddy front (D-17-21 add)
EOF

cat "$LOG_DIR/from-unbound-$TS.txt" "$LOG_DIR/additional-$TS.txt" > "$LOG_DIR/migration-list-$TS.txt"
TOTAL=$(wc -l < "$LOG_DIR/migration-list-$TS.txt" | tr -d ' ')
echo "  Records to migrate (Unbound) + add (new): $TOTAL"

# ── Step 3 — Add records to Dnsmasq ─────────────────────────────────────────
echo ""
echo ">>> Step 3: Add records to Dnsmasq (skip any already present)"
ADDED=0
SKIPPED=0
FAILED=0
while IFS='|' read -r host domain ip descr; do
    fqdn="${host}.${domain}"
    if echo "$EXISTING_DNSMASQ_FQDNS" | grep -qx "$fqdn"; then
        echo "  SKIP $fqdn (already in Dnsmasq)"
        SKIPPED=$((SKIPPED+1))
        continue
    fi
    payload=$(jq -nc \
        --arg h "$host" --arg d "$domain" --arg i "$ip" --arg s "$descr" \
        '{host:{host:$h, domain:$d, local:"0", ip:$i, descr:$s}}')
    resp=$(api_post /dnsmasq/settings/addHost "$payload")
    result=$(echo "$resp" | jq -r '.result')
    if [ "$result" = "saved" ]; then
        ADDED=$((ADDED+1))
    else
        echo "  FAIL $fqdn: $resp"
        FAILED=$((FAILED+1))
    fi
done < "$LOG_DIR/migration-list-$TS.txt"
echo "  Added: $ADDED  Skipped: $SKIPPED  Failed: $FAILED"
[ "$FAILED" -eq 0 ] || { echo "ABORT: $FAILED add(s) failed"; exit 2; }

echo ""
echo ">>> Step 3b: Apply Dnsmasq config (reconfigure)"
api_post /dnsmasq/service/reconfigure '{}' | jq '.'
sleep 3

# ── Step 4 — Validate every record resolves on port 53053 ───────────────────
echo ""
echo ">>> Step 4: Validate resolution on port 53053 (Dnsmasq current port)"
FAIL_RESOLVE=0
while IFS='|' read -r host domain ip descr; do
    fqdn="${host}.${domain}"
    actual=$(dig @192.168.10.1 -p 53053 "$fqdn" +short +tries=1 +time=2 | head -1)
    if [ "$actual" = "$ip" ]; then
        :  # OK
    else
        echo "  RESOLVE-FAIL $fqdn  expected=$ip  got=${actual:-NXDOMAIN}"
        FAIL_RESOLVE=$((FAIL_RESOLVE+1))
    fi
done < "$LOG_DIR/migration-list-$TS.txt"
echo "  Resolve failures (port 53053): $FAIL_RESOLVE"
[ "$FAIL_RESOLVE" -eq 0 ] || { echo "ABORT: $FAIL_RESOLVE record(s) failed to resolve via Dnsmasq pre-port-flip; not safe to disable Unbound"; exit 3; }

# ── Step 5 — Stop + disable Unbound (frees port 53) ─────────────────────────
echo ""
echo ">>> Step 5: Stop + disable Unbound"
echo "  setOption (set unbound.general.enabled=0)"
api_post /unbound/settings/set '{"unbound":{"general":{"enabled":"0"}}}' | jq '.'
echo "  reconfigure (apply disable)"
api_post /unbound/service/reconfigure '{}' | jq '.'
echo "  stop service"
api_post /unbound/service/stop '{}' | jq '.'
sleep 2
echo "  status after stop:"
api_get /unbound/service/status | jq '.'

# ── Step 6 — Move Dnsmasq from 53053 → 53 ───────────────────────────────────
echo ""
echo ">>> Step 6: Move Dnsmasq port 53053 → 53"
api_post /dnsmasq/settings/set '{"dnsmasq":{"port":"53","dns_port":"53"}}' | jq '.'
echo "  reconfigure (rebind to :53)"
api_post /dnsmasq/service/reconfigure '{}' | jq '.'
sleep 3
echo "  status after port flip:"
api_get /dnsmasq/service/status | jq '.'

# ── Step 7 — Final smoke: all records resolve via :53 ───────────────────────
echo ""
echo ">>> Step 7: Final smoke — every migrated record resolves via :53"
FINAL_FAIL=0
while IFS='|' read -r host domain ip descr; do
    fqdn="${host}.${domain}"
    actual=$(dig @192.168.10.1 -p 53 "$fqdn" +short +tries=2 +time=3 | head -1)
    if [ "$actual" = "$ip" ]; then
        :
    else
        echo "  FINAL-FAIL $fqdn  expected=$ip  got=${actual:-NXDOMAIN}"
        FINAL_FAIL=$((FINAL_FAIL+1))
    fi
done < "$LOG_DIR/migration-list-$TS.txt"

# ── Post-snapshot ────────────────────────────────────────────────────────────
api_get /dnsmasq/settings/searchHost > "$LOG_DIR/dnsmasq-hosts-post-$TS.json"
api_get /dnsmasq/settings/get > "$LOG_DIR/dnsmasq-settings-post-$TS.json"
api_get /unbound/settings/get > "$LOG_DIR/unbound-settings-post-$TS.json"

DNSMASQ_COUNT_POST=$(jq '.rows | length' "$LOG_DIR/dnsmasq-hosts-post-$TS.json")
DNSMASQ_PORT_POST=$(jq -r '.dnsmasq.port' "$LOG_DIR/dnsmasq-settings-post-$TS.json")
UNBOUND_ENABLED_POST=$(jq -r '.unbound.general.enabled // .unbound.enabled // "unknown"' "$LOG_DIR/unbound-settings-post-$TS.json")

echo ""
echo "=== Migration summary ==="
echo "  Unbound .internal overrides pre:  $UNBOUND_COUNT"
echo "  Dnsmasq host entries pre:         $DNSMASQ_COUNT  (port $DNSMASQ_PORT_PRE)"
echo "  Dnsmasq host entries post:        $DNSMASQ_COUNT_POST  (port $DNSMASQ_PORT_POST)"
echo "  Records added this run:           $ADDED"
echo "  Records skipped (existing):       $SKIPPED"
echo "  Resolve failures on :53053 pre:   $FAIL_RESOLVE"
echo "  Resolve failures on :53 final:    $FINAL_FAIL"
echo "  Unbound enabled (post):           $UNBOUND_ENABLED_POST"
echo ""
[ "$FINAL_FAIL" -eq 0 ] && echo "RESULT: PASS — Dnsmasq is sole authority on :53" || \
    echo "RESULT: $FINAL_FAIL record(s) did not resolve on :53; investigate before closing D-17-21"
exit "$FINAL_FAIL"
