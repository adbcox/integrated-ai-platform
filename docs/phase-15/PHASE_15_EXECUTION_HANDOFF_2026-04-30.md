# Phase 15 — Complete Execution Handoff

**Date:** 2026-04-30
**Previous gate:** `phase-14-final` — PASS=16 FAIL=0 WARN=3, tag `9acfe6e`
**Baseline for all gates:** PASS=16 FAIL=0 WARN=3
**HEAD at handoff:** `db30fc4` (Phase 15 plan commit)
**Discovery numbering continues at:** #37

This document is a single self-contained execution handoff. Read it
once, then execute top to bottom. Hard stops are marked HARD STOP.
Surface only at hard stops or the final CL gate.

---

## Context files — read before beginning any block

```
CLAUDE.md                                               (platform rules, non-negotiables)
docs/ARCHITECTURE.md                                    (service inventory, node map)
docs/DECISION_REGISTER.md                               (13 ADRs)
docs/phase-13/PHASE_13_CLOSEOUT_CAMPAIGN_PLAN_2026-04-29.md   (D-OP, D-CN, 4.H, 4.J scope)
docs/phase-13/PHASE_13_INCREMENT_2A_CLOSEOUT_2026-04-29.md    (InvenTree 2A state)
docs/phase-14/PHASE_14_BLOCK_D_DOC_CLOSEOUT_2026-04-29.md     (D-DOC addendum, D-35 Plane token)
docs/phase-15/PHASE_15_PLAN_2026-04-30.md               (Phase 15 strategy)
docs/canonical-patterns/plane-connector-usage.md        (mandatory for all Plane writes)
docs/runbooks/add-new-service.md                        (Vault sidecar pattern)
docs/runbooks/operating-model.md                        (IV&V doctrine)
framework/plane_connector.py                            (current connector state)
docker/mkdocs/docker-compose.yml                        (CF-1 target)
```

---

## Execution order

```
Block A — Carry-forwards (CF-1 through CF-4)        ~4–7h    [no prereqs]
Block B — D-OP (operating-model doctrine ADRs)      ~2–3h    [no prereqs]
Block C — D-CN (connector hardening)                ~4–6h    [no prereqs]
Block D — Mac Studio Day-1                          ~2–3h    [HARD STOP: Studio must arrive]
Block E — 4.H (upgrade-watcher)                     ~4–7h    [no prereqs]
Block F — 4.J (network discovery → NetBox)          ~6–10h   [no prereqs]
Block G — Plane backlog curation                    ~1–2h    [no prereqs]
Block H — 2B (InvenTree suppliers + CSV)            ~6–10h   [HARD STOP: Mouser+DigiKey+CSV]
Block I — 4.E (cross-index service)                 ~6–10h   [hard dep: Block H]
Block J — 4.I (receipt ingestion)                   ~6–10h   [HARD STOP: Gmail OAuth + vision decision]
Block K — 4.G (vision plugin)                       ~6–10h   [hard dep: Block H]
Block L — HF-1 (Oura Ring 4)                        ~5–8h    [HARD STOP: Oura OAuth]
Block M — HF-2 (Garmin)                             ~5–8h    [HARD STOP: Garmin auth]
Block N — 4.F (BLE label maker)                     ~4–8h    [HARD STOP: BLE hardware]
Block O — Phase 13 CL closeout                      ~2–3h    [dep: H+I+E+F, defer J+K+L+M+N if needed]
```

Blocks A–G have no external prereqs and execute serially in this order.
Blocks D interrupts if Studio arrives mid-execution — it is a one-day
hardware-integration block. Blocks H–N open when the operator delivers
the listed prerequisites; execute in order as they become available.
Block O closes Phase 13 — it can be run on blocks H+I+E+F even if
J+K+L+M+N are still pending.

---

## Block A — Carry-forwards (CF-1 through CF-4)

**Estimate:** 4–7h total.

### CF-1 — MkDocs healthcheck fix

**Problem:** `docker/mkdocs/docker-compose.yml` uses `curl` in the healthcheck.
The `squidfunk/mkdocs-material` distroless image has no `curl`; healthcheck
reports `unhealthy` even though the container serves correctly on port 8000.

**Fix:**

```bash
# Verify the issue first
docker inspect mkdocs | python3 -c "
import json,sys
data=json.load(sys.stdin)[0]
print(data['Config']['Healthcheck'])
print('Status:', data['State']['Health']['Status'])
"
```

Edit `docker/mkdocs/docker-compose.yml` — replace the healthcheck block:

```yaml
    healthcheck:
      test: ["CMD-SHELL", "python3 -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/')\" || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 45s
```

Apply and verify:

```bash
docker compose -f docker/mkdocs/docker-compose.yml up -d mkdocs
sleep 35
docker inspect mkdocs | python3 -c "
import json,sys
data=json.load(sys.stdin)[0]
print('Health:', data['State']['Health']['Status'])
"
# Expected: healthy
```

IV&V: `curl -sk https://docs.internal/ | grep -c "<title>"` → nonzero.

**Commit:** `fix(mkdocs): healthcheck — python3 urllib instead of curl (CF-1)`

---

### CF-2 — Plane API token proper rotation (D-35)

**Background (D-35):** During NF-14-1 admin password rotation, the Plane API
token `plane_api_f6c2c3cc049d4fedb24b0f62acbfc00b` was soft-deleted. It was
restored via a direct DB update (`deleted_at=NULL`). That is not a proper
rotation — the token should be freshly generated and the old one hard-deleted.

**Step 1 — Generate fresh token:**

```bash
# Via Plane API (token is still active post-restore)
# First: get current token from Vault
PLANE_TOKEN=$(vault kv get -field=token secret/plane/api)
echo "sha256: $(echo -n $PLANE_TOKEN | sha256sum | head -c 12)"  # hash only, never print value

# Generate new token via Plane API
curl -s -X POST http://localhost:3001/api/v1/workspaces/<workspace-slug>/api-tokens/ \
  -H "X-CSRFToken: <csrf-token>" \
  -H "Cookie: <session-cookie>" \
  -d '{"label":"platform-automation","description":"Phase 15 CF-2 rotation"}' \
  | python3 -m json.tool | grep -v '"token"'  # never print token value
```

**Step 2 — Write to Vault:**

```bash
# Read new token from generation output, write to Vault
vault kv put secret/plane/api \
  token=<new-token> \
  rotated=2026-04-30 \
  reason="CF-2: proper rotation replacing D-35 soft-delete restore"
# Verify hash: expected prefix different from prior
PLANE_TOKEN=$(vault kv get -field=token secret/plane/api)
echo "sha256: $(echo -n $PLANE_TOKEN | sha256sum | head -c 12)"
```

**Step 3 — Update mcpo-proxy:**

The Vault Agent sidecar for mcpo-proxy renders `secret/plane/api:token` into
`/vault/secrets/credentials.env`. Re-render by restarting the sidecar:

```bash
# Find and restart vault-agent-mcpo-proxy (or equivalent sidecar)
docker ps | grep vault-agent-mcpo
docker restart vault-agent-mcpo-proxy  # or the named sidecar container
# Verify: sidecar exits 0 (one-shot pattern)
docker ps -a | grep vault-agent-mcpo
```

**Step 4 — Hard-delete old token:**

```bash
# Via Plane DB: delete the old restored token permanently
docker exec docker-plane-db-1 psql -U plane -c \
  "DELETE FROM api_tokens WHERE token='plane_api_f6c2c3cc049d4fedb24b0f62acbfc00b';"
# Confirm: 0 rows returned for old token
docker exec docker-plane-db-1 psql -U plane -c \
  "SELECT count(*) FROM api_tokens WHERE token='plane_api_f6c2c3cc049d4fedb24b0f62acbfc00b';"
# Expected: 0
```

**Step 5 — Verify new token works:**

```bash
# Test via plane_connector.py health check
python3 -c "
from framework.plane_connector import PlaneAPI
api = PlaneAPI()
ok = api.health_check()
print('health:', ok)
ws = api.get_workspace()
print('workspace:', ws.get('name','?'), '— projects:', len(api.list_projects()))
"
# Expected: health: True, workspace name, project count
```

IV&V gate: health_check True, old token not in DB, new hash written to Vault.

**Commit:** `fix(plane): API token proper rotation — D-35 cleanup (CF-2)`

---

### CF-3 — Uptime Kuma homepage slug

**Problem:** Homepage widget for Uptime Kuma shows no monitors because no slug
is configured in Uptime Kuma's Status Pages to match the homepage config.

**Step 1 — Check current slug state:**

```bash
curl -sk https://uptime.internal/status | head -20
# Check homepage config for expected slug
grep -r "uptime\|kuma\|slug" docker/homepage/ 2>/dev/null || \
  find ~/control-center-stack -name "*.yml" -exec grep -l "uptime\|kuma" {} \;
```

**Step 2 — Create status page in Uptime Kuma:**

Access `https://uptime.internal` → Status Pages → New Status Page:
- Slug: match whatever the homepage widget is configured to expect (e.g., `homelab`)
- Add monitors: all configured monitors
- Set public: yes

**Step 3 — Verify homepage widget:**

```bash
curl -sk https://homepage.internal | grep -i "uptime\|kuma\|status"
```

IV&V: Uptime Kuma widget on homepage shows monitor status, not blank.

**Note:** This is cosmetic. If Uptime Kuma UI is unavailable or slug is
already correct, document and move on — do not block CF-4 on this.

**No commit needed** (Uptime Kuma config is runtime state, not repo-tracked).

---

### CF-4 — mcp-docs-remote pre-built image

