#!/usr/bin/env bash
# validate-cmdb.sh — Validate service registry against live platform state
#
# Usage:
#   ./scripts/validate-cmdb.sh                    # full validation
#   ./scripts/validate-cmdb.sh --quick            # skip live health checks
#   ./scripts/validate-cmdb.sh --category ai      # check one category only
#   ./scripts/validate-cmdb.sh --service sonarr   # check single service
#
# Exit codes: 0=pass  1=failures found  2=script error

set -euo pipefail

# Ensure Docker CLI is on PATH (macOS Docker Desktop location)
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"

REGISTRY="$(cd "$(dirname "$0")/.." && pwd)/config/service-registry.yaml"
TIMEOUT=5
QUICK="false"
CATEGORY_FILTER=""
SERVICE_FILTER=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --quick)    QUICK="true";      shift ;;
    --category) CATEGORY_FILTER="$2"; shift 2 ;;
    --service)  SERVICE_FILTER="$2";  shift 2 ;;
    *) shift ;;
  esac
done

command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 required"; exit 2; }
command -v curl    >/dev/null 2>&1 || { echo "ERROR: curl required";    exit 2; }
python3 -c "import yaml" 2>/dev/null || { echo "ERROR: pip3 install pyyaml"; exit 2; }

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'; CYAN='\033[0;36m'; RESET='\033[0m'
pass()  { echo -e "${GREEN}  ✅ $1${RESET}"; }
fail()  { echo -e "${RED}  ❌ $1${RESET}"; FAILURES=$((FAILURES+1)); }
warn()  { echo -e "${YELLOW}  ⚠️  $1${RESET}"; WARNINGS=$((WARNINGS+1)); }
info()  { echo -e "${CYAN}  ℹ️  $1${RESET}"; }
header(){ echo -e "\n${CYAN}══ $1 ══${RESET}"; }

FAILURES=0; WARNINGS=0

# Use temp file to avoid heredoc variable interpolation issues
TMP_JSON=$(mktemp /tmp/cmdb-XXXXXX.json)
trap "rm -f $TMP_JSON" EXIT

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CMDB Validation — $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Registry: $REGISTRY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Schema validation ──────────────────────────────────────────────────────
header "1. Registry Schema"

if python3 <<PYEOF
import sys, yaml, json

try:
    with open("$REGISTRY") as f:
        reg = yaml.safe_load(f)
except Exception as e:
    print(f"SCHEMA_ERROR: Cannot parse YAML: {e}")
    sys.exit(1)

for key in ['metadata','services']:
    if key not in reg:
        print(f"SCHEMA_ERROR: Missing top-level key: {key}")
        sys.exit(1)

required = ['id','name','category','host','port','health_url']
errors = []
for svc in reg['services']:
    for f in required:
        if f not in svc:
            errors.append(f"{svc.get('id','?')}: missing '{f}'")

if errors:
    [print(f"SCHEMA_ERROR: {e}") for e in errors]
    sys.exit(1)

# Write JSON for downstream use
with open("$TMP_JSON", 'w') as f:
    json.dump(reg['services'], f)

print(f"OK: {len(reg['services'])} services, schema valid")
PYEOF
then pass "Registry YAML schema valid"
else fail "Registry YAML schema invalid"; fi

SERVICE_COUNT=$(python3 -c "import json; print(len(json.load(open('$TMP_JSON'))))" 2>/dev/null || echo "?")
info "Loaded $SERVICE_COUNT services from registry"

# ── 2. Port conflict check ────────────────────────────────────────────────────
header "2. Port Conflict Detection"

if python3 <<PYEOF
import json, sys
with open("$TMP_JSON") as f:
    services = json.load(f)
port_map = {}; conflicts = []
for svc in services:
    if svc.get('host') != 'mac-mini': continue
    port = svc.get('port')
    if not port: continue
    if port in port_map:
        conflicts.append(f"Port {port}: '{port_map[port]}' vs '{svc['id']}'")
    else:
        port_map[port] = svc['id']
if conflicts:
    [print(f"CONFLICT: {c}") for c in conflicts]; sys.exit(1)
else:
    print(f"OK: No port conflicts ({len(port_map)} mac-mini ports mapped)")
PYEOF
then pass "No port conflicts"
else fail "Port conflicts detected"; fi

# ── 3. Docker container cross-reference ──────────────────────────────────────
header "3. Container State vs Registry"

RUNNING_CONTAINERS_FILE=$(mktemp /tmp/cmdb-containers-XXXXXX)
docker ps --format '{{.Names}}' 2>/dev/null | sort > "$RUNNING_CONTAINERS_FILE"

python3 <<PYEOF
import json, sys

with open("$TMP_JSON") as f:
    services = json.load(f)
with open("$RUNNING_CONTAINERS_FILE") as f:
    running = set(l.strip() for l in f if l.strip())

# Containers declared in registry
registry_containers = {
    s['container'] for s in services
    if s.get('container') and s.get('host') == 'mac-mini'
}

missing = [
    f"{s['id']} (container: {s['container']})"
    for s in services
    if s.get('container') and s.get('host') == 'mac-mini'
    and s['container'] not in running
]
undocumented = sorted(running - registry_containers - {''})

for u in undocumented:
    print(f"WARN_UNDOCUMENTED: {u}")
for m in missing:
    print(f"MISSING: {m}")

print(f"SUMMARY: registry={len(registry_containers)} running={len(running)} undocumented={len(undocumented)} missing={len(missing)}")
PYEOF

MISSING_COUNT=$(python3 <<PYEOF
import json
with open("$TMP_JSON") as f: services = json.load(f)
with open("$RUNNING_CONTAINERS_FILE") as f:
    running = set(l.strip() for l in f if l.strip())
missing = [s for s in services if s.get('container') and s.get('host') == 'mac-mini' and s['container'] not in running]
print(len(missing))
PYEOF
)
rm -f "$RUNNING_CONTAINERS_FILE"

if [[ "$MISSING_COUNT" -eq 0 ]]; then
  pass "All registry containers running"
else
  fail "$MISSING_COUNT registry containers not found"
fi

# ── 4. Health endpoint checks ─────────────────────────────────────────────────
if [[ "$QUICK" != "true" ]]; then
  header "4. Service Health Checks"

  HEALTH_RESULTS=$(python3 <<PYEOF
import json, urllib.request, urllib.error, sys

with open("$TMP_JSON") as f:
    services = json.load(f)

for svc in services:
    url = svc.get('health_url')
    if not url or 'localhost' not in url:
        continue
    sid = svc['id']
    cat = svc.get('category','')
    if "$CATEGORY_FILTER" and cat != "$CATEGORY_FILTER": continue
    if "$SERVICE_FILTER" and sid != "$SERVICE_FILTER": continue

    expected = svc.get('health_expect', 200)
    if isinstance(expected, int): expected = [expected]

    try:
        req = urllib.request.Request(url, method='GET')
        req.add_header('User-Agent', 'cmdb-validator/1.0')
        with urllib.request.urlopen(req, timeout=$TIMEOUT) as r:
            status = r.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:
        print(f"FAIL\t{sid}\t{url}\t0\t{e}")
        continue

    if status in expected:
        print(f"PASS\t{sid}\t{url}\t{status}")
    else:
        print(f"FAIL\t{sid}\t{url}\t{status}\t(expected {expected})")
PYEOF
)

  HEALTH_PASS=0; HEALTH_FAIL=0
  while IFS=$'\t' read -r st sid url code extra; do
    [[ -z "$st" ]] && continue
    if [[ "$st" == "PASS" ]]; then
      pass "$sid — HTTP $code"
      HEALTH_PASS=$((HEALTH_PASS+1))
    else
      fail "$sid — $url → $code $extra"
      HEALTH_FAIL=$((HEALTH_FAIL+1))
    fi
  done <<< "$HEALTH_RESULTS"

  info "Health checks: ${HEALTH_PASS} passed, ${HEALTH_FAIL} failed"
else
  warn "Skipping health checks (--quick)"
fi

# ── 5. Dependency graph ────────────────────────────────────────────────────────
header "5. Dependency Graph"

if python3 <<PYEOF
import json, sys
with open("$TMP_JSON") as f: services = json.load(f)
ids = {s['id'] for s in services}
errors = []
for svc in services:
    for dep in svc.get('depends_on', []):
        if dep not in ids:
            errors.append(f"{svc['id']} → '{dep}' not in registry")
if errors:
    [print(f"DEP_ERROR: {e}") for e in errors]; sys.exit(1)
else:
    print(f"OK: dependency graph valid ({len(ids)} nodes)")
PYEOF
then pass "Dependency graph consistent"
else fail "Dependency graph has dangling references"; fi

# ── 6. Security baseline ──────────────────────────────────────────────────────
header "6. Security Baseline"

python3 <<PYEOF
import json, subprocess, sys

with open("$TMP_JSON") as f:
    services = json.load(f)

drift = []; skipped = []

for svc in services:
    container = svc.get('container')
    if not container or svc.get('host') != 'mac-mini': continue
    sec = svc.get('security') or {}
    claimed_nnp = sec.get('no_new_privileges')
    if claimed_nnp is None: continue
    try:
        r = subprocess.run(
            ['docker','inspect',container,'--format','{{range .HostConfig.SecurityOpt}}{{.}}{{end}}'],
            capture_output=True, text=True, timeout=5
        )
        live_nnp = 'no-new-privileges:true' in r.stdout.strip()
        if claimed_nnp and not live_nnp:
            drift.append(f"DRIFT: {svc['id']} claims nnp=true but container has it off")
    except Exception as e:
        skipped.append(f"SKIP: {svc['id']} — {e}")

for s in skipped: print(s)
if drift:
    for d in drift: print(d)
    sys.exit(1)
else:
    print(f"OK: Security config consistent (checked {len(services) - len(skipped)} containers)")
PYEOF

if [[ $? -eq 0 ]]; then pass "Security config matches registry"
else warn "Security drift detected"; fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $FAILURES -eq 0 ]]; then
  echo -e "${GREEN}  RESULT: ALL CHECKS PASSED ✅${RESET}"
  echo -e "  Failures: 0 | Warnings: $WARNINGS"
  exit 0
else
  echo -e "${RED}  RESULT: $FAILURES CHECK(S) FAILED ❌${RESET}"
  echo -e "  Warnings: $WARNINGS"
  exit 1
fi
