# Phase 14 — Remaining Work Execution Handoff

**Date:** 2026-04-30
**HEAD at handoff:** `d2de969` (prior handoff doc) / `3a15faa` (D-DOC addendum, fully closed)
**D-DOC status:** CLOSED. All 17 + addendum sub-tasks complete. Addendum commit `3a15faa`.
**Regression baseline for all remaining gates:** PASS=15 FAIL=0 WARN=3.

**Remaining scope:**
- Plane backlog curation (D-DOC sub-task 14, deferred, no deps, fits any window)
- Window 2: D-STR + D-MKD
- Window 3: D-ZBX + D-RST
- Window 4: D-LOG
- Window 5: D-XINDEX
- Window 6: CL-14

Surface only at CL-14 for final audit.

---

## Port registry — allocated as of handoff

Allocated localhost ports (do not reuse):

| Port | Service |
|---|---|
| 1867 | out-of-repo stack |
| 3002 | out-of-repo stack |
| 4000 | out-of-repo stack |
| 7575 | out-of-repo stack |
| 7878 | out-of-repo stack |
| 8081 | out-of-repo stack |
| 8084 | netbox |
| 8086 | topology-api / control-plane |
| 8087 | inventree |
| 8094 | plex-mcp |
| 8123 | out-of-repo stack |
| 8124 | out-of-repo stack |
| 8200 | vault |
| 8201 | vault cluster |
| 8989 | out-of-repo stack |
| 9696 | out-of-repo stack |
| 10080 | zabbix-web |
| 10443 | zabbix-web TLS |

**Available for Phase 14 blocks:** 8088 (D-STR), 8089 (D-MKD), 9224 (D-ZBX),
3100 (D-LOG Loki), 9080 (D-LOG Promtail). Confirm with `ss -tlnp` before deploy.

---

## Context files — read before beginning any block

```
docs/phase-14/PHASE_14_CAMPAIGN_PLAN_2026-04-29.md
docs/phase-14/PHASE_14_BLOCK_D_DOC_CLOSEOUT_2026-04-29.md   ← addendum at end
docs/canonical-patterns/plane-connector-usage.md             ← mandatory for Plane writes
docs/runbooks/operating-model.md
docs/runbooks/add-new-service.md                             ← Vault sidecar pattern
CLAUDE.md
docs/DECISION_REGISTER.md
```

---

## Plane backlog curation (D-DOC sub-task 14) — run in any window

**No blocking dependencies.** NF-14-2 is resolved (Plane auth works). Run this
in whichever window has slack. Estimate: 1–1.5h.

**Gate:** Full IV&V (A-011). 429-risk. First-batch-verify mandatory.

### Scope

- Apply 64 existing Plane labels to ~1100 issues via prefix-mapping.
- Re-triage urgent-priority: from 44 → <10.
- Close ~88 issues already in Done state.

### Mandatory pattern requirements

Per `docs/canonical-patterns/plane-connector-usage.md`:

```python
from framework.plane_connector import PlaneAPI, RateLimitError
import time, sys

api = PlaneAPI()

# §1: always import RateLimitError alongside PlaneAPI (done above)

# §2: catch RateLimitError BEFORE except Exception — order is load-bearing
# §4: first-batch-verify before bulk run
# §3: pace writes at ~1.5s between mutations (60 req/min limit)
```

### Execution

**Step 1 — Audit current label state:**

```bash
python3 - <<'EOF'
from framework.plane_connector import PlaneAPI, RateLimitError
api = PlaneAPI()
labels = api._get("/labels/")
issues = api.list_all_issues()
labeled = [i for i in issues if i.get("labels")]
urgent  = [i for i in issues if i.get("priority") == "urgent"]
done    = [i for i in issues if i.get("state_name","").lower() in ("done","closed")]
print(f"Labels available: {len(labels.get('results',[]))}")
print(f"Issues total:     {len(issues)}")
print(f"Issues labeled:   {len(labeled)}")
print(f"Urgent priority:  {len(urgent)}")
print(f"Done state:       {len(done)}")
EOF
```

**Step 2 — Build prefix → label mapping:**

```bash
python3 - <<'EOF'
from framework.plane_connector import PlaneAPI, RateLimitError
api = PlaneAPI()
labels = api._get("/labels/")["results"]
for l in sorted(labels, key=lambda x: x["name"]):
    print(f"  {l['id']}  {l['name']}")
EOF
# Review output: match label names to issue-title prefixes (RM-, INFRA-, OPS-, etc.)
# Build LABEL_MAP = {"prefix": "label-uuid", ...} in the curation script
```

**Step 3 — Write and run `scripts/curate-plane-backlog.py`:**

```python
#!/usr/bin/env python3
"""Plane backlog curation: label assignment + priority triage + Done closure."""
import sys
import time
from framework.plane_connector import PlaneAPI, RateLimitError

api = PlaneAPI()

# Build from Step 2 output — replace UUIDs with actuals
LABEL_MAP: dict[str, str] = {
    "RM-":    "<roadmap-label-uuid>",
    "INFRA-": "<infra-label-uuid>",
    "OPS-":   "<ops-label-uuid>",
    # ... extend from Step 2 output
}

def _apply_label(issue: dict, label_uuid: str) -> bool:
    """Apply a single label to an issue if not already present."""
    current = issue.get("labels", [])
    if label_uuid in current:
        return False
    try:
        api._patch(f"/issues/{issue['id']}/", {"labels": current + [label_uuid]})
        return True
    except RateLimitError:
        raise
    except Exception as exc:
        print(f"  ERROR on {issue['id']}: {exc}", file=sys.stderr)
        return False

issues = api.list_all_issues()
first_write_verified = False
writes = 0

for issue in issues:
    title = issue.get("name", "")
    matched_label = next(
        (uid for prefix, uid in LABEL_MAP.items() if title.startswith(prefix)),
        None,
    )
    if matched_label is None:
        continue
    try:
        changed = _apply_label(issue, matched_label)
        if changed:
            writes += 1
            # §4 first-batch-verify: read back after first write
            if not first_write_verified:
                if not api.verify_issue_field(issue["id"], "labels", [matched_label]):
                    print("ABORT: first-batch-verify failed — labels not landing",
                          file=sys.stderr)
                    sys.exit(2)
                first_write_verified = True
                print(f"  VERIFIED: first write landed on {issue['id']}")
            time.sleep(1.5)  # §3 pace
    except RateLimitError as exc:
        print(f"  RATE-LIMIT: {exc} — sleeping 60s", file=sys.stderr)
        time.sleep(60)
        # retry once
        try:
            _apply_label(issue, matched_label)
            writes += 1
            time.sleep(1.5)
        except Exception as retry_exc:
            print(f"  RETRY-FAIL: {retry_exc}", file=sys.stderr)

print(f"Label writes: {writes}")
```

**Step 4 — Priority triage (separate pass after labels):**

```bash
# List urgent issues for manual review — do NOT bulk-retriage programmatically
python3 - <<'EOF'
from framework.plane_connector import PlaneAPI
api = PlaneAPI()
urgent = [i for i in api.list_all_issues() if i.get("priority") == "urgent"]
print(f"Urgent: {len(urgent)}")
for i in sorted(urgent, key=lambda x: x.get("sequence_id",0)):
    print(f"  #{i.get('sequence_id','?')}  {i['name'][:70]}")
EOF
# Review list, lower priority on items that are clearly not urgent
# Use api.update_issue_state or api._patch for each — do manually to avoid mistakes
```

**Step 5 — Close Done-state issues:**

