#!/usr/bin/env bash
# cmdb-equivalence.sh — prove YAML and NetBox CMDB sources are equivalent
# for the fields validate-cmdb.sh consumes.
#
# Block 4.C C5.2a evidence harness. Run:
#     ./scripts/cmdb-equivalence.sh
#     ./scripts/cmdb-equivalence.sh --full   # diff every field, not just
#                                            # validate-cmdb's consumed set
#
# Exit 0 = equivalent on consumed fields. Exit 1 = mismatch found.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

MODE="consumed"
[[ "${1:-}" == "--full" ]] && MODE="full"

YAML_OUT=$(mktemp /tmp/cmdb-yaml-XXXXXX.json)
NB_OUT=$(mktemp /tmp/cmdb-nb-XXXXXX.json)
trap "rm -f $YAML_OUT $NB_OUT" EXIT

echo "── Loading YAML backend ──"
CMDB_SOURCE=yaml python3 scripts/cmdb_source.py > "$YAML_OUT"
echo "── Loading NetBox backend ──"
CMDB_SOURCE=netbox python3 scripts/cmdb_source.py > "$NB_OUT"

python3 <<PYEOF
import json
y = json.load(open("$YAML_OUT"))
n = json.load(open("$NB_OUT"))

# Index by id
yi = {s['id']: s for s in y}
ni = {s['id']: s for s in n}

print(f"YAML count: {len(y)}    NetBox count: {len(n)}")
miss_in_nb = sorted(set(yi) - set(ni))
miss_in_y  = sorted(set(ni) - set(yi))
if miss_in_nb: print(f"  ❌ in YAML, missing in NetBox: {miss_in_nb}")
if miss_in_y:  print(f"  ❌ in NetBox, missing in YAML: {miss_in_y}")

# Fields validate-cmdb.sh actually consumes (per script audit):
#   schema:        id, name, category, host, port, health_url
#   port-conflict: host, port    (mac-mini only)
#   container-state: container, host
#   health-check:  health_url, health_expect
#   dep-graph:     id, depends_on
#   sec-baseline:  container, host, security.no_new_privileges
CONSUMED = {
    "id","name","category","host","port","container",
    "health_url","health_expect","depends_on","security",
}

mode = "$MODE"
if mode == "consumed":
    print(f"\n── Comparing {len(CONSUMED)} consumed fields across {len(yi)} services ──")
else:
    print(f"\n── Comparing ALL fields (full mode) across {len(yi)} services ──")

mismatches = []
for sid in sorted(set(yi) & set(ni)):
    ys = yi[sid]; ns = ni[sid]
    if mode == "consumed":
        keys = CONSUMED
    else:
        keys = set(ys.keys()) | set(ns.keys())
    # health_expect is dead-field unless service has a health_url
    # (validate-cmdb's loop is gated on 'localhost' in health_url).
    # Normalize None vs default 200 to "absent" when no URL.
    has_health_url = bool(ys.get("health_url") or ns.get("health_url"))
    for k in sorted(keys):
        yv = ys.get(k)
        nv = ns.get(k)
        # Normalize: empty list vs absent, empty dict vs absent
        if yv in (None, "", [], {}): yv = None
        if nv in (None, "", [], {}): nv = None
        if k == "health_expect" and not has_health_url:
            # Field is unused (validate-cmdb's loop is gated on
            # 'localhost' in health_url). Any value here is dead.
            yv = nv = None
        # Lists: compare as sorted (order doesn't matter for depends_on)
        if isinstance(yv, list) and isinstance(nv, list):
            yv = sorted(yv) if all(isinstance(x, str) for x in yv) else yv
            nv = sorted(nv) if all(isinstance(x, str) for x in nv) else nv
        # security.no_new_privileges is the only nested field consumed
        if k == "security" and mode == "consumed":
            yv_n = (ys.get("security") or {}).get("no_new_privileges")
            nv_n = (ns.get("security") or {}).get("no_new_privileges")
            if yv_n != nv_n:
                mismatches.append((sid, "security.no_new_privileges", yv_n, nv_n))
            continue
        if yv != nv:
            mismatches.append((sid, k, yv, nv))

if mismatches:
    print(f"\n  ❌ {len(mismatches)} field mismatches across {len(set(m[0] for m in mismatches))} services")
    # Group by field
    from collections import defaultdict
    by_field = defaultdict(list)
    for sid, k, yv, nv in mismatches:
        by_field[k].append((sid, yv, nv))
    for k in sorted(by_field):
        rows = by_field[k]
        print(f"\n    field={k}  ({len(rows)} services)")
        for sid, yv, nv in rows[:5]:
            yvs = repr(yv)[:60]
            nvs = repr(nv)[:60]
            print(f"      {sid:30s}  yaml={yvs}  netbox={nvs}")
        if len(rows) > 5:
            print(f"      ... {len(rows)-5} more")
    raise SystemExit(1)

if miss_in_nb or miss_in_y:
    raise SystemExit(1)
print(f"\n  ✅ EQUIVALENT on {('all fields' if mode=='full' else 'consumed fields')}")
PYEOF