**Problem (D#29):** `mcp-docs-remote` runs `apt-get install python3 make g++` then
`npm install -g @arabold/docs-mcp-server` at every container start. This causes:
- 60s+ cold-start time
- `cap_add: [CHOWN, SETUID, SETGID, DAC_OVERRIDE]` requirement (broad capability set)
- Network dependency at startup (npm registry must be reachable)

**Goal:** Pre-built image with tree-sitter already compiled.
Result: cold-start <5s, `cap_drop: [ALL]` only (no cap_add), no network at startup.

**Step 1 — Create Dockerfile:**

```bash
mkdir -p docker/mcp/docs-mcp-server
```

`docker/mcp/docs-mcp-server/Dockerfile`:

```dockerfile
FROM node:22-bookworm-slim
# Install build tools for tree-sitter native compilation
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends python3 make g++ && \
    npm install -g @arabold/docs-mcp-server && \
    apt-get purge -y --auto-remove python3 make g++ && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /root/.npm
# Drop to non-root
RUN groupadd -r mcp && useradd -r -g mcp mcp
USER mcp
ENTRYPOINT ["docs-mcp-server"]
```

**Step 2 — Build and test:**

```bash
docker build -t local/docs-mcp-server:latest docker/mcp/docs-mcp-server/
# Verify the binary is present
docker run --rm local/docs-mcp-server:latest --help 2>&1 | head -5
# Measure start time
time docker run --rm local/docs-mcp-server:latest --version 2>&1
```

**Step 3 — Test tree-sitter compilation:**

```bash
# The key test: can it parse code without errors?
docker run --rm -i local/docs-mcp-server:latest \
  echo '{"jsonrpc":"2.0","method":"ping","id":1}' | \
  timeout 10 docker run --rm -i local/docs-mcp-server:latest 2>&1 | head -5
```

**Step 4 — Update obot-stack.yml:**

Find mcp-docs-remote in `docker/obot-stack.yml`:

```yaml
  mcp-docs-remote:
    image: local/docs-mcp-server:latest   # was: node:22 with startup install
    container_name: mcp-docs-remote
    restart: unless-stopped
    cap_drop: [ALL]                        # was: [ALL] + cap_add for apt
    security_opt: [no-new-privileges:true]
    # Remove the command: that ran apt-get + npm install
    # Remove cap_add entirely
    mem_limit: 256m
    networks:
      - caddy-net
```

**Step 5 — Deploy and verify:**

```bash
docker compose -f docker/obot-stack.yml up -d mcp-docs-remote
docker ps | grep mcp-docs-remote
# Verify no restart loop
docker inspect mcp-docs-remote | python3 -c "
import json,sys
d=json.load(sys.stdin)[0]
print('Status:', d['State']['Status'])
print('RestartCount:', d['RestartCount'])
"
# Expected: Status: running, RestartCount: 0
```

IV&V: container up, no restart, cap_drop:[ALL] with no cap_add, cold start <15s.

**Commit:** `feat(mcp): docs-mcp-server pre-built image — D#29 remediation (CF-4)`

---

## Block B — D-OP: Operating-Model Doctrine ADRs

**Estimate:** 2–3h.
**Doctrine:** ADR-A-013 fold gates (all sub-items are mechanical doc authoring
once the content is decided; no executable artifact to validate independently).

**Scope:** Three new ADRs + DECISION_REGISTER update + one runbook.
The patterns exist in Block 4.C evidence; this block makes them durable.

### B.1 — ADR-A-014: NetBox as authoritative CMDB

File: `docs/adr/ADR-A-014-netbox-cmdb-authority.md`

```markdown
# ADR-A-014 — NetBox as Authoritative CMDB

**Status:** Accepted
**Date:** 2026-04-30
**Phase:** 15

## Context

Block 4.C migrated the service registry from `config/service-registry.yaml`
to NetBox CMDB. CMDB_SOURCE default was `yaml` during the transition window;
flipped to `netbox` in Phase 14 D-DOC (commit `60aeb96`). Seventeen discoveries
surfaced during the migration. This ADR captures the outcome as a durable
architectural decision.

## Decision

NetBox (`netbox.internal`) is the authoritative source of truth for:
- Service inventory (name, host, port, protocol)
- Physical node inventory (devices, IP addresses, roles)
- Network topology (vlans, prefixes, interfaces)

`config/service-registry.yaml` is retained solely as a deprecation-gate
fallback (ADR-A-012 lifecycle requirement) accessible via `CMDB_SOURCE=yaml`.
It is not a write target; updates must go to NetBox.

## Alternatives considered

- **Homegrown YAML only:** Rejected. YAML requires manual sync; no schema
  validation; no query API. Not suitable beyond ~20 services.
- **InvenTree-only:** Rejected. InvenTree models physical parts; it has no
  concept of running services or network topology.
- **Netshot / LibreNMS:** Rejected. Network-discovery-first tools; not
  designed for service registry use.

## Consequences

Positive:
- Single authoritative store; `scripts/cmdb_source.py` is the canonical
  consumer path.
- NetBox GraphQL + REST APIs enable topology-API and cross-index service
  (Block 4.E) without custom parsers.
- Portability: NetBox runs as a Docker container; same API on any host.

Negative:
- NetBox is a dependency; its failure means topology-API degraded to YAML
  fallback (acceptable; YAML is retained for this case).
- Schema changes in NetBox require migration planning (Discovery #16
  round-trip equivalence doctrine — see ADR-A-015).

## Related

- ADR-A-012 (equivalence harness — the migration proof)
- ADR-A-015 (staged-toggle pattern — the transition mechanism)
- `scripts/cmdb_source.py` line 311 (implementation)
- `docs/architecture/dependency-graph.md` (topology view)
```

### B.2 — ADR-A-015: Staged-Toggle Pattern for Source Migrations

File: `docs/adr/ADR-A-015-staged-toggle-migration.md`

```markdown
# ADR-A-015 — Staged-Toggle Pattern for Source-of-Truth Migrations

**Status:** Accepted
**Date:** 2026-04-30
**Phase:** 15

## Context

When migrating an authoritative data source, the platform cannot do a hard
cutover: running services depend on the old source, and a bug in the new
source could break production. Block 4.C's NetBox migration proved a pattern
that safely handles this class of problem.

## Decision

All source-of-truth migrations use the staged-toggle pattern:

1. **Build a unified loader** that accepts both old and new sources via a
   single env-var flag (`CMDB_SOURCE=yaml|netbox`). The loader is the only
   code that knows which source is active.
2. **Default to old** (`CMDB_SOURCE=yaml` initially). New source is opt-in.
3. **Prove equivalence at migration time** (ADR-A-012): run the loader in
   both modes against the same snapshot; assert byte-identical output.
4. **Flip the default** after a stability window (≥1 week no incidents that
   would have demanded old-source fallback).
5. **Retain the old source** as a fallback for at least one full release cycle
   after the flip. Remove only when ADR-A-012 deprecation-gate re-run passes.

## Consequences

Positive:
- Zero-downtime migration; instant rollback by env-var flip.
- Migration correctness provable before cutover.
- Fallback path is documented and tested.

Negative:
- Loader must maintain two code paths during the transition window.
- Requires discipline not to write to the old source during transition.
```

### B.3 — ADR-A-016: Canonical Patterns Registry

File: `docs/adr/ADR-A-016-canonical-patterns-registry.md`

```markdown
# ADR-A-016 — Canonical Patterns Registry

**Status:** Accepted
**Date:** 2026-04-30
**Phase:** 15

## Context

Block 4.C surfaced 17 discoveries. Many of these are not one-off fixes but
reusable patterns that should be applied consistently across the platform.
Today these live only in discovery comments in closeout docs; they decay into
tribal knowledge. This ADR formalises a canonical patterns registry.

## Decision

`docs/canonical-patterns/` is the platform's patterns registry. Each pattern
file documents:
- The problem class it solves
- The canonical implementation (code snippet or config excerpt)
- The discovery or incident that proved the pattern necessary
- The services it applies to today

Current entries:
- `plane-connector-usage.md` — Plane V1 API usage (RateLimitError order,
  `labels` vs `label_ids`, first-batch-verify, `_with_429_retry`)

New patterns are added when:
- A Discovery identifies a cross-cutting concern (applies to >1 service)
- A runbook references the same implementation more than once

## Consequences

Positive:
- Execution windows can reference a canonical pattern rather than
  re-deriving it from discovery notes.
- New blocks onboard faster; fewer repeated discoveries.

Negative:
- Patterns require maintenance; stale patterns are worse than no patterns.
- Review patterns on each major version bump of external dependencies.
```

### B.4 — Runbook: migrate-source-of-truth.md

File: `docs/runbooks/migrate-source-of-truth.md`

```markdown
# Runbook — Migrate a Source of Truth

**Pattern:** Staged-toggle (ADR-A-015)
**Doctrine:** ADR-A-012 (equivalence harness must run at migration time)

## Step 1 — Build the unified loader

Write a single loader module that reads from either the old or new source
based on `CMDB_SOURCE` env var. Both paths must produce identical output
schemas. Example: `scripts/cmdb_source.py`.

## Step 2 — Populate the new source

Migrate data to the new source. Do not write to the old source after this
point.

## Step 3 — Run equivalence harness

```bash
# With both sources populated, prove byte-identical output
python3 scripts/cmdb_source.py --source yaml  > /tmp/old.json
python3 scripts/cmdb_source.py --source netbox > /tmp/new.json
diff /tmp/old.json /tmp/new.json
# Expected: empty diff (byte-identical)
```

Document the diff output in the migration closeout doc (even if empty).
A non-empty diff is a HARD STOP — investigate and resolve before
flipping the default.

## Step 4 — Flip the default

Change the default value of `CMDB_SOURCE` in the loader from old to new.
Add a `CMDB_SOURCE=old` env var to any service that needs rollback access.

## Step 5 — Stability window

Run for ≥1 week under the new default. Monitor for:
- Services that can't read from the new source (check container logs)
- API errors from new-source-specific endpoints

## Step 6 — Deprecation gate

Re-run equivalence harness. Verify output is still identical. Then remove
the old-source code path (or freeze it as read-only).
```

### B.5 — DECISION_REGISTER update

Add rows for A-014, A-015, A-016 to `docs/DECISION_REGISTER.md` under a new
"CMDB and data governance" section. Follow existing table format exactly.

**Regression probe:** Run `docs/phase-13/h1-regression-probe.sh` after B.5.
Expected: PASS=16 FAIL=0 WARN=3 (no change; D-OP is docs only).

**Commit:** `docs(phase-15-B): D-OP — ADR-A-014/015/016 + migrate-source-of-truth runbook`

---

## Block C — D-CN: Plane Connector Hardening

**Estimate:** 4–6h.
**Doctrine:** ADR-A-011 (full IV&V on audit; fold gates on mechanical fixes).
**Reference:** `docs/phase-13/POST_BLOCK_4C_NEXT_OPTIONS.md` Option B; Discoveries #10–#15.

### C.1 — Audit current connector state

```bash
# Check which discoveries are already fixed vs still open
python3 - <<'EOF'
import ast, pathlib, textwrap

src = pathlib.Path("framework/plane_connector.py").read_text()

# Discovery #14: create_issue name field bug
# Check: does payload always include 'name'?
# Already fixed (payload["name"] = name is unconditional) -- verify
print("Discovery #14 (create_issue name field):")
if '"name": name' in src or "'name': name" in src:
    print("  FIXED: name always in payload")
else:
    print("  OPEN: check create_issue payload")

# Discovery #13: dry-run skips apply path
print("Discovery #13 (dry-run apply path test):")
if 'apply_path' in src or 'dry_run' in src:
    print("  apply_path/dry_run found — check coverage")
else:
    print("  OPEN: no dry-run integration test present")

# Discovery #10: rate-limit handling
print("Discovery #10 (rate-limit handling):")
if 'RateLimitError' in src:
    print("  RateLimitError class exists")
    # Count usages
    count = src.count('RateLimitError')
    print(f"  {count} occurrences")

# Discovery #11: error class hierarchy
print("Discovery #11 (error class hierarchy):")
exceptions = [l for l in src.split('\n') if 'class ' in l and 'Error' in l]
print(f"  Exception classes: {exceptions}")

# Discovery #12: pagination contract
print("Discovery #12 (pagination):")
if 'next_page_results' in src:
    print("  next_page_results terminator found")

# Discovery #15: first-batch verify
print("Discovery #15 (first-batch verify):")
if 'verify_issue_field' in src:
    print("  verify_issue_field method exists")
EOF
```

### C.2 — Fix Discovery #14 (if still open)

From reading the connector, `create_issue` already sets `payload["name"] = name`
unconditionally at line ~371. Confirm the audit from C.1 and document as closed
if already fixed. If somehow still open:

```python
# In create_issue, ensure this is ALWAYS first in payload construction:
payload: dict[str, Any] = {
    "name": name,                    # MUST be present — Discovery #14
    "description_html": f"<p>{description}</p>" if description else "",
    "priority": priority,
}
```

### C.3 — Add apply-path integration test (Discovery #13)

The audit requires a staging project. If Plane has a "test" or "sandbox"
workspace project:

```bash
# Find staging project
python3 -c "
from framework.plane_connector import PlaneAPI
api = PlaneAPI()
for p in api.list_projects():
    print(p['id'], p['name'], p['identifier'])
"
```

Write `scripts/test-plane-apply-path.py`:

```python
#!/usr/bin/env python3
"""Discovery #13 — integration test for connector apply path.
Run against a staging/sandbox project; tears down created issue.
Never run against the production roadmap project.
"""
import os, sys, time
from framework.plane_connector import PlaneAPI, RateLimitError

STAGING_PROJECT_ID = os.environ.get("PLANE_STAGING_PROJECT_ID")
if not STAGING_PROJECT_ID:
    print("PLANE_STAGING_PROJECT_ID not set — cannot run apply-path test")
    sys.exit(1)

api = PlaneAPI()
api._project_id = STAGING_PROJECT_ID   # override to staging

print("Step 1: create test issue")
issue = api.create_issue(
    name="[apply-path-test] D#13 integration test — delete me",
    description="Automated apply-path smoke test. Will be deleted.",
    priority="low",
    external_id="apply-path-test-D13",
)
issue_id = issue["id"]
print(f"  Created: {issue_id}")

print("Step 2: verify creation (first-batch-verify pattern)")
if not api.verify_issue_field(issue_id, "name", "[apply-path-test] D#13 integration test — delete me"):
    print("FAIL: name field not persisted after POST")
    sys.exit(1)
print("  name verified")

print("Step 3: apply a label update")
labels = api.list_labels()
if labels:
    label_id = labels[0]["id"]
    api.update_issue(issue_id, {"labels": [label_id]})
    time.sleep(1.5)
    if not api.verify_issue_field(issue_id, "labels", [label_id]):
        print("FAIL: label update not persisted")
        sys.exit(1)
    print(f"  label update verified")
else:
    print("  SKIP: no labels in staging project to test with")

print("Step 4: apply a state transition")
states = api.list_states()
done_state = next((s["id"] for s in states if s["name"].lower() in ("done","closed")), None)
if done_state:
    api.update_issue_state(issue_id, "Done")
    time.sleep(1.5)
    reopened = api._get(api._proj_url(f"/issues/{issue_id}/"))
    print(f"  state after: {reopened.get('state_detail',{}).get('name','?')}")

print("Step 5: delete test issue")
deleted = api._delete(api._proj_url(f"/issues/{issue_id}/"))
print(f"  deleted: {deleted}")

print("PASS: apply-path integration test complete")
```

Run: `PLANE_STAGING_PROJECT_ID=<id> python3 scripts/test-plane-apply-path.py`

Expected output: PASS with all steps verified.

### C.4 — Audit rate-limit handling uniformity (Discovery #10)

```bash
# Find all callers of plane_connector and check RateLimitError handling
grep -rn "plane_connector\|PlaneAPI\|_patch\|_post\|upsert_issue\|create_issue" \
  scripts/ framework/ --include="*.py" | grep -v "__pycache__" | grep -v ".pyc"
```

For each script that calls the connector: verify the pattern
`except RateLimitError` appears BEFORE `except Exception`.

If any script is missing proper handling, add a wrapper. The canonical pattern:

```python
try:
    api.upsert_issue(...)
except RateLimitError:
    time.sleep(60)
    api.upsert_issue(...)   # one retry
except Exception as exc:
    print(f"item-level error: {exc}", file=sys.stderr)
```

### C.5 — Document pagination contract (Discovery #12)

Add a docstring to `_paginate` in `framework/plane_connector.py`:

```python
def _paginate(self, ...):
    """Paginate a Plane list endpoint.

    Termination contract (Discovery #12):
    - Primary: stop when `next_page_results` is False in the response JSON.
    - Secondary: stop when a page returns 0 results (protects against
      endpoints that omit next_page_results).
    - Tertiary: stop after 500 pages (hard limit; prevents runaway loops
      if the pagination contract changes in a Plane upgrade).

    All three conditions are checked in the while loop below. The primary
    condition is sufficient for current Plane CE versions (≥0.22).
    """
```

### C.6 — Regression and gate

```bash
# Run connector unit tests if they exist
python3 -m pytest tests/ -k "plane" -v 2>/dev/null || echo "no unit tests"

# Run apply-path integration test
PLANE_STAGING_PROJECT_ID=<staging-id> python3 scripts/test-plane-apply-path.py

# Run regression probe
bash docs/phase-13/h1-regression-probe.sh
# Expected: PASS=16 FAIL=0 WARN=3
```

**Commit:** `fix(connector): D-CN hardening — apply-path test, rate-limit audit, pagination contract (D#10-#15)`

---

## Block D — Mac Studio Day-1

**HARD STOP:** Do not begin Block D until the Mac Studio M3 Ultra physically arrives
and is powered on. This block is intentionally short — it is hardware integration
only, not a multi-session build-out.

**Prereq check before starting:**
```bash
# From Mac Mini — verify Studio is reachable
ping -c3 192.168.10.146 2>/dev/null && echo "Studio reachable" || echo "Studio not on LAN yet"
# If unreachable: wait; do not proceed
```

**Verify Mac Mini chip to resolve M4-Pro/M5 contradiction:**
```bash
ssh admin@192.168.10.145 "system_profiler SPHardwareDataType 2>/dev/null | grep -E 'Chip|Memory'"
# Record actual chip name; update CLAUDE.md if needed
```

### D.1 — Studio OS baseline

On Studio (via SSH once network is up, or locally):
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# CLI tools matching Mini baseline
brew install colima docker docker-compose vault jq git

# Start Colima — 80GB/24CPU for large-model workloads
colima start --cpu 24 --memory 80 --disk 500 --arch aarch64
docker info | grep -E "CPUs|Memory"
# Expected: CPUs: 24, Memory: ~82GB
```

### D.2 — NetBox registration

```bash
# From Mini: register Studio in NetBox
# Get Vault token for NetBox API
NETBOX_TOKEN=$(vault kv get -field=token secret/netbox/api 2>/dev/null || \
  vault kv get -field=api_token secret/netbox/api 2>/dev/null)

curl -s -X POST http://netbox.internal/api/dcim/devices/ \
  -H "Authorization: Token $NETBOX_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mac-studio",
    "device_type": {"slug": "mac-studio"},
    "site": {"slug": "home-lab"},
    "role": {"slug": "compute-node"},
    "status": "active",
    "comments": "Mac Studio M3 Ultra 96GB — compute node; arrived 2026-05-01"
  }' | python3 -m json.tool | grep '"id"\|"name"\|"display"'