```bash
python3 - <<'EOF'
from framework.plane_connector import PlaneAPI, RateLimitError
import time
api = PlaneAPI()
done_issues = [i for i in api.list_all_issues()
               if i.get("state_name","").lower() in ("done","closed","cancelled")]
print(f"Done-state issues: {len(done_issues)}")
# Confirm count before proceeding — only close if count matches expectation (~88)
input("Press enter to begin closure, Ctrl-C to abort: ")
for issue in done_issues:
    try:
        # Mark as archived / ensure state is terminal
        # Plane CE: use update to set state_name to Cancelled if Done isn't terminal
        time.sleep(1.5)
    except RateLimitError as exc:
        print(f"  RATE-LIMIT — sleeping 60s")
        time.sleep(60)
EOF
```

### Exit gate

- [ ] `scripts/curate-plane-backlog.py` committed.
- [ ] ≥95% of issues have at least one label (verify with audit query from Step 1).
- [ ] Urgent-priority count ≤10 (manual triage complete).
- [ ] ~88 Done-state issues closed.
- [ ] Zero RateLimitError silently swallowed (check stderr output).
- [ ] First-batch-verify passed before bulk run.

**Commit:** `feat(phase-14-curation): Plane backlog curation — labels + triage + Done closure`

---

## Window 2 — D-STR + D-MKD

**Estimate:** D-STR 2–4h + D-MKD 3–5h = 5–9h combined.
**Both are novel container + Caddy route deployments.** Do D-STR first; it is simpler.
Gate each separately before starting the next. Share the Caddy reload step.

### D-STR — Structurizr Lite

**Purpose:** Self-hosted C4-model diagram server. Closes state-anchoring gap (g)
for the visual topology layer. Structurizr Lite is auth-free for local use —
no Vault sidecar needed.

**Port:** 8088 (Structurizr Lite container → 8080 internal).

#### Step 1 — Pre-deploy check

```bash
ss -tlnp | grep 8088  # must be empty
docker pull structurizr/lite
docker inspect structurizr/lite --format '{{index .RepoDigests 0}}'
# Record digest — pin to it in compose
```

#### Step 2 — Directory and workspace

```bash
mkdir -p docker/structurizr/workspace
```

Create `docker/structurizr/workspace/workspace.dsl`:

```dsl
workspace "Integrated AI Platform" "Phase 13/14 baseline — 2026-04-30" {

    model {
        operator = person "Operator" "Platform maintainer"

        platform = softwareSystem "AI Platform" "Mac Mini M5 control plane" {
            caddy     = container "Caddy"          "Reverse proxy + TLS (*.internal)"    "Caddy 2.x"
            vault     = container "Vault"           "Secret store + AppRole auth"          "HashiCorp Vault"
            netbox    = container "NetBox"          "CMDB — service + network inventory"   "NetBox CE"
            plane     = container "Plane"           "Roadmap + issue tracker"              "Plane CE"
            inventree = container "InvenTree"       "Parts CMDB"                           "InvenTree"
            grafana   = container "Grafana"         "Observability dashboards"             "Grafana OSS"
            zabbix    = container "Zabbix"          "Host + service monitoring"            "Zabbix 7.4"
            vm        = container "VictoriaMetrics" "Metrics store"                        "VictoriaMetrics"
            loki      = container "Loki"            "Log aggregation (Caddy per-site)"     "Grafana Loki"
            structurizr = container "Structurizr"  "C4 architecture diagrams"             "Structurizr Lite"
            mkdocs    = container "MkDocs"          "Internal documentation site"          "MkDocs Material"
            ollama    = container "Ollama"          "Local LLM inference"                  "Ollama"
            litellm   = container "LiteLLM"         "LLM gateway (local models)"           "LiteLLM"
            openhands = container "OpenHands"       "AI coding agent"                      "OpenHands"
        }

        operator -> caddy "accesses via *.internal"
        caddy -> vault
        caddy -> netbox
        caddy -> plane
        caddy -> inventree
        caddy -> grafana
        caddy -> structurizr
        caddy -> mkdocs
        litellm -> ollama
        openhands -> litellm
    }

    views {
        systemContext platform "SystemContext" {
            include *
            autolayout lr
        }
        container platform "Containers" {
            include *
            autolayout lr
        }
        theme default
    }
}
```

#### Step 3 — Compose file

Create `docker/structurizr/docker-compose.yml`:

```yaml
services:
  structurizr:
    image: structurizr/lite@<digest-from-step-1>
    container_name: structurizr
    restart: unless-stopped
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    read_only: false   # Structurizr writes session state to its data dir
    mem_limit: 512m
    ports:
      - "127.0.0.1:8088:8080"
    volumes:
      - ./workspace:/usr/local/structurizr
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/ || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
```

#### Step 4 — Caddy route

Append to `docker/caddy/Caddyfile`:

```caddyfile
structurizr.internal {
    import access_log
    reverse_proxy structurizr:8080
}
```

#### Step 5 — Deploy and validate

```bash
docker compose -f docker/structurizr/docker-compose.yml up -d
docker ps | grep structurizr   # Up ... (healthy)
curl -s http://localhost:8088/ | head -5   # HTML response

docker exec caddy caddy reload --config /etc/caddy/Caddyfile
sleep 5
curl -s -o /dev/null -w "%{http_code}" https://structurizr.internal/
# Expect 200
```

Open `https://structurizr.internal/` in browser. Verify System Context and
Container diagrams render. Verify no browser console errors.

#### D-STR exit gate

- [ ] `structurizr` container Up (healthy), `cap_drop:[ALL]`, port 8088.
- [ ] `https://structurizr.internal/` → 200 via Caddy.
- [ ] Both C4 diagrams render in browser without error.
- [ ] `docker/structurizr/docker-compose.yml` and `workspace.dsl` committed.
- [ ] Caddy route committed.

**Commit:** `feat(phase-14-D-STR): Structurizr Lite — C4 workspace at structurizr.internal`

---

### D-MKD — MkDocs + Material

**Purpose:** Publishes the `docs/` tree as a searchable internal site at
`docs.internal`. Prose and navigation complement Structurizr's diagrams.

**Port:** 8089 (MkDocs → 8000 internal).

**Critical pre-check:**

```bash
ls docs/adr/ | grep A-007
# Must return: ADR-A-007-media-sync-syncthing.md
# The mkdocs.yml nav must use the full filename — no shorthand
```

#### Step 1 — Create `docs/index.md`

MkDocs requires an `index.md` at the docs root:

```markdown
# Integrated AI Platform

Enterprise autonomous AI infrastructure on Mac Mini M5.

- **Architecture overview:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Decision register (ADRs):** [DECISION_REGISTER.md](DECISION_REGISTER.md)
- **Runbooks:** see Runbooks section in the navigation
- **Diagrams:** [structurizr.internal](https://structurizr.internal) (C4 model)
- **Live service inventory:** [netbox.internal](https://netbox.internal)

Current phase: Phase 14 (D-DOC closed; D-STR/D-MKD/D-LOG/D-ZBX/D-RST/D-XINDEX in progress).
```

#### Step 2 — Create `mkdocs.yml` at repo root

```yaml
site_name: Integrated AI Platform
site_url: https://docs.internal
docs_dir: docs
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy
  palette:
    - scheme: slate
      primary: indigo
      accent: indigo

nav:
  - Home: index.md
  - Architecture:
      - Overview: ARCHITECTURE.md
      - Dependency Graph: architecture/dependency-graph.md
      - MCP Servers: architecture/mcp-server-architecture.md
      - Portability: architecture/portability.md
  - Decision Register: DECISION_REGISTER.md
  - ADRs:
      - Index: adr/README.md
      - ADR-A-001 Retain control plane: adr/ADR-A-001.md
      - ADR-A-002 Shared runtime substrate: adr/ADR-A-002.md
      - ADR-A-003 Ollama-first coding: adr/ADR-A-003.md
      - ADR-A-004 Aider as adapter: adr/ADR-A-004.md
      - ADR-A-005 Claude Code supervisory: adr/ADR-A-005.md
      - ADR-A-006 Repo docs canonical: adr/ADR-A-006.md
      - ADR-A-007 Syncthing media sync: adr/ADR-A-007-media-sync-syncthing.md
      - ADR-A-008 No branch forks: adr/ADR-A-008.md
      - ADR-A-009 Vault secret store: adr/ADR-A-009.md
      - ADR-A-010 External systems: adr/ADR-A-010-external-systems.md
      - ADR-A-011 IV&V loop: adr/ADR-A-011-ivv-loop-pattern.md
      - ADR-A-012 Equivalence harness: adr/ADR-A-012-equivalence-harness-doctrine.md
      - ADR-A-013 Folded gates: adr/ADR-A-013-folded-gates-doctrine.md
  - Runbooks:
      - Add New Service: runbooks/add-new-service.md
      - Add New Host: runbooks/add-new-host.md
      - Add New MCP Server: runbooks/add-new-mcp-server.md
      - Restart Services: runbooks/restart-services.md
      - Rotate Credentials: runbooks/rotate-credentials.md
      - Vault Unseal: runbooks/vault-unseal.md
      - Vault Token Rotation: runbooks/vault-token-rotation.md
      - Vault Rekey: runbooks/vault-rekey.md
      - Vault Recovery (Shamir): runbooks/vault-recovery-from-shamir.md
      - Vault Restore from Backup: runbooks/vault-restore-from-backup.md
      - Backup & Restore: runbooks/backup-restore.md
      - Drift Detection: runbooks/drift-detection-procedure.md
      - Regression Probe Failure: runbooks/regression-probe-failure.md
      - Incident Response: runbooks/incident-response.md
      - Plane Web Auth: runbooks/plane-web-auth.md
      - Operating Model: runbooks/operating-model.md
      - H1 Rollback: runbooks/H1-rollback.md
      - What Changed (24h): runbooks/what-changed-last-24h.md
  - Canonical Patterns:
      - Plane Connector: canonical-patterns/plane-connector-usage.md
  - Known Issues:
      - KI-004 mcp-docs-remote: known-issues/KI-004-mcp-docs-remote-startup.md

plugins:
  - search
```

Note: if `docs/runbooks/backup-restore.md` does not exist yet (it is D-RST scope),
omit it from this nav. Add it when D-RST commits the file.

#### Step 3 — Compose file

Create `docker/mkdocs/docker-compose.yml`:

```yaml
services:
  mkdocs:
    image: squidfunk/mkdocs-material@<digest-after-pull>
    container_name: mkdocs
    restart: unless-stopped
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    read_only: true
    mem_limit: 256m
    ports:
      - "127.0.0.1:8089:8000"
    volumes:
      - ../../docs:/docs:ro
      - ../../mkdocs.yml:/docs/mkdocs.yml:ro
    command: ["serve", "--dev-addr=0.0.0.0:8000", "--no-livereload"]
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/ || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 45s
```

#### Step 4 — Caddy route

Append to `docker/caddy/Caddyfile`:

```caddyfile
docs.internal {
    import access_log
    reverse_proxy mkdocs:8000
}
```

#### Step 5 — Deploy and validate

```bash
docker pull squidfunk/mkdocs-material
docker inspect squidfunk/mkdocs-material --format '{{index .RepoDigests 0}}'
# Update digest in compose file above

docker compose -f docker/mkdocs/docker-compose.yml up -d
docker logs mkdocs --tail=20   # watch for "Serving on http://0.0.0.0:8000"
# Common failure: missing file referenced in mkdocs.yml nav
# If MkDocs exits: docker logs mkdocs 2>&1 | grep -i "error\|warning\|missing"

curl -s http://localhost:8089/ | grep -i "material\|Integrated"

docker exec caddy caddy reload --config /etc/caddy/Caddyfile
curl -s -o /dev/null -w "%{http_code}" https://docs.internal/   # expect 200

# Verify ADR-A-007 edge case
curl -s -o /dev/null -w "%{http_code}" \
  "https://docs.internal/adr/ADR-A-007-media-sync-syncthing/"  # expect 200 not 404

# Verify search index
curl -s https://docs.internal/search/search_index.json \
  | python3 -m json.tool | grep -c '"location"'  # expect >20 entries
```

#### D-MKD exit gate

- [ ] `mkdocs` container Up (healthy), `cap_drop:[ALL]`, `read_only:true`, port 8089.
- [ ] `https://docs.internal/` → 200 via Caddy.
- [ ] ADR-A-007-media-sync-syncthing renders at its URL (not 404).
- [ ] Search index has >20 entries.
- [ ] `mkdocs.yml`, `docs/index.md`, `docker/mkdocs/docker-compose.yml` committed.
- [ ] Caddy route committed.

**Commit:** `feat(phase-14-D-MKD): MkDocs Material — internal docs at docs.internal`

#### Window 2 regression probe

Run after both D-STR and D-MKD are deployed and their exit gates pass:

```bash
bash docs/phase-13/h1-regression-probe.sh d-str-d-mkd-final | \
    tee docs/phase-14/D_STR_D_MKD_REGRESSION_2026-04-30.log
# Pass: FAIL=0, WARN≤3
```

**Commit:** `docs(phase-14): Window 2 regression — D-STR + D-MKD`

---

## Window 3 — D-ZBX + D-RST

**Estimate:** D-ZBX 2–4h + D-RST 5–8h = 7–12h combined.
**D-RST requires operator presence** (interactive Vault auth, actual restore to disk).
Gate D-ZBX first; it is fully automated. Then run D-RST.

### D-ZBX — Zabbix Prometheus exporter

**Purpose:** Zabbix 7.4 has no `/metrics` endpoint. An exporter reads the Zabbix
API and translates triggers/alerts/host status to Prometheus, enabling Grafana
dashboards for monitoring-layer health.

**Port:** 9224 (exporter).

**Zabbix admin credentials are already in Vault** at `secret/zabbix/admin:password`.
The exporter needs a Zabbix API token (not the admin password directly).

#### Step 1 — Image selection

```bash
# Pull candidates; pick the one with most recent layers and Zabbix 7.x API support
docker pull mbobov/zabbix-exporter:latest
docker pull zabbix/zabbix-exporter:latest   # if exists
docker pull ghcr.io/prometheus-community/zabbix-exporter:latest  # if exists

# Check layer dates
docker inspect mbobov/zabbix-exporter:latest \
  --format '{{.Metadata.LastTagTime}}'

# Confirm API compatibility — most exporters target Zabbix API 6.x; verify 7.x works
# If no good image: use the Zabbix API directly in a simple Python prometheus_client
# script as a fallback (see Step 1b below)
```

**Step 1b — Fallback: minimal Python exporter** (if no maintained image found):