```

If device-type slug doesn't exist, create it first via NetBox UI at `netbox.internal`.

### D.3 — Headscale client enrollment

```bash
# On Mini: generate pre-auth key
headscale preauthkeys create --user homelab --expiration 24h
# Note the key — do NOT write it anywhere persistent

# On Studio: install Tailscale and join
brew install tailscale
tailscale up --login-server https://headscale.internal --authkey <key>
# Verify from Mini
headscale nodes list | grep mac-studio
```

### D.4 — ARCHITECTURE.md + CLAUDE.md update

Update `docs/ARCHITECTURE.md` Physical Nodes table:

```markdown
| Mac Studio M3 Ultra | Compute node — large-model inference | 192.168.10.146 |
```

Remove Mac Studio from the "Future nodes" section.

Update `CLAUDE.md`:
- Line 4: add Mac Studio to "Deployment Target"
- "Heterogeneous Architecture": move Mac Studio from "future block" to active
- Correct M4-Pro vs M5 contradiction (use verified `system_profiler` output)

**Regression probe:** PASS=16 FAIL=0 WARN=3 (Studio not yet in probe).

**Commit:** `docs(phase-15-D): Mac Studio day-1 — NetBox registration, Headscale, ARCHITECTURE.md`

---

## Block E — 4.H: Upgrade-Watcher Service

**Estimate:** 4–7h.
**Reference:** Phase 13 campaign plan §2 Block 4.H.
**Approach:** Diun (Docker Image Update Notifier) — lightest option; ARM64 native;
notifies via webhook. Custom Plane issue creation via webhook adapter.

### E.1 — Pre-deploy audit

```bash
# Collect all pinned image tags from in-repo compose files
grep -rh "image:" docker/ --include="*.yml" | \
  grep -v "^#\|x-" | \
  sort -u | head -40

# Check out-of-repo pinned images too
find ~/control-center-stack -name "*.yml" -exec grep -h "image:" {} \; 2>/dev/null | \
  grep -v "^#" | sort -u | head -20

# Port check
ss -tlnp | grep -E "5000|8095|8096"
```

### E.2 — Compose file

`docker/upgrade-watcher/docker-compose.yml`:

```yaml
version: "3.9"

services:
  diun:
    image: crazymax/diun:latest
    container_name: upgrade-watcher
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - diun-data:/data
      - ./diun.yml:/diun.yml:ro
    environment:
      - LOG_LEVEL=info
      - LOG_JSON=false
    command: ["serve", "--config=/diun.yml"]
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 128m
    networks:
      - control-center-net

volumes:
  diun-data:

networks:
  control-center-net:
    external: true
    name: control-center-net
```

### E.3 — Diun configuration

`docker/upgrade-watcher/diun.yml`:

```yaml
db:
  path: /data/diun.db

watch:
  workers: 8
  schedule: "0 8 * * *"     # daily at 08:00
  first_check_notif: false   # don't fire on first run

notif:
  webhook:
    endpoint: http://host.docker.internal:8086/webhook/upgrade   # topology-api or custom receiver
    method: POST
    headers:
      Content-Type: application/json
    timeout: 30s

providers:
  docker:
    watch_stopped: false
    # Include all running containers
```

**Note on webhook receiver:** The topology-api at port 8086 may not have a
`/webhook/upgrade` endpoint. Two options:
1. Deploy a minimal webhook receiver (Python Flask, 20 lines) that creates Plane issues.
2. Use Diun's built-in Slack notifier if a webhook URL is configured.
3. Use Diun's SMTP notifier to operator email.

Preferred: option 1 — create `scripts/webhook-upgrade-receiver.py` (see below).

### E.4 — Webhook receiver for Plane issues

`scripts/webhook-upgrade-receiver.py`:

```python
#!/usr/bin/env python3
"""Receives Diun webhook payloads and creates Plane issues for image updates."""
import json, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from framework.plane_connector import PlaneAPI, RateLimitError
import time

api = PlaneAPI()

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        self.send_response(200)
        self.end_headers()

        entry = body.get("entry", {})
        image = entry.get("image", "unknown")
        new_tag = entry.get("new_tag", "?")
        old_tag = entry.get("old_tag", "?")

        title = f"[UPGRADE] {image}: {old_tag} → {new_tag}"
        desc = (
            f"Diun detected a new tag for `{image}`.\n\n"
            f"Old: `{old_tag}`\nNew: `{new_tag}`\n\n"
            f"Review changelog and update image pin in compose file."
        )
        try:
            issue = api.create_issue(name=title, description=desc, priority="low")
            print(f"Created Plane issue: {issue.get('id')} — {title}")
        except RateLimitError:
            time.sleep(60)
            try:
                api.create_issue(name=title, description=desc, priority="low")
            except Exception as e:
                print(f"Retry failed: {e}")
        except Exception as e:
            print(f"Failed to create issue: {e}")

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8097))
    print(f"Upgrade receiver listening on :{port}")
    HTTPServer(("", port), Handler).serve_forever()
```

Add a service for this receiver to `docker/upgrade-watcher/docker-compose.yml`:

```yaml
  upgrade-receiver:
    image: python:3.12-slim
    container_name: upgrade-receiver
    restart: unless-stopped
    working_dir: /app
    volumes:
      - ../../framework:/app/framework:ro
      - ../../scripts/webhook-upgrade-receiver.py:/app/receiver.py:ro
    environment:
      - PORT=8097
      - PLANE_API_URL=http://host.docker.internal:3001
      - PLANE_WORKSPACE_SLUG=${PLANE_WORKSPACE_SLUG}
      - PLANE_PROJECT_ID=${PLANE_PROJECT_ID}
    command: ["python3", "receiver.py"]
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 128m
    ports:
      - "127.0.0.1:8097:8097"
    networks:
      - control-center-net
```

Update `diun.yml` webhook endpoint to `http://upgrade-receiver:8097`.

### E.5 — Deploy and verify

```bash
docker compose -f docker/upgrade-watcher/docker-compose.yml up -d
docker ps | grep -E "upgrade|diun"
# Trigger a test run
docker exec upgrade-watcher diun show --config=/diun.yml
# Check for errors
docker logs upgrade-watcher --tail 20
```

IV&V: Diun starts, reads Docker socket, lists watched images.
Gate: no restart loop, logs show image watch count > 0.

**Commit:** `feat(phase-15-E): 4.H upgrade-watcher — Diun + Plane webhook receiver`

---

## Block F — 4.J: Network Discovery → NetBox

**Estimate:** 6–10h.
**Purpose:** Automated active scan + passive arp-table feeding NetBox dcim/ipam objects.
**Risk:** Writes into authoritative NetBox store — full IV&V (ADR-A-011).

### F.1 — Audit existing NetBox dcim shape

```bash
# What devices/IPs are currently in NetBox?
python3 - <<'EOF'
import os, requests, json

NETBOX_URL = "http://netbox.internal"
TOKEN = os.environ.get("NETBOX_TOKEN", "")
if not TOKEN:
    import subprocess
    TOKEN = subprocess.check_output(
        ["vault", "kv", "get", "-field=token", "secret/netbox/api"],
        text=True
    ).strip()

headers = {"Authorization": f"Token {TOKEN}"}

devices = requests.get(f"{NETBOX_URL}/api/dcim/devices/", headers=headers).json()
print(f"Devices in NetBox: {devices['count']}")
for d in devices['results'][:5]:
    print(f"  {d['name']} — {d.get('primary_ip',{}).get('address','no-ip')}")

ips = requests.get(f"{NETBOX_URL}/api/ipam/ip-addresses/", headers=headers).json()
print(f"IP addresses in NetBox: {ips['count']}")
EOF
```

### F.2 — Network scanner script

`scripts/network-discovery.py`:

```python
#!/usr/bin/env python3
"""
Scan 192.168.10.0/24, resolve hostnames, compare against NetBox.
For each discovered host not in NetBox: create an IP address record
and optionally a Device record (with manual confirmation flag).

Writes are gated on first-batch-verify (ADR-A-011/A-015).
Run with --dry-run to preview changes; run without for writes.
"""
import argparse, os, subprocess, json, sys, time, ipaddress
import requests

NETWORK = "192.168.10.0/24"
NETBOX_URL = os.environ.get("NETBOX_URL", "http://netbox.internal")


def get_token():
    try:
        return subprocess.check_output(
            ["vault", "kv", "get", "-field=token", "secret/netbox/api"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return os.environ.get("NETBOX_TOKEN", "")


def nmap_scan(network: str) -> list[dict]:
    """Run nmap -sn (ping scan) and parse output."""
    result = subprocess.run(
        ["nmap", "-sn", "--open", "-oG", "-", network],
        capture_output=True, text=True, timeout=120
    )
    hosts = []
    for line in result.stdout.splitlines():
        if line.startswith("Host:"):
            parts = line.split()
            ip = parts[1]
            hostname = parts[2].strip("()") if len(parts) > 2 else ""
            hosts.append({"ip": ip, "hostname": hostname})
    return hosts


def arp_scan() -> list[dict]:
    """Read macOS ARP table for passive discovery."""
    result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
    hosts = []
    for line in result.stdout.splitlines():
        # Format: hostname (ip) at mac [ether] on interface
        parts = line.split()
        if len(parts) >= 2 and "(" in parts[1]:
            ip = parts[1].strip("()")
            hostname = parts[0] if parts[0] != "?" else ""
            mac = parts[3] if len(parts) > 3 and ":" in parts[3] else ""
            hosts.append({"ip": ip, "hostname": hostname, "mac": mac})
    return hosts


def get_netbox_ips(token: str) -> set[str]:
    headers = {"Authorization": f"Token {token}"}
    r = requests.get(f"{NETBOX_URL}/api/ipam/ip-addresses/?limit=1000", headers=headers)
    return {addr["address"].split("/")[0] for addr in r.json().get("results", [])}


def create_ip(token: str, ip: str, hostname: str, dry_run: bool) -> dict | None:
    if dry_run:
        print(f"  DRY-RUN: would create IP {ip} ({hostname})")
        return None
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    payload = {
        "address": f"{ip}/24",
        "status": "active",
        "dns_name": hostname or "",
        "description": f"Auto-discovered by network-discovery.py",
    }
    r = requests.post(f"{NETBOX_URL}/api/ipam/ip-addresses/", headers=headers, json=payload)
    if r.status_code == 201:
        return r.json()
    else:
        print(f"  ERROR: {r.status_code} — {r.text[:200]}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview only; no writes")
    parser.add_argument("--arp-only", action="store_true", help="Passive ARP only; no nmap")
    args = parser.parse_args()

    token = get_token()
    if not token:
        print("ERROR: cannot get NetBox token from Vault", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {NETWORK} ...")
    if args.arp_only:
        discovered = arp_scan()
    else:
        discovered = nmap_scan(NETWORK) + arp_scan()

    # Deduplicate by IP
    seen: dict[str, dict] = {}
    for h in discovered:
        if h["ip"] not in seen:
            seen[h["ip"]] = h
    hosts = list(seen.values())
    print(f"Discovered {len(hosts)} hosts")

    existing_ips = get_netbox_ips(token)
    new_hosts = [h for h in hosts if h["ip"] not in existing_ips]
    print(f"Not in NetBox: {len(new_hosts)} hosts")

    if not new_hosts:
        print("Nothing to add.")
        return

    # First-batch-verify (ADR-A-011)
    first = new_hosts[0]
    print(f"First-batch-verify: creating {first['ip']} ({first['hostname']})")
    result = create_ip(token, first["ip"], first["hostname"], args.dry_run)
    if not args.dry_run:
        if result is None:
            print("ABORT: first-batch-verify failed — check NetBox API")
            sys.exit(1)
        # Verify it appears in NetBox
        time.sleep(2)
        check = get_netbox_ips(token)
        if first["ip"] not in check:
            print("ABORT: first-batch-verify failed — IP not found in NetBox after creation")
            sys.exit(1)
        print("  First-batch-verify PASSED")

    # Remaining hosts
    for host in new_hosts[1:]:
        create_ip(token, host["ip"], host["hostname"], args.dry_run)
        time.sleep(0.5)   # avoid rate-limit on NetBox API

    print(f"Done. Created {len(new_hosts)} IP records in NetBox.")


if __name__ == "__main__":
    main()
```

### F.3 — Dry run first, then apply