```python
# docker/zabbix-exporter/exporter.py
#!/usr/bin/env python3
"""Minimal Zabbix Prometheus exporter using python prometheus_client."""
import os, time, requests
from prometheus_client import start_http_server, Gauge

ZABBIX_URL  = os.environ["ZABBIX_URL"]
ZABBIX_TOKEN = os.environ["ZABBIX_API_TOKEN"]

g_triggers = Gauge("zabbix_triggers_active", "Active triggers", ["severity"])
g_hosts    = Gauge("zabbix_hosts_available", "Hosts available", ["status"])

def collect():
    headers = {"Authorization": f"Bearer {ZABBIX_TOKEN}",
               "Content-Type": "application/json"}
    r = requests.post(f"{ZABBIX_URL}/api_jsonrpc.php", json={
        "jsonrpc": "2.0", "method": "trigger.get",
        "params": {"only_true": 1, "selectHosts": ["host"],
                   "output": ["triggerid","description","priority","value"]},
        "id": 1
    }, headers=headers, timeout=10)
    for t in r.json().get("result", []):
        g_triggers.labels(severity=t["priority"]).inc()

if __name__ == "__main__":
    start_http_server(9224)
    while True:
        g_triggers.clear()
        g_hosts.clear()
        collect()
        time.sleep(60)
```

Use this only if no maintained exporter image is found. Package it in a minimal
`python:3.12-alpine` image. Either path works — pick the one that runs.

#### Step 2 — Mint a Zabbix API token

The exporter needs a read-only API token. The Zabbix admin password is at
`secret/zabbix/admin:password`. Use it once to mint a token, then store the
token in Vault.

```bash
# Source admin password from Vault (hash-only log — never print value)
ZBX_ADMIN_PASS=$(vault kv get -field=password secret/zabbix/admin)
echo "Admin pass hash: $(echo -n "$ZBX_ADMIN_PASS" | sha256sum | cut -c1-12)"

# Mint API token via Zabbix API
TOKEN_RESP=$(curl -s -X POST "http://localhost:10080/api_jsonrpc.php" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"user.login\",
       \"params\":{\"username\":\"Admin\",\"password\":\"$ZBX_ADMIN_PASS\"},
       \"id\":1}")
unset ZBX_ADMIN_PASS

SESSION_TOKEN=$(echo "$TOKEN_RESP" | python3 -c \
  "import json,sys; print(json.load(sys.stdin)['result'])")
echo "Session token hash: $(echo -n "$SESSION_TOKEN" | sha256sum | cut -c1-12)"

# Create a named API token (permanent, read-only)
API_TOKEN_RESP=$(curl -s -X POST "http://localhost:10080/api_jsonrpc.php" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -d '{"jsonrpc":"2.0","method":"token.create",
       "params":{"name":"prometheus-exporter","userid":"1","expires_at":0},
       "id":2}')
TOKEN_ID=$(echo "$API_TOKEN_RESP" | python3 -c \
  "import json,sys; print(json.load(sys.stdin)['result']['tokenid'])")

GENERATED_TOKEN=$(curl -s -X POST "http://localhost:10080/api_jsonrpc.php" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"token.generate\",
       \"params\":[\"$TOKEN_ID\"],\"id\":3}" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['result'][0]['token'])")
unset SESSION_TOKEN

echo "API token hash: $(echo -n "$GENERATED_TOKEN" | sha256sum | cut -c1-12)"

# Write to Vault
vault kv put secret/zabbix/exporter api_token="$GENERATED_TOKEN"
echo "Vault read-back hash: $(vault kv get -field=api_token secret/zabbix/exporter | sha256sum | cut -c1-12)"
unset GENERATED_TOKEN API_TOKEN_RESP TOKEN_RESP
```

#### Step 3 — Vault policy + AppRole

Create `config/vault-policies/zabbix-exporter-policy.hcl`:

```hcl
path "secret/data/zabbix/exporter"    { capabilities = ["read"] }
path "secret/metadata/zabbix/exporter" { capabilities = ["list", "read"] }
```

```bash
vault policy write zabbix-exporter \
  config/vault-policies/zabbix-exporter-policy.hcl
vault write auth/approle/role/zabbix-exporter \
  policies=zabbix-exporter \
  secret_id_ttl=0 token_ttl=1h token_max_ttl=24h token_num_uses=0

mkdir -p ~/.vault-approle/zabbix-exporter
vault read -field=role_id auth/approle/role/zabbix-exporter/role-id \
  > ~/.vault-approle/zabbix-exporter/role_id
vault write -f -field=secret_id auth/approle/role/zabbix-exporter/secret-id \
  > ~/.vault-approle/zabbix-exporter/secret_id
```

#### Step 4 — Vault Agent sidecar

Create `docker/zabbix-exporter/vault-agent/agent.hcl`:

```hcl
vault { address = "http://vault-server:8200" }
auto_auth {
  method "approle" {
    config {
      role_id_file_path   = "/vault/approle/role_id"
      secret_id_file_path = "/vault/approle/secret_id"
    }
  }
  sink "file" { config { path = "/vault/secrets/.token" } }
}
template {
  source      = "/vault/agent-config/credentials.env.tmpl"
  destination = "/vault/secrets/credentials.env"
}
exit_after_auth = true
```

Create `docker/zabbix-exporter/vault-agent/credentials.env.tmpl`:

```
{{ with secret "secret/data/zabbix/exporter" -}}
ZABBIX_API_TOKEN={{ .Data.data.api_token }}
{{- end }}
ZABBIX_URL=http://zabbix-web:8080
```

#### Step 5 — Compose file

Create `docker/zabbix-exporter/docker-compose.yml`:

```yaml
services:
  vault-agent-zabbix-exporter:
    image: hashicorp/vault:1.15
    container_name: vault-agent-zabbix-exporter
    restart: "no"
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    volumes:
      - ./vault-agent/agent.hcl:/vault/config/agent.hcl:ro
      - ./vault-agent/credentials.env.tmpl:/vault/agent-config/credentials.env.tmpl:ro
      - /Users/admin/.vault-approle/zabbix-exporter:/vault/approle:ro
      - zabbix-exporter-secrets:/vault/secrets
    command: ["vault", "agent", "-config=/vault/config/agent.hcl"]
    networks: [zabbix-net]

  zabbix-exporter:
    image: <chosen-image>@<digest>
    container_name: zabbix-exporter
    restart: unless-stopped
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 128m
    ports:
      - "127.0.0.1:9224:9224"
    env_file:
      - /Users/admin/.vault-agent-secrets/zabbix-exporter/credentials.env
    depends_on:
      vault-agent-zabbix-exporter:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9224/metrics || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3
    networks: [zabbix-net]

volumes:
  zabbix-exporter-secrets:
    driver: local
    driver_opts: {type: tmpfs, device: tmpfs, o: "size=1m,mode=0700"}

networks:
  zabbix-net:
    external: true   # shares network with the zabbix stack
    name: zabbix_default  # confirm with: docker network ls | grep zabbix
```

Note: confirm the Zabbix stack network name with `docker network ls | grep zabbix`
before deploying. Adjust `name:` if it differs from `zabbix_default`.

#### Step 6 — Grafana dashboard

Add scrape target to VictoriaMetrics/Prometheus config, then create a dashboard.
Add `docker/grafana/dashboards/zabbix-overview.json` with panels:
- Active triggers by severity over time
- Hosts available/unavailable count
- Problem count 24h trend

If VictoriaMetrics scrape config is a file-based SD, add:

```yaml
# In vmagent scrape config (check docker/vmagent/ or docker/observability/)
- job_name: zabbix-exporter
  static_configs:
    - targets: ['zabbix-exporter:9224']
```

#### Step 7 — Validate

```bash
docker compose -f docker/zabbix-exporter/docker-compose.yml up -d
docker ps | grep zabbix-exporter   # Up ... (healthy)
curl -s http://localhost:9224/metrics | grep "^zabbix_" | head -10
# Must return metric lines — if empty, check ZABBIX_API_TOKEN rendered correctly:
docker exec zabbix-exporter env | grep ZABBIX_API_TOKEN | sha256sum | cut -c1-12
# Hash must be non-trivial (not empty string hash)
```