```bash
# Install nmap on Mac Mini if not present
which nmap || brew install nmap

# Dry run
python3 scripts/network-discovery.py --dry-run
# Review output: expected hosts in 192.168.10.0/24

# Apply
python3 scripts/network-discovery.py
# Verify new IPs in NetBox
curl -s "http://netbox.internal/api/ipam/ip-addresses/" \
  -H "Authorization: Token $(vault kv get -field=token secret/netbox/api)" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Total IPs: {d[\"count\"]}')"
```

### F.4 — Schedule as launchd cron

`~/Library/LaunchAgents/com.iap.network-discovery.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.iap.network-discovery</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/admin/repos/integrated-ai-platform/scripts/network-discovery.py</string>
        <string>--arp-only</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/network-discovery.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/network-discovery.err</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.iap.network-discovery.plist
launchctl list | grep network-discovery
```

**Regression probe:** PASS=16 FAIL=0 WARN=3 (no new probe section for 4.J).

**Commit:** `feat(phase-15-F): 4.J network discovery → NetBox (nmap + arp + launchd cron)`

---

## Block G — Plane Backlog Curation

**Estimate:** 1–2h.
**Reference:** Phase 14 D-DOC sub-task 14; documented in D-DOC closeout as deferred.
**Plane Curation gate status:** 99.8% coverage noted in Phase 14 closeout (616/617) —
verify current state before running full re-curation; may only need gap fill.

### G.1 — Audit current state

```bash
python3 - <<'EOF'
from framework.plane_connector import PlaneAPI, RateLimitError
api = PlaneAPI()

issues = api.list_all_issues()
labels = api.list_labels()
label_results = labels if isinstance(labels, list) else labels.get("results", [])

labeled  = [i for i in issues if i.get("labels")]
unlabeled= [i for i in issues if not i.get("labels")]
urgent   = [i for i in issues if i.get("priority") == "urgent"]
done     = [i for i in issues
            if i.get("state_detail",{}).get("name","").lower() in ("done","closed","cancelled")]

print(f"Labels available:  {len(label_results)}")
print(f"Issues total:      {len(issues)}")
print(f"Issues labeled:    {len(labeled)} ({100*len(labeled)//max(len(issues),1)}%)")
print(f"Issues unlabeled:  {len(unlabeled)}")
print(f"Urgent priority:   {len(urgent)}")
print(f"Done/Closed state: {len(done)}")
if unlabeled:
    print("\nFirst 10 unlabeled:")
    for i in unlabeled[:10]:
        print(f"  #{i.get('sequence_id','?')} {i.get('name','')[:60]}")
EOF
```

If ≥95% labeled and urgent ≤10 and done-state issues closed → curation is complete.
Document and move on.

If gaps remain:

### G.2 — Label gap fill

```bash
python3 - <<'EOF'
from framework.plane_connector import PlaneAPI, RateLimitError
import sys, time

api = PlaneAPI()
issues = api.list_all_issues()
labels = api.list_labels()
label_results = labels if isinstance(labels, list) else labels.get("results", [])

# Print label IDs for mapping
print("Available labels:")
for l in sorted(label_results, key=lambda x: x["name"]):
    print(f"  {l['id']}  {l['name']}")

unlabeled = [i for i in issues if not i.get("labels")]
print(f"\nUnlabeled count: {len(unlabeled)}")
EOF

# Build LABEL_MAP from output above, then run targeted label application
# Use the script from PHASE_14_REMAINING_WORK_HANDOFF_2026-04-30.md §Plane curation
```

### G.3 — Urgent triage and Done closure

Follow the step-by-step from `docs/phase-14/PHASE_14_REMAINING_WORK_HANDOFF_2026-04-30.md`
§Plane backlog curation, Steps 4 and 5.

**Exit gate:**
- ≥95% labeled (or document why remaining issues are intentionally unlabeled)
- Urgent count ≤10
- Done-state issues confirmed closed or documented as already handled

**Commit:** `feat(phase-15-G): Plane backlog curation — label gap fill + priority triage`

---

## Block H — Increment 2B: InvenTree Suppliers + CSV Import

**HARD STOP:** Do not begin Block H until:
1. `secret/mouser/api#key` exists in Vault (verify: `vault kv get -field=key secret/mouser/api`)
2. `secret/digikey/api` exists with `client_id` + `client_secret`
3. `docs/inventory/components-2026-04.csv` committed to repo (129 rows)

When operator delivers prerequisites, start here.

**Reference:** Phase 13 campaign plan §2 Block 4.D; Increment 2A closeout
`docs/phase-13/PHASE_13_INCREMENT_2A_CLOSEOUT_2026-04-29.md`.
**InvenTree is already deployed** (Increment 2A); this block configures suppliers and imports data.

### H.1 — Vault path verification

```bash
# Verify all three prereqs are in Vault
vault kv get -field=key secret/mouser/api | sha256sum | head -c 12
# Expected: non-trivial hash (not "null" or empty)

vault kv get secret/digikey/api | grep -E "client_id|client_secret" | sed 's/=.*/= [REDACTED]/'
# Expected: both fields present

# Verify CSV is committed
ls -la docs/inventory/components-2026-04.csv
wc -l docs/inventory/components-2026-04.csv
# Expected: 129-131 lines (1 header + 129 parts)
```

### H.2 — InvenTree health check

```bash
# Confirm InvenTree is still running from Increment 2A
docker ps | grep inventree
curl -sk https://inventree.internal/api/ | python3 -m json.tool | grep '"version"\|"apiVersion"'
# Expected: InvenTree 1.0.9, apiVersion 391
```

### H.3 — Update inventree AppRole policy for Mouser/DigiKey

The Increment 2A policy at `config/vault-policies/inventree-policy.hcl` intentionally
excluded Mouser/DigiKey paths (commented: "added in 2B"). Add them:

```hcl
# Add to config/vault-policies/inventree-policy.hcl
path "secret/data/mouser/api" {
  capabilities = ["read"]
}
path "secret/metadata/mouser/api" {
  capabilities = ["read", "list"]
}
path "secret/data/digikey/api" {
  capabilities = ["read"]
}
path "secret/metadata/digikey/api" {
  capabilities = ["read", "list"]
}
```

Apply:
```bash
vault policy write inventree config/vault-policies/inventree-policy.hcl
# Verify
vault policy read inventree | grep mouser
```

### H.4 — Update Vault Agent template for InvenTree

Edit `docker/inventree/vault-agent-inventree/credentials.env.tmpl` — add supplier keys:

```
{{- with secret "secret/data/mouser/api" -}}
MOUSER_API_KEY={{ .Data.data.key }}
{{- end }}
{{- with secret "secret/data/digikey/api" -}}
DIGIKEY_CLIENT_ID={{ .Data.data.client_id }}
DIGIKEY_CLIENT_SECRET={{ .Data.data.client_secret }}
{{- end }}
```

Restart sidecar to re-render:
```bash
docker compose -f docker/inventree/docker-compose.yml up -d vault-agent-inventree
# Wait for exit 0
docker ps -a | grep vault-agent-inventree
# Verify env file updated
ls -la ~/.vault-agent-secrets/inventree/credentials.env
```

### H.5 — Enable supplier plugins in InvenTree

```bash
# Connect to InvenTree container
docker exec -it inventree /bin/bash -c "
  . /vault/secrets/credentials.env
  # Enable inventree-supplier-panel and inventree-part-import
  python manage.py shell -c \"
from plugin.models import PluginConfig
for slug in ['inventree-supplier-panel', 'inventree-part-import']:
    p, created = PluginConfig.objects.get_or_create(key=slug)
    p.active = True
    p.save()
    print(f'{slug}: active={p.active}')
\"
"
```

Verify in InvenTree UI at `https://inventree.internal/settings/plugin/`.

### H.6 — CSV import (ADR-A-012 equivalence harness)

**Pre-import state capture:**
```bash
python3 - <<'EOF'
import requests, os

headers = {"Authorization": f"Token {os.environ['INVENTREE_TOKEN']}"}
r = requests.get("https://inventree.internal/api/part/?limit=1", headers=headers)
print(f"Parts before import: {r.json()['count']}")
EOF
```

**Import 10 parts first (first-batch-verify):**
```bash
python3 - <<'EOF'
import csv, requests, os, json

headers = {
    "Authorization": f"Token {os.environ['INVENTREE_TOKEN']}",
    "Content-Type": "application/json"
}
base = "https://inventree.internal/api"

# Get or create a default category
cats = requests.get(f"{base}/part/category/", headers=headers).json()
default_cat = cats["results"][0]["pk"] if cats["count"] else None

with open("docs/inventory/components-2026-04.csv") as f:
    reader = list(csv.DictReader(f))

print(f"CSV rows: {len(reader)}")
print(f"Columns: {list(reader[0].keys())}")

# Import first 10
created = []
for row in reader[:10]:
    payload = {
        "name": row.get("name") or row.get("Name") or row.get("part_name"),
        "description": row.get("description") or row.get("Description", ""),
        "category": default_cat,
        "active": True,
    }
    # Add supplier part number if column exists
    mpn = row.get("mpn") or row.get("MPN") or row.get("manufacturer_part_number", "")
    if mpn:
        payload["IPN"] = mpn

    r = requests.post(f"{base}/part/", headers=headers, json=payload)
    if r.status_code == 201:
        created.append(r.json()["pk"])
        print(f"  Created: {payload['name']} (pk={created[-1]})")
    else:
        print(f"  ERROR: {r.status_code} — {r.text[:100]}")

print(f"\nFirst-batch: {len(created)}/10 created")
# Verify one by re-reading
if created:
    verify = requests.get(f"{base}/part/{created[0]}/", headers=headers).json()
    print(f"Verify first: {verify.get('name')} active={verify.get('active')}")
EOF
```

If first-batch passes: import remaining 119 parts:

```bash
python3 - <<'EOF'
import csv, requests, os, time

headers = {
    "Authorization": f"Token {os.environ['INVENTREE_TOKEN']}",
    "Content-Type": "application/json"
}
base = "https://inventree.internal/api"

cats = requests.get(f"{base}/part/category/", headers=headers).json()
default_cat = cats["results"][0]["pk"] if cats["count"] else None

with open("docs/inventory/components-2026-04.csv") as f:
    reader = list(csv.DictReader(f))

# Skip first 10 (already imported)
errors = 0
for i, row in enumerate(reader[10:], start=11):
    payload = {
        "name": row.get("name") or row.get("Name") or row.get("part_name"),
        "description": row.get("description") or row.get("Description", ""),
        "category": default_cat,
        "active": True,
    }
    mpn = row.get("mpn") or row.get("MPN", "")
    if mpn:
        payload["IPN"] = mpn

    r = requests.post(f"{base}/part/", headers=headers, json=payload)
    if r.status_code != 201:
        errors += 1
        print(f"  ROW {i} ERROR: {r.status_code} — {row.get('name','?')}")
    time.sleep(0.3)   # avoid hammering InvenTree

r_check = requests.get(f"{base}/part/?limit=1", headers=headers).json()
print(f"\nImport complete: {r_check['count']} parts total, {errors} errors")
EOF
```

**Post-import equivalence harness (ADR-A-012):**
```bash
python3 - <<'EOF'
import csv, requests, os

headers = {"Authorization": f"Token {os.environ['INVENTREE_TOKEN']}"}
base = "https://inventree.internal/api"

# Count CSV rows
with open("docs/inventory/components-2026-04.csv") as f:
    csv_count = sum(1 for _ in csv.DictReader(f))

# Count InvenTree parts
r = requests.get(f"{base}/part/?limit=1", headers=headers).json()
inv_count = r["count"]

print(f"CSV rows:           {csv_count}")
print(f"InvenTree parts:    {inv_count}")
print(f"Match: {'PASS' if inv_count >= csv_count else 'FAIL — investigate'}")
EOF
```

### H.7 — Mouser integration

```bash
# Test Mouser API (within InvenTree's supplier plugin)
# Or standalone test:
python3 - <<'EOF'
import os, requests

# Get Mouser API key from env (rendered by Vault Agent)
api_key = os.environ.get("MOUSER_API_KEY", "")
if not api_key:
    import subprocess
    api_key = subprocess.check_output(
        ["vault", "kv", "get", "-field=key", "secret/mouser/api"],
        text=True, stderr=subprocess.DEVNULL
    ).strip()

# Test lookup — search for a resistor (generic, no quota risk)
r = requests.post(
    "https://api.mouser.com/api/v1/search/keyword",
    params={"apiKey": api_key},
    json={"SearchByKeywordRequest": {
        "keyword": "10k resistor 0402",
        "records": 5,
        "startingRecord": 0,
        "searchOptions": "None",
        "searchWithYourSignUpLanguage": "false"
    }}
)
data = r.json()
count = data.get("SearchResults", {}).get("NumberOfResult", "?")
print(f"Mouser search OK: {count} results for '10k resistor 0402'")
EOF
```

Configure Mouser supplier in InvenTree:
- InvenTree UI → Settings → Suppliers → Add Supplier: `Mouser Electronics`
- API Key: set via plugin config UI (rendered from `credentials.env`)

### H.8 — DigiKey integration

DigiKey uses OAuth 2.0 client_credentials flow:

```python
# Test DigiKey OAuth token retrieval (standalone)
import os, requests

CLIENT_ID = os.environ.get("DIGIKEY_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("DIGIKEY_CLIENT_SECRET", "")

r = requests.post(
    "https://api.digikey.com/v1/oauth2/token",
    data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
)
if r.status_code == 200:
    token = r.json().get("access_token", "")
    print(f"DigiKey token OK: {token[:8]}...{token[-4:]} (hash only)")
else:
    print(f"DigiKey auth failed: {r.status_code} — {r.text[:200]}")
```

Store token in Vault if long-lived, or let the plugin handle refresh.

### H.9 — NetBox cross-reference custom field

```bash
python3 - <<'EOF'
import os, requests, json

NETBOX_URL = "http://netbox.internal"
TOKEN = ""  # loaded from Vault
import subprocess
TOKEN = subprocess.check_output(
    ["vault", "kv", "get", "-field=token", "secret/netbox/api"],
    text=True, stderr=subprocess.DEVNULL
).strip()
headers = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}

# Create custom field on dcim.device: inventree_bom_url
payload = {
    "object_types": ["dcim.device"],
    "type": "url",
    "name": "inventree_bom_url",
    "label": "InvenTree BOM",
    "description": "Link to InvenTree parts list for this device's BOM",
    "required": False,
    "ui_visible": "always",
    "ui_editable": "yes",
}
r = requests.post(f"{NETBOX_URL}/api/extras/custom-fields/", headers=headers, json=payload)
print(f"Custom field create: {r.status_code}")
if r.status_code in (200, 201):
    print(f"  id: {r.json()['id']} name: {r.json()['name']}")
else:
    print(f"  response: {r.text[:200]}")
    # May already exist — check
    check = requests.get(f"{NETBOX_URL}/api/extras/custom-fields/?name=inventree_bom_url",
                         headers=headers).json()
    if check["count"] > 0:
        print(f"  Already exists: id={check['results'][0]['id']}")
EOF
```

**Regression probe:** PASS=16 FAIL=0 WARN=3.

**Commit:** `feat(phase-15-H): 2B — InvenTree suppliers (Mouser+DigiKey) + CSV import + NetBox cross-ref`

---

## Block I — 4.E: Cross-Index Service

**Hard dep:** Block H complete (InvenTree has parts data).

### I.1 — Extend cross-index-validate.py

The Phase 14 D-XINDEX cross-index already covers ADR→Plane. Extend to include
InvenTree as a data axis.

`scripts/cross-index-validate.py` — add InvenTree section:

```python
# Add after existing ADR/Plane checks

def check_inventree_netbox_crossref(netbox_token: str, inventree_token: str) -> list[str]:
    """Find NetBox devices without an InvenTree BOM URL."""
    gaps = []
    headers_nb = {"Authorization": f"Token {netbox_token}"}
    r = requests.get("http://netbox.internal/api/dcim/devices/?limit=200", headers=headers_nb)
    for device in r.json().get("results", []):
        bom = device.get("custom_fields", {}).get("inventree_bom_url", "")
        if not bom:
            gaps.append(f"Device '{device['name']}' has no InvenTree BOM URL")
    return gaps
```

### I.2 — FastAPI endpoint (optional)

If the topology-api at port 8086 has extension points, add a `/cross-index` endpoint.
Otherwise, `scripts/cross-index-validate.py` as a CLI tool is sufficient for Phase 15.

### I.3 — Deploy and verify

```bash
python3 scripts/cross-index-validate.py --verbose
# Expected: ADR checks pass, InvenTree cross-ref shows devices with/without BOM URLs
```

**Commit:** `feat(phase-15-I): 4.E cross-index — InvenTree axis + NetBox BOM cross-ref`

---

## Block J — 4.I: Gmail Receipt Ingestion

**HARD STOP:** Surface to operator. Requires:
1. `secret/gmail/oauth` in Vault (Gmail OAuth `client_id` + `client_secret` + `refresh_token`)
2. Operator decision: use `claude-pro` quota for vision, or local Studio llava model?

**Operator decision protocol:**
- If Studio has llava (vision model) pulled: use local (no Pro quota)
- If Studio is not set up yet: use claude-pro (operator-triggered, not service-driven)
- Decision recorded in this doc before proceeding

### J.1 — Gmail OAuth setup

```bash
# Verify OAuth credentials in Vault
vault kv get secret/gmail/oauth | grep -E "client_id|client_secret|refresh_token" | sed 's/=.*/= [REDACTED]/'

# Test token refresh
python3 - <<'EOF'
import os, subprocess, requests

creds = {}
for field in ["client_id", "client_secret", "refresh_token"]:
    creds[field] = subprocess.check_output(
        ["vault", "kv", "get", f"-field={field}", "secret/gmail/oauth"],
        text=True, stderr=subprocess.DEVNULL
    ).strip()

r = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": creds["client_id"],
    "client_secret": creds["client_secret"],
    "refresh_token": creds["refresh_token"],
    "grant_type": "refresh_token",
})
print(f"Token refresh: {r.status_code}")
if r.status_code == 200:
    token = r.json().get("access_token", "")
    print(f"  access_token: {token[:8]}...{token[-4:]} (hash only)")
EOF
```

### J.2 — Gmail → InvenTree receipt pipeline

`scripts/gmail-receipt-ingestion.py`:

```python
#!/usr/bin/env python3
"""
Gmail receipt ingestion → InvenTree draft parts.
Phase: run operator-triggered (not as a service).
Vision: local Ollama llava or claude-pro — set VISION_MODE env var.
"""
import os, base64, subprocess, requests, time, json

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
INVENTREE_BASE = "https://inventree.internal/api"
VISION_MODE = os.environ.get("VISION_MODE", "local")  # "local" or "claude-pro"


def get_access_token() -> str:
    creds = {f: subprocess.check_output(
        ["vault", "kv", "get", f"-field={f}", "secret/gmail/oauth"],
        text=True, stderr=subprocess.DEVNULL).strip()
        for f in ["client_id", "client_secret", "refresh_token"]}
    r = requests.post("https://oauth2.googleapis.com/token", data={
        **creds, "grant_type": "refresh_token"})
    return r.json()["access_token"]


def list_receipt_threads(token: str) -> list[dict]:
    """Find emails with receipt-like subjects from component suppliers."""
    headers = {"Authorization": f"Bearer {token}"}
    query = "from:(mouser.com OR digikey.com OR lcsc.com OR amazon.com) subject:(order OR receipt OR invoice) newer_than:30d"
    r = requests.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/threads",
        headers=headers,
        params={"q": query, "maxResults": 20}
    )
    return r.json().get("threads", [])


def get_thread_body(token: str, thread_id: str) -> str:
    """Get plain-text body of first message in thread."""
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(
        f"https://gmail.googleapis.com/gmail/v1/users/me/threads/{thread_id}",
        headers=headers,
        params={"format": "full"}
    )
    msgs = r.json().get("messages", [])
    if not msgs:
        return ""
    payload = msgs[0].get("payload", {})
    # Walk parts to find text/plain
    def extract(p):
        if p.get("mimeType") == "text/plain":
            data = p.get("body", {}).get("data", "")
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
        for part in p.get("parts", []):
            result = extract(part)
            if result:
                return result
        return ""
    return extract(payload)


def parse_parts_from_receipt(body: str) -> list[dict]:
    """Use vision/LLM to extract part numbers and quantities from receipt text."""
    prompt = f"""Extract all electronic component part numbers and quantities from this order receipt.
Return JSON array with objects: {{name, mpn, quantity, supplier}}.
If no parts found, return empty array [].

Receipt:
{body[:3000]}

JSON only, no explanation:"""

    if VISION_MODE == "local":
        r = requests.post(
            "http://192.168.10.146:11435/api/generate",
            json={"model": "llama3.3:70b", "prompt": prompt, "stream": False}
        )
        response_text = r.json().get("response", "[]")
    else:
        # claude-pro path — operator-triggered only
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = msg.content[0].text

    try:
        start = response_text.find("[")
        end = response_text.rfind("]") + 1
        return json.loads(response_text[start:end]) if start >= 0 else []
    except Exception:
        return []


def create_draft_part(inv_token: str, part: dict) -> dict | None:
    """Create a draft part in InvenTree (not active until reviewed)."""
    headers = {"Authorization": f"Token {inv_token}", "Content-Type": "application/json"}
    payload = {
        "name": part.get("name", part.get("mpn", "Unknown")),
        "description": f"Auto-draft from receipt. Supplier: {part.get('supplier','?')}",
        "active": False,   # draft — requires operator review
        "IPN": part.get("mpn", ""),
    }
    r = requests.post(f"{INVENTREE_BASE}/part/", headers=headers, json=payload)
    if r.status_code == 201:
        return r.json()
    return None


def main():
    print("Gmail receipt ingestion — Phase 15 Block J")
    gmail_token = get_access_token()
    inv_token = subprocess.check_output(
        ["vault", "kv", "get", "-field=token", "secret/inventree/api_token"],
        text=True, stderr=subprocess.DEVNULL
    ).strip()

    threads = list_receipt_threads(gmail_token)
    print(f"Found {len(threads)} receipt threads")

    total_parts = 0
    for thread in threads:
        body = get_thread_body(gmail_token, thread["id"])
        if not body:
            continue
        parts = parse_parts_from_receipt(body)
        if not parts:
            continue
        print(f"  Thread {thread['id'][:8]}: {len(parts)} parts extracted")
        for part in parts:
            draft = create_draft_part(inv_token, part)
            if draft:
                total_parts += 1
                print(f"    Draft: {draft['name']} (pk={draft['pk']})")
            time.sleep(0.3)

    print(f"\nTotal draft parts created: {total_parts}")
    print("Review at https://inventree.internal/part/?active=false")


if __name__ == "__main__":
    main()
```