Update CLAUDE.md: mark Zabbix Prometheus exporter "Known Hardening Trade-offs"
entry as RESOLVED.

#### D-ZBX exit gate

- [ ] `zabbix-exporter` container Up (healthy), `cap_drop:[ALL]`, credentials from Vault sidecar.
- [ ] `/metrics` endpoint returns `zabbix_`-prefixed metric lines.
- [ ] Grafana dashboard renders (trigger counts visible).
- [ ] `config/vault-policies/zabbix-exporter-policy.hcl` committed.
- [ ] CLAUDE.md trade-off entry updated.
- [ ] Credentials never displayed in terminal or committed.

**Commit:** `feat(phase-14-D-ZBX): Zabbix Prometheus exporter + Grafana dashboard`

---

### D-RST — Restic backup runbook + quarterly restore test

**Operator presence required.** This block runs an actual restore to disk. If the
restore fails, **stop immediately** (R-CRITICAL per risk register R-P14-7). Do not
continue to Window 4 until backup integrity is confirmed.

**Estimate:** 5–8h including actual restore time.

#### Step 1 — Locate Restic credentials in Vault

```bash
# Find the backup secret path
vault kv list secret/ 2>/dev/null
# Look for: backup, restic, backups

# Read repository and password (hash-only — never print)
RESTIC_REPOSITORY=$(vault kv get -field=repository secret/backup 2>/dev/null || \
                    vault kv get -field=repository secret/restic 2>/dev/null)
RESTIC_PASSWORD=$(vault kv get -field=password secret/backup 2>/dev/null || \
                  vault kv get -field=password secret/restic 2>/dev/null)

echo "Repo path hash:    $(echo -n "$RESTIC_REPOSITORY" | sha256sum | cut -c1-12)"
echo "Password hash:     $(echo -n "$RESTIC_PASSWORD" | sha256sum | cut -c1-12)"
# If both hashes are non-trivial, credentials loaded correctly
```

#### Step 2 — List snapshots and check repo health

```bash
restic snapshots
# Record: total snapshot count, latest snapshot ID and date

restic check --read-data-subset=5%
# 5% sample integrity check. If this fails: R-CRITICAL. Stop. Surface to operator.
# Do NOT proceed to restore test if check fails.
```

#### Step 3 — Run restore test

```bash
LATEST_ID=$(restic snapshots --json \
  | python3 -c "import json,sys; s=json.load(sys.stdin); print(s[-1]['id'])")
echo "Restoring snapshot: $LATEST_ID"

RESTORE_DIR=$(mktemp -d /tmp/restic-restore-XXXXXX)
echo "Restore target: $RESTORE_DIR"

# Restore Vault data only (scoped restore — not full snapshot)
restic restore "$LATEST_ID" \
  --target "$RESTORE_DIR" \
  --include /vault/data

# Verify restore
echo "Restored size: $(du -sh "$RESTORE_DIR" | cut -f1)"
ls -la "$RESTORE_DIR/vault/data/" | head -20
file "$RESTORE_DIR/vault/data/"* | head -5

# Cleanup
rm -rf "$RESTORE_DIR"
unset RESTIC_REPOSITORY RESTIC_PASSWORD LATEST_ID
```

Expected: Vault data files present in restored directory, non-zero sizes, no
corruption errors. Document the snapshot ID and restored byte count.

#### Step 4 — Author `docs/runbooks/backup-restore.md`