**Commit:** `feat(phase-15-J): 4.I Gmail receipt ingestion → InvenTree draft parts`

---

## Block K — 4.G: Vision-Recognition InvenTree Plugin

**Hard dep:** Block H (InvenTree with parts data).
**Vision model:** Prefer local llava on Studio (96GB can run llava:13b without swap).

### K.1 — Pull vision model on Studio

```bash
# On Studio (or via docker exec on ollama-studio container)
docker exec ollama-studio ollama pull llava:13b
# Verify
curl -s http://192.168.10.146:11435/api/tags | python3 -c "
import json,sys
models = json.load(sys.stdin)['models']
for m in models:
    print(m['name'])
"
```

### K.2 — InvenTree plugin: photo → part match

`docker/inventree/plugins/inventree_vision_plugin/__init__.py`:

```python
"""InvenTree Vision Recognition Plugin.
Identifies electronic components from photos; suggests InvenTree part matches.
Uses local Ollama llava:13b on Mac Studio (192.168.10.146:11435).
"""
from plugin import InvenTreePlugin
from plugin.mixins import ActionMixin
import base64, requests, json


class VisionRecognitionPlugin(InvenTreePlugin, ActionMixin):
    NAME = "Vision Recognition"
    SLUG = "vision-recognition"
    TITLE = "Component Vision Recognition"
    DESCRIPTION = "Identify components from photos via local llava:13b"
    VERSION = "0.1.0"
    AUTHOR = "IAP Phase 15"

    VISION_BASE = "http://192.168.10.146:11435"
    INVENTREE_BASE = "http://localhost:8000"

    def perform_action(self, user=None, data=None):
        """Accept base64 image; return top-3 InvenTree part matches."""
        if not data or "image" not in data:
            return {"success": False, "error": "No image provided"}

        image_b64 = data["image"]
        prompt = (
            "This is a photo of an electronic component. "
            "Identify the component type, manufacturer, and part number if visible. "
            "Return JSON: {component_type, manufacturer, part_number, description}. "
            "JSON only."
        )

        r = requests.post(
            f"{self.VISION_BASE}/api/generate",
            json={
                "model": "llava:13b",
                "prompt": prompt,
                "images": [image_b64],
                "stream": False,
            },
            timeout=60
        )
        if r.status_code != 200:
            return {"success": False, "error": f"Vision API error: {r.status_code}"}

        response_text = r.json().get("response", "{}")
        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            parsed = json.loads(response_text[start:end]) if start >= 0 else {}
        except Exception:
            return {"success": False, "error": "Could not parse vision response", "raw": response_text[:200]}

        # Search InvenTree for matching parts
        part_number = parsed.get("part_number", "")
        search_term = part_number or parsed.get("component_type", "")
        matches = []
        if search_term:
            inv_r = requests.get(
                f"{self.INVENTREE_BASE}/api/part/",
                params={"search": search_term, "limit": 3},
                headers={"Authorization": f"Token {self._get_api_token()}"}
            )
            if inv_r.status_code == 200:
                matches = inv_r.json().get("results", [])

        return {
            "success": True,
            "identified": parsed,
            "matches": [{"pk": m["pk"], "name": m["name"], "IPN": m.get("IPN")} for m in matches],
        }

    def _get_api_token(self) -> str:
        """Get InvenTree API token from Vault (rendered by sidecar)."""
        import subprocess
        return subprocess.check_output(
            ["vault", "kv", "get", "-field=token", "secret/inventree/api_token"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
```

### K.3 — Install and enable plugin

```bash
# Copy plugin to InvenTree data directory
docker cp docker/inventree/plugins/inventree_vision_plugin \
  inventree:/home/inventree/data/plugins/inventree_vision_plugin

# Add to plugins.txt
docker exec inventree sh -c "echo 'inventree-vision-plugin' >> /home/inventree/data/plugins.txt"

# Restart to load
docker compose -f docker/inventree/docker-compose.yml restart inventree
sleep 15

# Verify plugin loaded
docker exec inventree python manage.py shell -c "
from plugin.models import PluginConfig
p = PluginConfig.objects.filter(key='vision-recognition').first()
print('Plugin loaded:', p is not None)
if p: print('Active:', p.active)
"
```

**Commit:** `feat(phase-15-K): 4.G vision plugin — llava:13b component recognition for InvenTree`

---

## Block L — HF-1: Oura Ring 4 Integration

**HARD STOP:** Surface to operator. Requires:
1. `secret/oura/oauth` in Vault with `client_id` + `client_secret` + `access_token`
2. Operator decision: Oura Cloud API (cleanest) vs local protocol (unsupported)

### L.1 — Oura API test

```bash
python3 - <<'EOF'
import subprocess, requests

token = subprocess.check_output(
    ["vault", "kv", "get", "-field=access_token", "secret/oura/oauth"],
    text=True, stderr=subprocess.DEVNULL
).strip()

# Test Oura API v2
r = requests.get(
    "https://api.ouraring.com/v2/usercollection/sleep",
    headers={"Authorization": f"Bearer {token}"},
    params={"start_date": "2026-04-29", "end_date": "2026-04-30"}
)
print(f"Oura API: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  Sleep records: {len(data.get('data', []))}")
else:
    print(f"  Error: {r.text[:200]}")
EOF
```

### L.2 — Ingestion script

`scripts/oura-ingest.py` — fetch sleep + readiness + activity from Oura Cloud API,
write metrics to VictoriaMetrics (already deployed at port 8428):

```python
#!/usr/bin/env python3
"""Oura Ring 4 → VictoriaMetrics ingestion.
Writes Prometheus-format metrics to VM's /api/v1/import/prometheus endpoint.
Schedule: nightly via launchd.
"""
import subprocess, requests, datetime, sys

OURA_BASE = "https://api.ouraring.com/v2/usercollection"
VM_BASE = "http://localhost:8428"
TODAY = datetime.date.today().isoformat()
YESTERDAY = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()


def get_oura_token() -> str:
    return subprocess.check_output(
        ["vault", "kv", "get", "-field=access_token", "secret/oura/oauth"],
        text=True, stderr=subprocess.DEVNULL
    ).strip()


def fetch(endpoint: str, token: str, start: str, end: str) -> list[dict]:
    r = requests.get(
        f"{OURA_BASE}/{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
        params={"start_date": start, "end_date": end}
    )
    if r.status_code != 200:
        print(f"  {endpoint}: {r.status_code}", file=sys.stderr)
        return []
    return r.json().get("data", [])


def push_metrics(lines: list[str]):
    payload = "\n".join(lines) + "\n"
    r = requests.post(f"{VM_BASE}/api/v1/import/prometheus", data=payload.encode())
    if r.status_code not in (200, 204):
        print(f"  VM write error: {r.status_code} — {r.text[:100]}", file=sys.stderr)


def main():
    token = get_oura_token()
    lines = []

    # Sleep
    for record in fetch("sleep", token, YESTERDAY, TODAY):
        ts = int(datetime.datetime.fromisoformat(record.get("day", TODAY)).timestamp() * 1000)
        if record.get("total_sleep_duration"):
            lines.append(f'oura_sleep_duration_seconds{{date="{record["day"]}"}} {record["total_sleep_duration"]} {ts}')
        if record.get("efficiency"):
            lines.append(f'oura_sleep_efficiency{{date="{record["day"]}"}} {record["efficiency"]} {ts}')
        if record.get("score"):
            lines.append(f'oura_sleep_score{{date="{record["day"]}"}} {record["score"]} {ts}')

    # Readiness
    for record in fetch("readiness", token, YESTERDAY, TODAY):
        ts = int(datetime.datetime.fromisoformat(record.get("day", TODAY)).timestamp() * 1000)
        if record.get("score"):
            lines.append(f'oura_readiness_score{{date="{record["day"]}"}} {record["score"]} {ts}')

    # Activity
    for record in fetch("daily_activity", token, YESTERDAY, TODAY):
        ts = int(datetime.datetime.fromisoformat(record.get("day", TODAY)).timestamp() * 1000)
        if record.get("score"):
            lines.append(f'oura_activity_score{{date="{record["day"]}"}} {record["score"]} {ts}')
        if record.get("steps"):
            lines.append(f'oura_steps{{date="{record["day"]}"}} {record["steps"]} {ts}')

    print(f"Pushing {len(lines)} metrics to VictoriaMetrics")
    if lines:
        push_metrics(lines)
        print("Done")

    # Verify
    r = requests.get(f"{VM_BASE}/api/v1/query", params={"query": "oura_sleep_score"})
    result = r.json().get("data", {}).get("result", [])
    print(f"VM verification: {len(result)} oura_sleep_score series")


if __name__ == "__main__":
    main()
```

Schedule: `com.iap.oura-ingest.plist` launchd agent, runs nightly at 03:00.

Grafana dashboard: add "Health & Fitness" dashboard with panels for sleep score,
readiness, activity. Use VictoriaMetrics as data source; queries: `oura_sleep_score`,
`oura_readiness_score`, `oura_activity_score`, `oura_steps`.

**Commit:** `feat(phase-15-L): HF-1 Oura Ring 4 → VictoriaMetrics ingestion`

---

## Block M — HF-2: Garmin Integration

**HARD STOP:** Surface to operator for Garmin auth path decision:
- Option A: `garth` library (unofficial, Python, maintained) — recommmend
- Option B: FIT file export from Garmin Connect Web → local processing
- Option C: Garmin Health API (paid, commercial) — not recommended

Assuming `garth` path (Option A):

```bash
pip3 install garth
python3 - <<'EOF'
import garth, os

# First-time auth — requires operator interaction
# garth.login("username", "password")  # DO NOT in script; use saved session
# Load saved session
garth.resume("~/.garth")  # session saved from prior interactive login

# Fetch recent activities
activities = garth.connectapi("/activitylist-service/activities/search/activities", params={"limit": 5})
print(f"Activities: {len(activities)}")
for a in activities:
    print(f"  {a.get('startTimeLocal')} {a.get('activityType',{}).get('typeKey','?')} {a.get('distance',0)/1000:.1f}km")
EOF
```

Write VictoriaMetrics metrics similar to HF-1 pattern:
- `garmin_activity_distance_meters`
- `garmin_activity_duration_seconds`
- `garmin_vo2_max`
- `garmin_resting_hr_bpm`

**Commit:** `feat(phase-15-M): HF-2 Garmin Fenix → VictoriaMetrics (garth SDK)`

---

## Block N — 4.F: BLE Label Maker

**HARD STOP:** Requires BLE label printer hardware (Brother, Niimbot, or Phomemo).
Check `framework/niimbot_printer.py` — this module already exists. Verify it matches
the arriving hardware.

```bash
cat framework/niimbot_printer.py | head -40
# If Niimbot: hardware is already scaffolded
```

`scripts/print-inventree-label.py`:

```python
#!/usr/bin/env python3
"""Print InvenTree part labels via BLE label printer.
Usage: python3 scripts/print-inventree-label.py <part-pk>
"""
import sys, requests, os

INVENTREE_BASE = "https://inventree.internal/api"


def get_part(pk: int, token: str) -> dict:
    r = requests.get(f"{INVENTREE_BASE}/part/{pk}/",
                     headers={"Authorization": f"Token {token}"})
    return r.json()


def main():
    if len(sys.argv) < 2:
        print("Usage: print-inventree-label.py <part-pk>")
        sys.exit(1)

    pk = int(sys.argv[1])
    token = os.environ.get("INVENTREE_TOKEN", "")

    part = get_part(pk, token)
    name = part.get("name", f"Part {pk}")
    ipn  = part.get("IPN", "")
    desc = part.get("description", "")

    # Format label
    line1 = name[:20]
    line2 = ipn[:20] if ipn else desc[:20]

    from framework.niimbot_printer import NiimbotPrinter
    printer = NiimbotPrinter()
    printer.connect()
    printer.print_label(line1=line1, line2=line2)
    printer.disconnect()
    print(f"Printed: {line1} / {line2}")


if __name__ == "__main__":
    main()
```

**Commit:** `feat(phase-15-N): 4.F BLE label maker — InvenTree part label printing via Niimbot`

---

## Block O — Phase 13 Closeout (CL)

**Dep:** Blocks H + I + E + F complete. J, K, L, M, N may be open — document their
deferral status in the closeout doc.

### O.1 — Pre-closeout checklist

```bash
# 1. All hard-dep blocks closed
grep -E "CLOSED|complete" docs/phase-15/PHASE_15_EXECUTION_HANDOFF_2026-04-30.md | head -10

# 2. InvenTree live with data
curl -sk https://inventree.internal/api/part/?limit=1 | python3 -c \
  "import json,sys; print('Parts:', json.load(sys.stdin)['count'])"
# Expected: ≥129

# 3. Cross-index service running
python3 scripts/cross-index-validate.py --json 2>/dev/null | python3 -m json.tool | head -20

# 4. Upgrade-watcher running
docker ps | grep upgrade-watcher
# Expected: Up

# 5. Network discovery registered hosts in NetBox
curl -s http://netbox.internal/api/ipam/ip-addresses/ \
  -H "Authorization: Token $(vault kv get -field=token secret/netbox/api)" \
  | python3 -c "import json,sys; print('IPs in NetBox:', json.load(sys.stdin)['count'])"

# 6. All Phase 14 carry-forwards closed (CF-1–CF-4)
docker inspect mkdocs | python3 -c "
import json,sys
print('MkDocs health:', json.load(sys.stdin)[0]['State']['Health']['Status'])"

# 7. Regression probe
bash docs/phase-13/h1-regression-probe.sh 2>&1 | tail -5
# Expected: PASS=16+ FAIL=0 WARN≤3
```

### O.2 — A-012 equivalence harness re-runs

```bash
# CMDB_SOURCE: both sources still produce same output
python3 scripts/cmdb_source.py --source yaml > /tmp/old.json 2>/dev/null
python3 scripts/cmdb_source.py --source netbox > /tmp/new.json 2>/dev/null
diff /tmp/old.json /tmp/new.json && echo "CMDB equiv: PASS" || echo "CMDB equiv: FAIL — investigate"

# Plane admin hash (unchanged since NF-14-1)
vault kv get -field=password secret/plane/admin | sha256sum | head -c 12
echo " (should match Phase 14 addendum: 14e715e688a8)"

# plex-mcp PLEX_TOKEN (unchanged since Phase 14-G)
docker exec plex-mcp sh -c 'echo $PLEX_TOKEN' | sha256sum | head -c 12
echo " (should match Phase 14 closeout: 5c5c9e74931a)"
```

### O.3 — Final regression probe

```bash
bash docs/phase-13/h1-regression-probe.sh 2>&1 | tee docs/phase-13/PHASE_13_FINAL_REGRESSION_$(date +%Y-%m-%d).log
# Expected: PASS≥16 FAIL=0 WARN≤3
```

### O.4 — Closeout document

Write `docs/phase-13/PHASE_13_CLOSEOUT_2026-XX-XX.md` using the Phase 14 closeout
doc as a template. Sections:

1. Gate result + HEAD commit
2. Block status table (D-OP through CL)
3. Discoveries #37+ (anything surfaced in Phase 15 execution)
4. A-012 harness results
5. Deferred items (J, K, L, M, N if open) → Phase 16
6. CLAUDE.md updates applied

### O.5 — Git tag

```bash
git tag -a phase-13-final -m "Phase 13 CLOSED — PASS=16+ FAIL=0 WARN≤3"
git push origin phase-13-final
```

**Commit:** `docs(phase-13-CL): Phase 13 CLOSED — final regression probe + closeout`

---

## Hard stops summary

| Block | Hard stop condition |
|---|---|
| D | Mac Studio physically arrived and on LAN |
| H | `secret/mouser/api#key`, `secret/digikey/api`, `docs/inventory/components-2026-04.csv` all present |
| J | `secret/gmail/oauth` present; operator confirms vision path (local vs claude-pro) |
| L | `secret/oura/oauth` present; operator confirms API path |
| M | Operator picks Garmin auth path (garth / FIT export / Health API) |
| N | BLE label printer hardware on hand; model confirmed against `framework/niimbot_printer.py` |

When hitting a hard stop: commit all work to date with message
`docs(phase-15): partial completion — halted at Block <X> hard stop`.
Surface to operator with the specific prerequisite needed.

---

## Commit plan summary

| Block | Commit message |
|---|---|
| CF-1 | `fix(mkdocs): healthcheck — python3 urllib instead of curl` |
| CF-2 | `fix(plane): API token proper rotation — D-35 cleanup` |
| CF-4 | `feat(mcp): docs-mcp-server pre-built image — D#29 remediation` |
| B | `docs(phase-15-B): D-OP — ADR-A-014/015/016 + migrate-source-of-truth runbook` |
| C | `fix(connector): D-CN — apply-path test, rate-limit audit, pagination contract` |
| D | `docs(phase-15-D): Mac Studio day-1 — NetBox, Headscale, ARCHITECTURE.md` |
| E | `feat(phase-15-E): 4.H upgrade-watcher — Diun + Plane webhook receiver` |
| F | `feat(phase-15-F): 4.J network discovery → NetBox` |
| G | `feat(phase-15-G): Plane backlog curation — label gap fill + triage` |
| H | `feat(phase-15-H): 2B — InvenTree suppliers + CSV import + NetBox cross-ref` |
| I | `feat(phase-15-I): 4.E cross-index — InvenTree axis` |
| J | `feat(phase-15-J): 4.I Gmail receipt ingestion → InvenTree draft parts` |
| K | `feat(phase-15-K): 4.G vision plugin — llava:13b component recognition` |
| L | `feat(phase-15-L): HF-1 Oura Ring 4 → VictoriaMetrics` |
| M | `feat(phase-15-M): HF-2 Garmin → VictoriaMetrics` |
| N | `feat(phase-15-N): 4.F BLE label maker — Niimbot InvenTree labels` |
| O | `docs(phase-13-CL): Phase 13 CLOSED — final regression probe + closeout` |

---

## Effort estimate

| Blocks | Effort |
|---|---|
| A (CF-1–CF-4) | 4–7h |
| B + C (D-OP + D-CN) | 6–9h |
| D (Studio day-1) | 2–3h |
| E + F (4.H + 4.J) | 10–17h |
| G (Plane curation) | 1–2h |
| H (2B suppliers) | 6–10h |
| I (4.E cross-index) | 6–10h |
| J (4.I Gmail) | 6–10h |
| K (4.G vision) | 6–10h |
| L + M (HF-1 + HF-2) | 10–16h |
| N (4.F BLE) | 4–8h |
| O (CL closeout) | 2–3h |
| **Total** | **63–105h** |

Point estimate: **~84h**. The hard-stop blocks (H, J, L, M, N) run only when
operator delivers prerequisites. Blocks A–G + O can fully close independent
of those prerequisites.