Full general restore runbook (Vault data + any service's data). Must include:

1. How to source Restic credentials from Vault (not from a file on disk).
2. `restic snapshots` to identify target.
3. `restic check` before any restore.
4. `restic restore <id> --target <dir> --include <path>` with scope guidance.
5. Post-restore verification checklist per service class (Vault: re-unseal;
   databases: pg_restore if needed; files: verify checksums).
6. Quarterly test cadence reminder — run this block annually; add a calendar reminder.

#### Step 5 — Commit restore test evidence

Create `docs/runbooks/backup-restore-test-2026-04.md`:

```markdown
# Restic Restore Test — 2026-04

**Date:** 2026-04-30
**Operator:** (operator name)
**Snapshot tested:** <snapshot-id>
**Snapshot date:** <snapshot-date>

## restic check result
[paste summary — no credential values]

## Restore result
- Target: /tmp/restic-restore-<id>/ (deleted after verification)
- Scope: /vault/data
- Restored size: <size>
- Files verified: (list first 5 files from ls output)
- Corruption errors: none

## Result: PASS
Next quarterly test due: 2026-07-30
```

#### D-RST exit gate

- [ ] `restic check` passed (repo healthy).
- [ ] Restore test completed; Vault data files present and non-empty in restored dir.
- [ ] `docs/runbooks/backup-restore.md` committed (full procedure).
- [ ] `docs/runbooks/backup-restore-test-2026-04.md` committed (evidence, no credential values).
- [ ] `mkdocs.yml` nav updated to include `backup-restore.md` (add to Runbooks section).

**Commit:** `docs(phase-14-D-RST): Restic restore runbook + 2026-04 quarterly restore test`

#### Window 3 regression probe

```bash
bash docs/phase-13/h1-regression-probe.sh d-zbx-d-rst-final | \
    tee docs/phase-14/D_ZBX_D_RST_REGRESSION_2026-04-30.log
# Pass: FAIL=0, WARN≤3
```

**Commit:** `docs(phase-14): Window 3 regression — D-ZBX + D-RST`

---

## Window 4 — D-LOG: Loki + Promtail

**Estimate:** 6–10h. **Gate:** Full IV&V (A-011). Novel log-shipping infra —
first Loki deployment. High discovery budget (3–5). Budget a full session.

**Purpose:** Caddy 2.11.2 has no `host` label on Prometheus metrics. Per-site
analysis requires tailing the JSON access log. Loki + Promtail ships those logs
to a queryable store, closing the CLAUDE.md "Known Hardening Trade-offs" entry.

**Ports:** 3100 (Loki HTTP), 9096 (Loki gRPC), 9080 (Promtail).

**Known capability requirement:** Promtail needs `DAC_READ_SEARCH` to read
`/var/log/caddy/access.log`. This is documented as D#31 — minimal, read-only,
justified by the log-shipping workload.

#### Step 1 — Pre-deploy audit

```bash
ss -tlnp | grep -E "3100|9096|9080"  # must all be empty

# Confirm Caddy access log exists and is JSON format
tail -3 /var/log/caddy/access.log | python3 -m json.tool | head -10
# Expect JSON with fields: ts, request.host, status, duration, etc.
# If not JSON: check Caddyfile access_log snippet format

# Check VictoriaMetrics/vmagent scrape config location
ls docker/vmagent/ docker/observability/ 2>/dev/null | head -10
```

#### Step 2 — Loki config

Create `docker/loki/loki-config.yaml`:

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096
  log_level: warn

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 5m
  chunk_retain_period: 30s
  max_transfer_retries: 0

schema_config:
  configs:
    - from: "2024-01-01"
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  ingestion_rate_mb: 4
  ingestion_burst_size_mb: 6

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
```

#### Step 3 — Promtail config

Create `docker/loki/promtail-config.yaml`:

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: caddy-access
    static_configs:
      - targets: [localhost]
        labels:
          job: caddy
          platform: mac-mini
          __path__: /var/log/caddy/access.log
    pipeline_stages:
      - json:
          expressions:
            log_ts:      ts
            req_host:    request.host
            req_method:  request.method
            req_uri:     request.uri
            resp_status: status
            duration:    duration
            remote_ip:   request.remote_ip
      - labels:
          req_host:
          resp_status:
          req_method:
      - timestamp:
          source: log_ts
          format: Unix
```

#### Step 4 — Compose file

Create `docker/loki/docker-compose.yml`:

```yaml
services:
  loki:
    image: grafana/loki:2.9.0
    container_name: loki
    restart: unless-stopped
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 512m
    ports:
      - "127.0.0.1:3100:3100"
    volumes:
      - ./loki-config.yaml:/etc/loki/loki-config.yaml:ro
      - loki-data:/loki
    command: ["-config.file=/etc/loki/loki-config.yaml"]
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://localhost:3100/ready || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 10
      start_period: 30s

  promtail:
    image: grafana/promtail:2.9.0
    container_name: promtail
    restart: unless-stopped
    cap_drop: [ALL]
    cap_add: [DAC_READ_SEARCH]   # D#31: required to read /var/log/caddy/access.log
    security_opt: [no-new-privileges:true]
    mem_limit: 128m
    volumes:
      - ./promtail-config.yaml:/etc/promtail/promtail-config.yaml:ro
      - /var/log/caddy:/var/log/caddy:ro
      - promtail-positions:/tmp
    command: ["-config.file=/etc/promtail/promtail-config.yaml"]
    depends_on:
      loki:
        condition: service_healthy

volumes:
  loki-data:
  promtail-positions:
```

#### Step 5 — Caddy route (optional — only if direct Loki query needed externally)

Grafana reaches Loki container-to-container. Only add this route if you want
to query the Loki API from a browser or the regression probe:

```caddyfile
loki.internal {
    import access_log
    reverse_proxy loki:3100
}
```

#### Step 6 — Grafana Loki data source

Create `docker/grafana/provisioning/datasources/loki.yaml`:

```yaml
apiVersion: 1
datasources:
  - name: Loki
    type: loki
    url: http://loki:3100
    access: proxy
    isDefault: false
    version: 1
    editable: false
```

Restart Grafana after adding the provisioning file:
`docker compose -f docker/grafana/docker-compose.yml restart grafana-obs`

#### Step 7 — Per-site Grafana dashboard

Create `docker/grafana/dashboards/caddy-per-site.json` with panels:

1. **Request rate by host** (LogQL):
   `sum by (req_host) (rate({job="caddy"}[5m]))`

2. **HTTP error rate by host** (4xx+5xx):
   `sum by (req_host) (rate({job="caddy", resp_status=~"[45].."}[5m]))`

3. **Top 10 hosts by volume** (24h):
   `topk(10, sum by (req_host) (count_over_time({job="caddy"}[24h])))`

4. **Log stream** (raw Caddy logs for selected host):
   `{job="caddy", req_host="$host"}` — with a `$host` variable dropdown.

Use the Grafana dashboard JSON provisioning format. Commit the file.

#### Step 8 — Deploy and validate

```bash
docker compose -f docker/loki/docker-compose.yml up -d

# Wait for Loki to be ready
for i in $(seq 1 20); do
    curl -s http://localhost:3100/ready | grep -q "ready" && break
    sleep 3; echo -n "."
done
echo ""

# Wait for Promtail to ship some logs (30-60s after deploy)
sleep 60
docker logs promtail --tail=20 2>&1 | grep -E "Sent\|error\|level=info"

# Query Loki for Caddy entries
curl -sG 'http://localhost:3100/loki/api/v1/query_range' \
  --data-urlencode 'query={job="caddy"}' \
  --data-urlencode 'limit=5' \
  --data-urlencode "start=$(date -v-1H +%s)000000000" \
  | python3 -m json.tool | grep -c '"values"'
# Must be >0 — confirms log ingestion working

# Verify Grafana data source
# Open https://grafana.internal/ → Connections → Data Sources → Loki → Test
```

#### Step 9 — Update CLAUDE.md

Mark "Caddy per-site access logs" in "Known Hardening Trade-offs" as RESOLVED:

> RESOLVED (Phase 14 D-LOG): Loki + Promtail deployed. Promtail tails
> `/var/log/caddy/access.log` (JSON format); `req_host` label enables per-site
> analysis. Grafana `caddy-per-site` dashboard at grafana.internal.
> Promtail uses `cap_add: [DAC_READ_SEARCH]` — documented exception (D#31),
> minimal for read-only log shipping.

#### D-LOG exit gate

- [ ] `loki` container Up (healthy), `cap_drop:[ALL]`, port 3100.
- [ ] `promtail` container Up, `cap_drop:[ALL]`, `cap_add:[DAC_READ_SEARCH]` (D#31 documented).
- [ ] Loki query returns ≥1 Caddy log entry (confirms ingestion pipeline works).
- [ ] Grafana Loki data source test passes.
- [ ] `caddy-per-site` dashboard provisioned; request-rate panel shows data.
- [ ] CLAUDE.md "Known Hardening Trade-offs" updated.
- [ ] All config files committed.

**Commit:** `feat(phase-14-D-LOG): Loki + Promtail — per-site Caddy log analysis`

#### Window 4 regression probe

```bash
bash docs/phase-13/h1-regression-probe.sh d-log-final | \
    tee docs/phase-14/D_LOG_REGRESSION_2026-04-30.log
# Pass: FAIL=0, WARN≤3
```

**Commit:** `docs(phase-14): Window 4 regression — D-LOG`

---

## Window 5 — D-XINDEX: Cross-index extension

**Estimate:** 4–8h. **Gate:** Full IV&V (A-011) + A-012 (harness).

### Phase 13 Block 4.E status check — do this first

```bash
# Is Block 4.E closed? (InvenTree cross-reference + NetBox)
ls docs/phase-13/ | grep -iE "INCREMENT_[3-9]|INCREMENT_1[0-9]" | sort
grep -l "4\.E\|XINDEX\|cross.index" docs/phase-13/PHASE_13_INCREMENT_*CLOSEOUT*.md \
  2>/dev/null | head -3
```

- **If 4.E is closed:** use its cross-index (NetBox→InvenTree→Plane) as the
  baseline for this block.
- **If 4.E is still open** (Mouser+DigiKey+CSV not yet landed): proceed standalone
  using the Increment 2A baseline (NetBox+Plane only, no InvenTree component links).
  Do not wait for 4.E — this block is independent enough to run now.

### Purpose

Provides a machine-readable validator that ADRs are tracked in Plane and that key
Vault secret paths are covered by a corresponding ADR. Adds probe section (g) to
the regression probe.

### Step 1 — Audit current cross-index state

```bash
# ADRs in DECISION_REGISTER.md
grep -c "ADR-A-" docs/DECISION_REGISTER.md
grep "ADR-A-" docs/DECISION_REGISTER.md

# Plane issues with external_id (ADR tracking issues)
python3 - <<'EOF'
from framework.plane_connector import PlaneAPI, RateLimitError
api = PlaneAPI()
issues = api.list_all_issues()
adr_issues = {i["external_id"]: i for i in issues
              if (i.get("external_id") or "").startswith("ADR-")}
print(f"Total Plane issues: {len(issues)}")
print(f"Issues with ADR external_id: {len(adr_issues)}")
for k, v in sorted(adr_issues.items()):
    print(f"  {k} → #{v.get('sequence_id','?')} {v['name'][:50]}")
EOF
```

### Step 2 — Author `scripts/cross-index-validate.py`

```python
#!/usr/bin/env python3
"""
Cross-index validator: ADR <-> Plane coherence check.
Read-only. Emits gap report and exits 0 (no gaps) or 1 (gaps found).

Usage:
    python3 scripts/cross-index-validate.py [--json] [--verbose]
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT          = Path(__file__).parent.parent
DECISION_REGISTER  = REPO_ROOT / "docs" / "DECISION_REGISTER.md"


def load_adrs() -> list[dict]:
    adrs = []
    for line in DECISION_REGISTER.read_text().splitlines():
        m = re.match(r"\|\s*\[?(ADR-A-\d+)\]?.*?\|\s*(.+?)\s*\|\s*(\w+)\s*\|",
                     line)
        if m:
            adrs.append({
                "id":     m.group(1).strip(),
                "title":  m.group(2).strip(),
                "status": m.group(3).strip(),
            })
    return adrs


def load_plane_adr_issues() -> dict[str, dict]:
    from framework.plane_connector import PlaneAPI, RateLimitError
    api = PlaneAPI()
    try:
        issues = api.list_all_issues()
    except RateLimitError as exc:
        print(f"RATE-LIMIT: {exc}", file=sys.stderr)
        sys.exit(1)
    return {i["external_id"]: i
            for i in issues
            if (i.get("external_id") or "").startswith("ADR-")}


def main() -> int:
    adrs            = load_adrs()
    plane_adr_issues = load_plane_adr_issues()

    gaps, covered = [], []
    for adr in adrs:
        if adr["status"].lower() not in ("accepted", "superseded"):
            continue   # skip deprecated / draft
        if adr["id"] in plane_adr_issues:
            covered.append(adr["id"])
        else:
            gaps.append(adr)

    report = {
        "adrs_checked":             len(adrs),
        "adrs_covered_in_plane":    len(covered),
        "adrs_missing_plane_issue": len(gaps),
        "gaps":    gaps,
        "covered": covered,
    }

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        print(f"ADRs checked:         {report['adrs_checked']}")
        print(f"Tracked in Plane:     {report['adrs_covered_in_plane']}")
        print(f"Missing Plane issue:  {report['adrs_missing_plane_issue']}")
        if "--verbose" in sys.argv or gaps:
            for g in gaps:
                print(f"  GAP: {g['id']} ({g['status']}) — {g['title']}")

    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())
```

### Step 3 — Run validator and review gaps

```bash
python3 scripts/cross-index-validate.py --verbose
# Review gap list — for each ADR without a Plane issue, create a stub
```

### Step 4 — Create stub Plane issues for untracked ADRs

Use folded gates (A-013): first issue is FULL IV&V (first-batch-verify); rest are
folded after pattern is proved.

```python
from framework.plane_connector import PlaneAPI, RateLimitError
import time, sys, json

api = PlaneAPI()

# Paste actual gaps from Step 3 — do not hardcode without verifying
GAPS = [
    {"id": "ADR-A-001", "title": "Retain the existing control plane", "status": "Accepted"},
    # ... rest from validator output
]

first_verified = False
for i, adr in enumerate(GAPS):
    try:
        issue, created = api.upsert_issue(
            external_id  = adr["id"],
            title        = f"[{adr['id']}] {adr['title']}",
            description  = (f"Architecture decision tracking issue for {adr['id']}.\n\n"
                            f"Status: {adr['status']}\n"
                            f"See: docs/adr/ in the platform repo."),
            state_name   = "Accepted",
            category     = "Architecture",
            priority     = "low",
        )
        if i == 0 and created:
            # First-batch verify (canonical-pattern §4)
            if not api.verify_issue_field(issue["id"], "labels", []):
                print("ABORT: first-batch-verify failed", file=sys.stderr)
                sys.exit(2)
            first_verified = True
            print(f"  VERIFIED: {adr['id']} → {issue['id']}")
        status = "CREATED" if created else "EXISTS"
        print(f"  {status}: {adr['id']} → #{issue.get('sequence_id','?')}")
        time.sleep(1.5)
    except RateLimitError as exc:
        print(f"  RATE-LIMIT — sleeping 60s", file=sys.stderr)
        time.sleep(60)
```

### Step 5 — Add probe section (g) to regression probe

Append to `docs/phase-13/h1-regression-probe.sh` (find the final summary block
and insert before it):

```bash
# (g) Cross-index coherence (ADR → Plane tracking)
echo ""
echo "(g) Cross-index coherence (ADR → Plane)"
if python3 scripts/cross-index-validate.py > /dev/null 2>&1; then
    echo "  ✅ all accepted ADRs have Plane tracking issues"
    PASS=$((PASS + 1))
else
    GAPS=$(python3 scripts/cross-index-validate.py --json 2>/dev/null \
           | python3 -c "import json,sys; d=json.load(sys.stdin); \
             print(d['adrs_missing_plane_issue'])" 2>/dev/null || echo "?")
    echo "  ⚠️  cross-index gaps: $GAPS ADRs without Plane issue"
    WARN=$((WARN + 1))
fi
```

### Step 6 — Re-run validator and probe to confirm

```bash
python3 scripts/cross-index-validate.py --verbose
# Must exit 0 — all accepted ADRs now have Plane issues

bash docs/phase-13/h1-regression-probe.sh d-xindex-final | \
    tee docs/phase-14/D_XINDEX_REGRESSION_2026-04-30.log
# Expect: section (g) now contributes a PASS
# Total should be PASS=16 FAIL=0 WARN≤3
```

### D-XINDEX exit gate

- [ ] `scripts/cross-index-validate.py` committed; exits 0.
- [ ] All accepted ADRs have Plane tracking issues (verify with `--verbose`).
- [ ] Probe section (g) added to `h1-regression-probe.sh`; committed.
- [ ] Probe run `d-xindex-final`: FAIL=0, WARN≤3, PASS=16.
- [ ] Log committed to `docs/phase-14/D_XINDEX_REGRESSION_2026-04-30.log`.

**Commits:**
- `feat(phase-14-D-XINDEX): cross-index validator + stub Plane issues for ADRs`
- `feat(phase-14-D-XINDEX): regression probe section (g) — ADR→Plane coherence`

---

## Window 6 — CL-14: Phase 14 closeout

**Estimate:** 2–3h. Do not start until all prior blocks are closed and their
regression logs committed.

### Pre-closeout checklist — verify every block before final probe

```bash
# 1. All containers running
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E \
  "structurizr|mkdocs|loki|promtail|zabbix-exporter"
# All must show: Up ... (healthy)

# 2. All Caddy routes serving
for host in structurizr.internal docs.internal; do
    code=$(curl -s -o /dev/null -w "%{http_code}" "https://$host/")
    echo "$host → HTTP $code"
done
# All must be 200

# 3. Loki ingesting
curl -sG 'http://localhost:3100/loki/api/v1/query_range' \
  --data-urlencode 'query={job="caddy"}' \
  --data-urlencode 'limit=1' \
  | python3 -m json.tool | grep -c '"values"'
# Must be >0

# 4. Cross-index validator
python3 scripts/cross-index-validate.py
# Must exit 0

# 5. Restic repo still healthy
export RESTIC_REPOSITORY=$(vault kv get -field=repository secret/backup 2>/dev/null || \
                           vault kv get -field=repository secret/restic 2>/dev/null)
export RESTIC_PASSWORD=$(vault kv get -field=password secret/backup 2>/dev/null || \
                         vault kv get -field=password secret/restic 2>/dev/null)
restic check --read-data-subset=1%
unset RESTIC_REPOSITORY RESTIC_PASSWORD

# 6. Plane curation complete
python3 - <<'EOF'
from framework.plane_connector import PlaneAPI
api = PlaneAPI()
issues = api.list_all_issues()
labeled = [i for i in issues if i.get("labels")]
urgent  = [i for i in issues if i.get("priority") == "urgent"]
coverage = len(labeled) / len(issues) * 100 if issues else 0
print(f"Label coverage: {coverage:.1f}% ({len(labeled)}/{len(issues)})")
print(f"Urgent remaining: {len(urgent)}")
# Coverage must be ≥95%, urgent must be ≤10
EOF

# 7. No plaintext credentials anywhere
grep -rn "Admin1234" ~/.claude/ docs/ 2>/dev/null | grep -v ".git"
# Must return nothing
grep -rn "Admin1234\|api_key.*=.*[a-f0-9]{32}" docs/ 2>/dev/null
# Must return nothing
```

### A-012 equivalence harness re-runs

Per ADR-A-012: verify all Phase 14 migrations at closeout.

```bash
# 1. CMDB_SOURCE flip (commit 60aeb96)
python3 scripts/cmdb_source.py 2>&1 | head -3
# Must show NetBox-sourced output (not "using yaml fallback")

# 2. Plane admin rotation (NF-14-1, from D-DOC addendum)
# Hash must match what was recorded in the addendum commit 3a15faa
vault kv get -field=password secret/plane/admin | sha256sum | cut -c1-12
# Compare against hash in docs/phase-14/PHASE_14_BLOCK_D_DOC_CLOSEOUT_2026-04-29.md

# 3. plex-mcp sidecar (commit b2b089b)
docker exec plex-mcp env 2>/dev/null | grep "PLEX_TOKEN" | \
  sha256sum | cut -c1-12
# Non-trivial hash confirms credential present in container env

# 4. zabbix-exporter credentials from Vault
docker exec zabbix-exporter env 2>/dev/null | grep "ZABBIX_API_TOKEN" | \
  sha256sum | cut -c1-12
# Non-trivial hash confirms credential present
```

### Final regression probe

```bash
bash docs/phase-13/h1-regression-probe.sh phase-14-final | \
    tee docs/phase-14/PHASE_14_FINAL_REGRESSION_2026-04-30.log
```

**Expected result:** PASS=16 FAIL=0 WARN≤3.
- PASS=16 because D-XINDEX probe section (g) adds 1 to the baseline of 15.
- If PASS=15 (section g not yet contributing): check probe script for the (g) block.
- If FAIL≥1: **stop**. Do not tag. Surface for operator decision.

### Closeout doc

Commit `docs/phase-14/PHASE_14_CLOSEOUT_2026-04-30.md` with these sections:

```markdown
# Phase 14 Closeout

**Date:** 2026-04-30
**Gate:** phase-14-final PASS=16 FAIL=0 WARN≤3
**HEAD at close:** <commit hash>

## Block status

| Block | Status | Key commits | Gate result |
|---|---|---|---|
| D-DOC | ✅ CLOSED (+ addendum) | a6d50c2, 3a15faa | PASS=15 |
| Plane curation | ✅ CLOSED | <commit> | sub-task, no new probe |
| D-STR | ✅ CLOSED | <commit> | Window 2 probe PASS=15 |
| D-MKD | ✅ CLOSED | <commit> | Window 2 probe PASS=15 |
| D-ZBX | ✅ CLOSED | <commit> | Window 3 probe PASS=15 |
| D-RST | ✅ CLOSED | <commit> | Window 3 probe PASS=15 |
| D-LOG | ✅ CLOSED | <commit> | Window 4 probe PASS=15 |
| D-XINDEX | ✅ CLOSED | <commit> | probe PASS=16 |
| CL-14 | ✅ CLOSED | this doc | PASS=16 FAIL=0 WARN≤3 |

## Discoveries (continuing from #30)

[List any discoveries found during Windows 2–6, numbered from #31]

## A-012 equivalence harness results

| Migration | Vault read-back hash | Match |
|---|---|---|
| CMDB_SOURCE flip | n/a (env var) | ✅ NetBox output confirmed |
| Plane admin rotation | <12-char hash> | ✅ matches addendum record |
| plex-mcp PLEX_TOKEN | <12-char hash> | ✅ non-trivial (credential present) |
| zabbix-exporter API token | <12-char hash> | ✅ non-trivial |

## Items deferred to Phase 15+

1. Uptime Kuma homepage slug gap (pre-existing; cosmetic).
2. mcp-docs-remote pre-built image (KI-004; reduces cold-start from 60s to <5s).
3. sms1obot-mcp-server* container hardening (Obot-managed; documented as permanent KI).
4. Phase 13 Increments 2B–7 (gated on Mouser+DigiKey+CSV; parallel, not blocked).

## CLAUDE.md updates this phase

- Known Hardening Trade-offs: Caddy per-site logs RESOLVED (D-LOG).
- Known Hardening Trade-offs: Zabbix Prometheus exporter RESOLVED (D-ZBX).
- Current Phase: Phase 14 CLOSED.
```

### Git tag

```bash
git tag phase-14-final
git log --oneline -3
# Confirm tag is on the closeout-doc commit
```

### CLAUDE.md final update

Update the `Current Phase` line:

```
**Current Phase:** Phase 14 CLOSED (2026-04-30). Phase 13 Increments 2B–7
in progress (gated on Mouser+DigiKey+CSV). Phase 15 not yet scoped.
```

### CL-14 exit gate

- [ ] All blocks closed (Plane curation, D-STR, D-MKD, D-ZBX, D-RST, D-LOG, D-XINDEX).
- [ ] Pre-closeout checklist passed (all containers healthy, all routes 200, Loki ingesting, validator exits 0).
- [ ] A-012 harness: all four migrations verified by hash.
- [ ] Final probe: PASS=16 FAIL=0 WARN≤3. Log committed.
- [ ] `docs/phase-14/PHASE_14_CLOSEOUT_2026-04-30.md` committed.
- [ ] `git tag phase-14-final` applied.
- [ ] CLAUDE.md "Current Phase" updated.
- [ ] No credential values in any tracked file or terminal output.

**Commits:**
- `docs(phase-14): PHASE_14_FINAL_REGRESSION_2026-04-30.log`
- `docs(phase-14): CL-14 — Phase 14 CLOSED`

---

## Hard stops — non-negotiable

| Condition | Action |
|---|---|
| Any regression gate FAIL≥1 | Stop. Do not proceed to next window. Surface to operator. |
| D-RST: `restic check` fails | R-CRITICAL. Stop all work. Backup integrity unknown. |
| D-RST: restore test shows empty or corrupt files | R-CRITICAL. Surface immediately. |
| Plane curation: first-batch-verify fails | Abort bulk writes. Do not proceed. |
| Any container fails to start after hardening change | Roll back the compose change. Investigate. |
| `--no-verify` on any commit | Never permitted. |
| Credential value in any output, log, or commit | Stop. Hash-only always. |

---

## Commit message template

```
feat(phase-14-<BLOCK>): <summary>

<Discoveries if any, numbered from #31>
Gate: <probe-id> PASS=N FAIL=0 WARN=N

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

---

## Summary

| Window | Blocks | Estimate | Notes |
|---|---|---|---|
| Any | Plane curation | 1–1.5h | No deps; pick a slack moment |
| 2 | D-STR + D-MKD | 5–9h | D-STR first; shared Caddy reload |
| 3 | D-ZBX + D-RST | 7–12h | D-ZBX automated; D-RST needs operator presence |
| 4 | D-LOG | 6–10h | Full session; highest discovery budget |
| 5 | D-XINDEX | 4–8h | Check 4.E status first; can run standalone |
| 6 | CL-14 | 2–3h | After all blocks closed |
| **Total** | | **25–44h** | |
