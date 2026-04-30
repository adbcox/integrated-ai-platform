# Phase 14 — Complete Execution Handoff

**Date:** 2026-04-30
**Status at handoff:** D-DOC gate PASSED (`phase-14-doc-final` PASS=15 FAIL=0 WARN=3,
commit `a6d50c2`). Three D-DOC sub-tasks deferred (NF-14-2 web auth, Plane backlog
curation, NF-14-1 admin rotation). All other D-DOC deliverables complete.
**Baseline for all remaining gates:** PASS=15 FAIL=0 WARN=3.
**HEAD at handoff:** `a6d50c2`

This document is a single self-contained execution handoff for the full remaining
Phase 14 arc. Read it once, then execute top to bottom. Surface at CL-14 only.

---

## Context files — read before beginning any work

```
docs/phase-14/PHASE_14_CAMPAIGN_PLAN_2026-04-29.md      (campaign plan, all blocks)
docs/phase-14/PHASE_14_BLOCK_D_DOC_CLOSEOUT_2026-04-29.md  (D-DOC state; open items)
docs/canonical-patterns/plane-connector-usage.md        (mandatory for all Plane writes)
docs/runbooks/operating-model.md                        (IV&V doctrine)
docs/DECISION_REGISTER.md                               (13 ADRs)
CLAUDE.md                                               (platform rules, non-negotiables)
```

---

## Part 1 — D-DOC post-gate addendum: NF-14-2 + NF-14-1 + Plane curation

**Scope:** Three sub-tasks deferred from D-DOC. Close them as an addendum to
`PHASE_14_BLOCK_D_DOC_CLOSEOUT_2026-04-29.md` rather than opening a new block.
**Gate:** No new regression probe required — these are sub-tasks within the D-DOC
gate boundary. Record sub-task completion in the addendum, not a new gate ID.
**Estimate:** 1–2h (NF-14-2) + 0.75–1h (NF-14-1) + 1–1.5h (Plane curation) = **3–5h total**.

### 1.1 NF-14-2 — Plane CE web auth (Full IV&V, A-011)

**Diagnosis first.** "No authentication methods available" on the Plane login page
is almost always one of three root causes in Plane CE:

1. **Proxy/CSRF issue** — Plane's Next.js frontend sends auth requests to
   `NEXT_PUBLIC_API_BASE_URL`. If that URL differs from what the reverse proxy
   presents, the CSRF token is rejected and the auth method list comes back empty.
   Check: does `docker inspect docker-plane-web-1` show
   `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`? The correct value for a
   Caddy-proxied setup is the *public* base URL: `https://plane.internal`.
2. **EMAIL_BACKEND not configured** — Plane CE requires a working SMTP backend to
   serve magic-link auth. If `EMAIL_HOST` is unset, the magic-link backend silently
   disables itself.
3. **`ENABLE_SIGNUP` / `IS_EMAIL_VERIFIED` flags** — some Plane CE versions gate the
   login form on these env vars being explicitly set.

**Diagnostic procedure (run on Mac Mini):**

```bash
# Step 1: check current NEXT_PUBLIC_API_BASE_URL
docker inspect docker-plane-web-1 \
  --format '{{range .Config.Env}}{{println .}}{{end}}' | grep NEXT_PUBLIC

# Step 2: check plane-api env for EMAIL_ vars
docker inspect docker-plane-api-1 \
  --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E "EMAIL|SMTP|ENABLE"

# Step 3: hit the auth methods API directly (bypasses proxy)
curl -s http://localhost:8000/auth/social-auth/ 2>/dev/null | head -200 || \
  curl -s http://localhost:8000/api/instances/ | python3 -m json.tool | grep -A5 auth

# Step 4: check Plane instance config
docker exec docker-plane-api-1 \
  python manage.py shell -c \
  "from plane.settings.common import *; print('EMAIL_HOST:', EMAIL_HOST)"
```

**Resolution path A — NEXT_PUBLIC_API_BASE_URL fix (most likely):**

If `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` and the proxy serves
`https://plane.internal`, update the plane-web compose env to:

```yaml
environment:
  NEXT_PUBLIC_API_BASE_URL: "https://plane.internal"
```

The plane stack lives in `~/control-center-stack/stacks/plane/` (out-of-repo).
Per CLAUDE.md: capture pre/post snapshot in this closeout addendum before
modifying. Then:

```bash
cd ~/control-center-stack/stacks/plane
docker compose up -d plane-web
# Wait ~30s for Next.js rebuild
curl -s https://plane.internal/auth/ | grep -i "auth\|login\|method"
```

**Resolution path B — enable local (email+password) auth backend:**

Plane CE ≥0.22 ships with local email/password auth disabled by default. Enable it:

```bash
docker exec docker-plane-api-1 \
  python manage.py shell -c "
from plane.db.models import Instance
inst = Instance.objects.first()
print('current config:', inst.config)
# If config is missing is_email_password_login_enabled:
inst.config['is_email_password_login_enabled'] = True
inst.save()
print('updated config:', inst.config)
"
```

Verify: `curl -s https://plane.internal/auth/` should now show the email/password
form, or the API endpoint `/api/instances/` should return the updated flag.

**Resolution path C — both:**

Apply A first (proxy URL), verify. If still broken, apply B (enable local auth),
verify. The two are independent fixes.

**Exit gate for NF-14-2:**
- [ ] Admin can reach `https://plane.internal/` in a browser and see a login form.
- [ ] Login with `admin@local.dev` succeeds (even with the current weak password —
  NF-14-1 rotates it immediately after).
- [ ] Author `docs/runbooks/plane-web-auth.md`: document what was broken, which
  path resolved it, and the ongoing auth backend config.
- [ ] Commit: runbook + any compose/env change (snapshot out-of-repo change in commit
  message body if plane-web compose was touched).

### 1.2 NF-14-1 — Plane admin password rotation (Full IV&V, A-011 + A-012)

**Prereq:** NF-14-2 exit gate passed (admin login works).

**Vault path decision (Q-P14-2 default):** `secret/plane/admin`.

```bash
# Step 1: generate a strong password (32 chars, no URL-unsafe chars)
NEW_PASS=$(LC_ALL=C tr -dc 'A-Za-z0-9!@#%^&*()-_=+' < /dev/urandom | head -c 32)
echo "Hash check: $(echo -n "$NEW_PASS" | sha256sum | cut -c1-12)"
# DO NOT print NEW_PASS — record only the hash

# Step 2: write to Vault (hash-only log)
vault kv put secret/plane/admin \
  username="admin@local.dev" \
  password="$NEW_PASS"
echo "Vault write hash: $(vault kv get -field=password secret/plane/admin | sha256sum | cut -c1-12)"

# Step 3: rotate via Django shell (reads from Vault — do not paste plaintext)
NEW_PASS_FROM_VAULT=$(vault kv get -field=password secret/plane/admin)
docker exec docker-plane-api-1 \
  python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(email='admin@local.dev')
u.set_password('$(echo $NEW_PASS_FROM_VAULT)')
u.save()
print('Password updated. User pk:', u.pk)
"
unset NEW_PASS NEW_PASS_FROM_VAULT

# Step 4: verify login works with new password
# Use browser: https://plane.internal/ → login with admin@local.dev + new cred
# OR via API:
curl -s -X POST https://plane.internal/auth/sign-in/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@local.dev\",\"password\":\"$(vault kv get -field=password secret/plane/admin)\"}" \
  | python3 -m json.tool | grep -E "token|error|detail"
# Unset any shell vars holding the credential immediately after
```

**A-012 equivalence harness:** Verify the hash of the Vault-stored password
matches a fresh read after the rotation:

```bash
# Read-back hash (not value)
vault kv get -field=password secret/plane/admin | sha256sum | cut -c1-12
# Must match the hash from Step 2 above
```

**Plaintext purge:** The `plane_deployment.md` memory file at
`/Users/admin/.claude/projects/-Users-admin-repos-integrated-ai-platform/memory/plane_deployment.md`
contains `admin@local.dev / Admin1234!`. After rotation, edit that file to replace
the plaintext password with `[rotated — see secret/plane/admin; hash only]`.

**Exit gate for NF-14-1:**
- [ ] Vault at `secret/plane/admin` has `username` and `password` (hash logged, value never displayed).
- [ ] Django admin login works with new credential.
- [ ] `Admin1234!` is no longer present in any tracked or memory file (`grep -r "Admin1234" ~/.claude/ docs/`).
- [ ] Vault write confirmed by read-back hash equality.
- [ ] Commit: memory file update + hash-only log entry in this addendum.

### 1.3 Plane backlog curation (Full IV&V, A-011)

**MANDATORY prerequisites before bulk run:**
- Use `framework/plane_connector.py` — no raw HTTP.
- Import `RateLimitError` alongside `PlaneAPI` (canonical-pattern §1).
- Catch `RateLimitError` BEFORE `except Exception` (canonical-pattern §2).
- First-batch-verify (canonical-pattern §4): write one label, read it back, confirm
  before proceeding.
- Use `_with_429_retry` from `scripts/backfill-plane-labels.py` for the bulk loop.

**Targets:**
- Apply 64 existing Plane labels to ~1100 issues via prefix-mapping.
- Re-triage: reduce urgent-priority count from 44 to <10.
- Close ~88 issues already in Done state.

**Execution pattern:**

```python
# Reference implementation skeleton — use backfill-plane-labels.py as the basis
from framework.plane_connector import PlaneAPI, RateLimitError
import time

api = PlaneAPI()

# First-batch-verify: label one issue, read it back
issue, created = api.upsert_issue(external_id="VERIFY-001", ...)
if not api.verify_issue_field(issue["id"], "labels", [expected_label_uuid]):
    raise SystemExit(2)  # abort — labels not landing

# Bulk loop with retry
for item in items:
    try:
        api.upsert_issue(...)
        time.sleep(1.5)  # pace: 60 req/min limit
    except RateLimitError as exc:
        time.sleep(60)
        # retry once
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
```

**Exit gate for Plane curation:**
- [ ] ≥95% of ~1100 issues have at least one label applied.
- [ ] Urgent-priority count ≤10.
- [ ] ~88 Done-state issues closed.
- [ ] Zero RateLimitError silently swallowed (check logs).
- [ ] Curation script committed to `scripts/curate-plane-backlog.py`.

### 1.4 Addendum closeout commit

After all three sub-tasks pass their exit gates:

Append an `## Addendum — D-DOC post-gate (2026-04-30)` section to
`docs/phase-14/PHASE_14_BLOCK_D_DOC_CLOSEOUT_2026-04-29.md` recording:
- NF-14-2 resolution path (which of A/B/C resolved it), commit hash.
- NF-14-1 Vault hash (not value), rotation commit hash, memory-file purge commit.
- Plane curation: final issue count, label coverage %, commit hash.
- No new regression probe — these are sub-tasks within the D-DOC gate boundary.

Commit message: `docs(phase-14): D-DOC addendum — NF-14-2/NF-14-1 closed + Plane curation complete`

**D-DOC is fully closed after this commit. All remaining blocks proceed.**

---

## Part 2 — D-STR: Structurizr Lite

**Estimate:** 2–4h. **Gate:** Full IV&V (A-011). **Pattern class:** Novel container +
Caddy route — mid-buffer (+35%).

### 2.1 Scope

Structurizr Lite is a self-hosted C4-model workspace server. It serves a single
`workspace.dsl` file via a web UI, providing the visual topology layer that closes
state-anchoring gap (g) alongside MkDocs.

### 2.2 Execution

**Step 1 — Pre-deploy audit (B.1):**

```bash
# Check port availability: Structurizr Lite default is 8080 — likely taken
# Use 8088 (next after InvenTree's 8087)
ss -tlnp | grep -E "8080|8088|8089"

# Confirm Structurizr Lite image
docker pull structurizr/lite:latest
docker inspect structurizr/lite:latest --format '{{.RepoDigests}}'
# Pin to the digest returned above
```

**Step 2 — Compose file:**

Create `docker/structurizr/docker-compose.yml`:

```yaml
services:
  structurizr:
    image: structurizr/lite:latest   # replace with pinned digest
    container_name: structurizr
    restart: unless-stopped
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    read_only: false          # Structurizr writes workspace state to /usr/local/structurizr
    mem_limit: 512m
    ports:
      - "127.0.0.1:8088:8080"
    volumes:
      - ./workspace:/usr/local/structurizr
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 30s
      timeout: 5s
      retries: 3
```

Note: Structurizr Lite stores its workspace in the bind-mounted volume, not
Vault — it has no credentials to protect. No sidecar needed.

**Step 3 — Caddy route** (append to `docker/caddy/Caddyfile`):

```caddyfile
structurizr.internal {
    import access_log
    reverse_proxy structurizr:8080
}
```

Reload Caddy: `docker exec caddy caddy reload --config /etc/caddy/Caddyfile`

**Step 4 — Initial workspace DSL:**

Create `docker/structurizr/workspace/workspace.dsl` with a C4 System Context
and Container diagram reflecting the Phase 13 platform. Minimum viable first
commit — the workspace grows over time. Start with:

```dsl
workspace "Integrated AI Platform" "Phase 13 baseline" {
    model {
        user = person "Operator"
        platform = softwareSystem "AI Platform" {
            vault = container "Vault" "Secret store" "HashiCorp Vault"
            netbox = container "NetBox" "CMDB" "NetBox CE"
            plane = container "Plane" "Roadmap" "Plane CE"
            caddy = container "Caddy" "Reverse proxy + TLS" "Caddy"
            grafana = container "Grafana" "Observability" "Grafana OSS"
            inventree = container "InvenTree" "Parts CMDB" "InvenTree"
        }
        user -> caddy "accesses via *.internal"
        caddy -> vault
        caddy -> netbox
        caddy -> plane
        caddy -> grafana
        caddy -> inventree
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

Commit workspace to `docker/structurizr/workspace/workspace.dsl`.

**Step 5 — Validation:**

```bash
docker compose -f docker/structurizr/docker-compose.yml up -d
docker ps | grep structurizr  # must be Up, healthy within 60s
curl -s http://localhost:8088/ | grep -i "structurizr\|workspace"
curl -s https://structurizr.internal/ -o /dev/null -w "%{http_code}"  # expect 200
```

### 2.3 Exit gate

- [ ] `structurizr` container running, healthy, `cap_drop:[ALL]`.
- [ ] `https://structurizr.internal/` returns 200 via Caddy.
- [ ] `workspace.dsl` renders System Context and Container diagrams in browser.
- [ ] Compose file committed to `docker/structurizr/docker-compose.yml`.
- [ ] Caddy route committed.

**Commit:** `feat(phase-14-D-STR): Structurizr Lite — C4 workspace for platform topology`

---

## Part 3 — D-MKD: MkDocs + Material

**Estimate:** 3–5h. **Gate:** Full IV&V (A-011). **Pattern class:** Novel container +
Caddy route + config file — mid-buffer (+35%).

### 3.1 Scope

MkDocs with the Material theme publishes the entire `docs/` tree as a searchable
internal site at `docs.internal`. Complements Structurizr (prose+navigation vs.
visual diagrams). Both close state-anchoring gap (g).

### 3.2 Execution

**Step 1 — Verify ADR filename edge case before anything else:**

```bash
ls docs/adr/ | grep A-007
# Expect: ADR-A-007-media-sync-syncthing.md
# mkdocs nav will need the full filename, not just ADR-A-007
```

**Step 2 — mkdocs.yml** (commit at repo root):

```yaml
site_name: Integrated AI Platform Docs
site_url: https://docs.internal
docs_dir: docs
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - search.suggest
    - search.highlight
  palette:
    scheme: slate

nav:
  - Home: index.md
  - Architecture:
    - Overview: ARCHITECTURE.md
    - Dependency Graph: architecture/dependency-graph.md
    - MCP Servers: architecture/mcp-server-architecture.md
    - Portability: architecture/portability.md
  - ADRs:
    - Index: adr/README.md
    - ADR-A-001: adr/ADR-A-001.md
    - ADR-A-002: adr/ADR-A-002.md
    - ADR-A-003: adr/ADR-A-003.md
    - ADR-A-004: adr/ADR-A-004.md
    - ADR-A-005: adr/ADR-A-005.md
    - ADR-A-006: adr/ADR-A-006.md
    - ADR-A-007 (Syncthing): adr/ADR-A-007-media-sync-syncthing.md
    - ADR-A-008: adr/ADR-A-008.md
    - ADR-A-009: adr/ADR-A-009.md
    - ADR-A-010: adr/ADR-A-010-external-systems.md
    - ADR-A-011: adr/ADR-A-011-ivv-loop-pattern.md
    - ADR-A-012: adr/ADR-A-012-equivalence-harness-doctrine.md
    - ADR-A-013: adr/ADR-A-013-folded-gates-doctrine.md
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
    - Drift Detection: runbooks/drift-detection-procedure.md
    - Regression Probe Failure: runbooks/regression-probe-failure.md
    - Incident Response: runbooks/incident-response.md
    - H1 Rollback: runbooks/H1-rollback.md
    - What Changed (24h): runbooks/what-changed-last-24h.md
    - Plane Web Auth: runbooks/plane-web-auth.md
    - Operating Model: runbooks/operating-model.md
  - Decision Register: DECISION_REGISTER.md
  - Known Issues:
    - KI-004 mcp-docs-remote: known-issues/KI-004-mcp-docs-remote-startup.md
  - Canonical Patterns:
    - Plane Connector: canonical-patterns/plane-connector-usage.md

plugins:
  - search
```

Note: `docs/index.md` does not exist yet. Create it as a one-paragraph landing
page pointing to ARCHITECTURE.md and the runbooks index.

**Step 3 — Compose file** (`docker/mkdocs/docker-compose.yml`):

```yaml
services:
  mkdocs:
    image: squidfunk/mkdocs-material:latest  # pin to digest after pull
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
    command: serve --dev-addr=0.0.0.0:8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 5s
      retries: 3
```

**Step 4 — Caddy route** (append to `docker/caddy/Caddyfile`):

```caddyfile
docs.internal {
    import access_log
    reverse_proxy mkdocs:8000
}
```

**Step 5 — Validation:**

```bash
docker compose -f docker/mkdocs/docker-compose.yml up -d
docker logs mkdocs 2>&1 | tail -10  # watch for MkDocs startup, no errors
curl -s http://localhost:8089/ | grep -i "material\|mkdocs\|Integrated"
curl -s https://docs.internal/ -o /dev/null -w "%{http_code}"  # expect 200
# Verify ADR-A-007 renders correctly
curl -s https://docs.internal/adr/ADR-A-007-media-sync-syncthing/ \
  -o /dev/null -w "%{http_code}"  # expect 200, not 404
# Verify search
curl -s https://docs.internal/search/search_index.json | python3 -m json.tool | head -5
```

### 3.3 Exit gate

- [ ] `mkdocs` container running, healthy, `cap_drop:[ALL]`, `read_only:true`.
- [ ] `https://docs.internal/` returns 200 via Caddy.
- [ ] All ADR pages render (including ADR-A-007-media-sync-syncthing).
- [ ] Search index populated.
- [ ] `mkdocs.yml` and `docs/index.md` committed.

**Commit:** `feat(phase-14-D-MKD): MkDocs Material — internal docs site at docs.internal`

---

## Part 4 — D-ZBX: Zabbix Prometheus exporter

**Estimate:** 2–4h. **Gate:** Full IV&V (A-011). **Pattern class:** Novel container +
Vault path — mid-buffer (+35%).

### 4.1 Scope

Zabbix 7.4 has no native `/metrics` endpoint. A sidecar exporter reads the Zabbix
API and translates triggers/alerts/host-status to Prometheus metrics, enabling
Grafana dashboards for Zabbix alert volume and host health.

### 4.2 Execution

**Step 1 — Image selection:**

```bash
# Evaluate options:
# Option A: zabbix-prometheus-exporter (Python-based, Zabbix API v4+)
docker pull registry.gitlab.com/gitlab-org/build/cng/zabbix-exporter:latest

# Option B: mbobov/zabbix-exporter
docker pull mbobov/zabbix-exporter:latest

# Option C: write a minimal one using framework/zabbix_connector.py if it exists
ls framework/ | grep -i zabbix

# Verify image is maintained (check last layer date):
docker inspect <chosen-image> --format '{{.Metadata.LastTagTime}}'
# Use whichever was updated most recently and supports Zabbix 7.x API
```

**Step 2 — Vault path for Zabbix API token:**

```bash
# Provision Zabbix API token in Vault
# The Zabbix admin API token is used by the exporter to query trigger/host state

# First, retrieve or create a Zabbix API token (not the admin password):
# Zabbix UI → User settings → API tokens → Create token (read-only, no expiry)
# OR via API:
ZABBIX_TOKEN=$(curl -s -X POST https://zabbix.internal/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"user.login",
       "params":{"username":"Admin","password":"<admin-pass-from-vault>"},
       "id":1}' | python3 -m json.tool | grep result | awk -F'"' '{print $4}')
# Write token to Vault (hash-only log)
vault kv put secret/zabbix/exporter api_token="$ZABBIX_TOKEN"
echo "Zabbix exporter token hash: $(vault kv get -field=api_token secret/zabbix/exporter | sha256sum | cut -c1-12)"
unset ZABBIX_TOKEN
```

**Step 3 — Vault policy + AppRole:**

Create `config/vault-policies/zabbix-exporter-policy.hcl`:

```hcl
path "secret/data/zabbix/exporter" { capabilities = ["read"] }
path "secret/metadata/zabbix/exporter" { capabilities = ["list", "read"] }
```

```bash
vault policy write zabbix-exporter config/vault-policies/zabbix-exporter-policy.hcl
vault auth enable -path=approle/zabbix-exporter approle 2>/dev/null || true
vault write auth/approle/role/zabbix-exporter \
  policies=zabbix-exporter \
  secret_id_ttl=0 token_ttl=1h token_max_ttl=24h
```

**Step 4 — Compose file** (`docker/zabbix-exporter/docker-compose.yml`):

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
      - /Users/admin/.vault-approle/zabbix-exporter:/vault/approle:ro
      - zabbix-exporter-secrets:/vault/secrets
    command: ["vault", "agent", "-config=/vault/config/agent.hcl"]

  zabbix-exporter:
    image: <chosen-image>:<pinned-tag>
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
      test: ["CMD", "curl", "-f", "http://localhost:9224/metrics"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  zabbix-exporter-secrets:
    driver: local
    driver_opts: {type: tmpfs, device: tmpfs, o: size=1m}
```

**Step 5 — Grafana data source + dashboard:**

```bash
# Verify Prometheus scrapes the exporter
# Add to VictoriaMetrics/Prometheus scrape config:
# - job_name: zabbix-exporter
#   static_configs:
#     - targets: ['zabbix-exporter:9224']

# Verify metrics appear in Grafana:
curl -s http://localhost:9224/metrics | grep zabbix | head -10
```

Create a Grafana dashboard: Zabbix trigger count by severity, host status
(available/unavailable), and problem count over time. Commit the dashboard
JSON to `docker/grafana/dashboards/zabbix-overview.json`.

**Step 6 — Update CLAUDE.md:**

Remove the Zabbix Prometheus exporter entry from "Known Hardening Trade-offs"
or mark it RESOLVED with reference to the new container.

### 4.3 Exit gate

- [ ] `zabbix-exporter` container healthy, `cap_drop:[ALL]`, credentials from Vault sidecar.
- [ ] `/metrics` endpoint returns Zabbix-keyed metrics.
- [ ] Grafana dashboard renders (trigger counts, host status).
- [ ] `config/vault-policies/zabbix-exporter-policy.hcl` committed.
- [ ] CLAUDE.md trade-off entry updated.

**Commit:** `feat(phase-14-D-ZBX): Zabbix Prometheus exporter + Grafana dashboard`

---

## Part 5 — D-RST: Restic backup runbook + restore test

**Estimate:** 5–8h. **Gate:** Full IV&V on restore test (A-011 + A-012); folded on
runbook authoring. **Operator presence required** (interactive Restic auth via
AppRole, actual restore to temp dir).

### 5.1 Scope

CLAUDE.md "Backup Policy" mandates quarterly restore tests — none has been
documented. This block makes the test repeatable and verifies the backup repo is
actually healthy.

### 5.2 Execution

**Step 1 — Locate Restic repository and credentials:**

```bash
# Restic creds are in Vault at secret/backup (or similar)
vault kv list secret/  # find backup path
vault kv get secret/backup  # get RESTIC_REPOSITORY and RESTIC_PASSWORD (hash-only log)

# Source credentials for this session only
export RESTIC_REPOSITORY=$(vault kv get -field=repository secret/backup)
export RESTIC_PASSWORD=$(vault kv get -field=password secret/backup)
echo "Repo hash: $(echo -n "$RESTIC_REPOSITORY" | sha256sum | cut -c1-12)"
echo "Pass hash: $(echo -n "$RESTIC_PASSWORD" | sha256sum | cut -c1-12)"
```

**Step 2 — List snapshots and verify repo health:**

```bash
restic snapshots
restic check --read-data-subset=5%  # quick integrity check (5% sample)
# Record: snapshot count, latest snapshot ID, latest snapshot date
```

**Step 3 — Run restore test to temp dir:**

```bash
LATEST=$(restic snapshots --json | python3 -c \
  "import json,sys; snaps=json.load(sys.stdin); print(snaps[-1]['id'])")
echo "Restoring snapshot: $LATEST"

RESTORE_DIR=$(mktemp -d /tmp/restic-restore-test-XXXXXX)
restic restore "$LATEST" --target "$RESTORE_DIR" --include /vault/data
echo "Restored bytes: $(du -sh "$RESTORE_DIR" | cut -f1)"

# Verify a known Vault file is present and non-empty
ls -la "$RESTORE_DIR/vault/data/" | head -10
file "$RESTORE_DIR/vault/data/"* | head -5

# Cleanup
rm -rf "$RESTORE_DIR"
unset RESTIC_REPOSITORY RESTIC_PASSWORD
```

**Step 4 — Author/update `docs/runbooks/backup-restore.md`:**

The runbook authored in D-DOC covers the Vault restore path. This block adds
the full general-restore procedure (any service's data, not just Vault) and
verifies consistency with `vault-restore-from-backup.md`.

Runbook must include:
- How to source Restic credentials from Vault (not from a file).
- `restic snapshots` → identify target.
- `restic restore <id> --target <dir>` with `--include` for scope.
- Post-restore verification checklist.
- Quarterly test cadence reminder.

**Step 5 — Commit restore test evidence:**

Create `docs/runbooks/backup-restore-test-2026-04.md` with:
- Date, operator, snapshot ID tested.
- `restic check` output summary.
- Restored bytes and verification evidence (file list excerpt, no credential values).
- Result: PASS or FAIL.

If FAIL: **stop immediately and escalate as R-CRITICAL (R-P14-7)**. Do not continue
to D-LOG or subsequent blocks until backup integrity is confirmed.

### 5.3 Exit gate

- [ ] `restic check` passes (repo healthy).
- [ ] Restore test completed to temp dir; known Vault data file present in restore.
- [ ] `docs/runbooks/backup-restore.md` committed (full procedure).
- [ ] `docs/runbooks/backup-restore-test-2026-04.md` committed (evidence).
- [ ] Credentials never printed to terminal or committed.

**Commit:** `docs(phase-14-D-RST): Restic restore runbook + 2026-04 quarterly restore test`

---

## Part 6 — D-LOG: Loki for per-site Caddy logs

**Estimate:** 6–10h. **Gate:** Full IV&V (A-011). **Pattern class:** Novel log-shipping
infra — first Loki deployment, high-buffer (+50%).

### 6.1 Scope

Caddy 2.11.2's Prometheus output has no `host` label — per-site analysis requires
tailing the JSON access log. Loki + Promtail ships those logs to a queryable store.
This closes the CLAUDE.md "Known Hardening Trade-offs" Caddy per-site log entry.

### 6.2 Execution

**Step 1 — Port audit:**

```bash
# Loki default ports: 3100 (HTTP), 9096 (gRPC)
# Promtail default: 9080
ss -tlnp | grep -E "3100|9096|9080"
# If any are taken, adjust in configs below
```

**Step 2 — Loki config** (`docker/loki/loki-config.yaml`):

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

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

schema_config:
  configs:
    - from: 2024-01-01
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
  filesystem:
    directory: /loki/chunks

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
```

**Step 3 — Promtail config** (`docker/loki/promtail-config.yaml`):

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
      - targets:
          - localhost
        labels:
          job: caddy
          host: mac-mini
          __path__: /var/log/caddy/access.log
    pipeline_stages:
      - json:
          expressions:
            ts: ts
            request_host: request.host
            status: status
            duration: duration
            method: request.method
            uri: request.uri
            remote_ip: request.remote_ip
      - labels:
          request_host:
          status:
          method:
      - timestamp:
          source: ts
          format: Unix
```

**Step 4 — Compose file** (`docker/loki/docker-compose.yml`):

```yaml
services:
  loki:
    image: grafana/loki:2.9.0   # pin version; do not use :latest for infra
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
    command: -config.file=/etc/loki/loki-config.yaml
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3100/ready"]
      interval: 30s
      timeout: 5s
      retries: 5

  promtail:
    image: grafana/promtail:2.9.0  # match Loki version
    container_name: promtail
    restart: unless-stopped
    cap_drop: [ALL]
    cap_add: [DAC_READ_SEARCH]    # needed to read /var/log/caddy/access.log
    security_opt: [no-new-privileges:true]
    mem_limit: 128m
    volumes:
      - ./promtail-config.yaml:/etc/promtail/promtail-config.yaml:ro
      - /var/log/caddy:/var/log/caddy:ro
      - promtail-positions:/tmp
    command: -config.file=/etc/promtail/promtail-config.yaml
    depends_on:
      loki:
        condition: service_healthy

volumes:
  loki-data:
  promtail-positions:
```

Note: `cap_add: [DAC_READ_SEARCH]` for Promtail is required to read log files
outside the container's user ownership. This is the minimal cap for a read-only
log shipper — document as D#31 with rationale.

**Step 5 — Caddy route (optional):**

Only needed if you want to query Loki's HTTP API from outside the container
network. Grafana connects to Loki internally (container-to-container). Add
only if Loki direct-query is needed:

```caddyfile
loki.internal {
    import access_log
    reverse_proxy loki:3100
}
```

**Step 6 — Grafana data source:**

Add Loki as a Grafana data source (via provisioning file or UI):

```yaml
# docker/grafana/provisioning/datasources/loki.yaml
apiVersion: 1
datasources:
  - name: Loki
    type: loki
    url: http://loki:3100
    access: proxy
    isDefault: false
```

**Step 7 — Per-site dashboard:**

Create a Grafana dashboard with these panels (commit JSON to
`docker/grafana/dashboards/caddy-per-site.json`):

- **Request rate by host** — `sum by (request_host) (rate({job="caddy"}[5m]))`
- **Error rate by host** — `sum by (request_host) (rate({job="caddy",status=~"5.."}[5m]))`
- **p99 latency** (requires duration parsing from log) — `histogram_quantile(0.99, ...)`
- **Top paths by volume** — `topk(10, count by (uri) ({job="caddy"}))`

**Step 8 — Validation:**

```bash
docker compose -f docker/loki/docker-compose.yml up -d
docker logs promtail 2>&1 | tail -20  # watch for successful log tail + push
sleep 30
# Query Loki directly
curl -s 'http://localhost:3100/loki/api/v1/query_range' \
  --data-urlencode 'query={job="caddy"}' \
  --data-urlencode 'limit=5' | python3 -m json.tool | grep -c "values"
# Should return >0 log entries
```

**Step 9 — Update CLAUDE.md:**

Mark the "Caddy per-site access logs" trade-off entry as RESOLVED (Loki in
place). Add a note: `promtail uses cap_add: [DAC_READ_SEARCH]` — documented
exception, minimal for read-only log shipping.

### 6.3 Exit gate

- [ ] `loki` and `promtail` containers running, healthy, `cap_drop:[ALL]`.
- [ ] Promtail reads `/var/log/caddy/access.log` and ships to Loki.
- [ ] Loki query returns at least one Caddy log entry.
- [ ] Grafana Loki data source connected; per-site dashboard renders.
- [ ] CLAUDE.md "Known Hardening Trade-offs" updated.
- [ ] Promtail `DAC_READ_SEARCH` cap documented (D#31 in closeout).

**Commit:** `feat(phase-14-D-LOG): Loki + Promtail — per-site Caddy log analysis`

---

## Part 7 — D-XINDEX: Cross-index extension

**Estimate:** 4–8h. **Gate:** Full IV&V (A-011 + A-012 for harness). **Pattern class:**
First-contact cross-index scripting, mid-high-buffer (+40%).

**Prereq check:** Before beginning, run:

```bash
# Check Phase 13 Block 4.E status
grep -r "4.E\|Block 4.E\|cross-index" docs/phase-13/PHASE_13_INCREMENT_*CLOSEOUT* \
  2>/dev/null | grep -i "closed\|complete\|pass" | tail -5
```

If 4.E is closed, use its cross-index as the baseline. If 4.E is still open (waiting
on Mouser+DigiKey+CSV), proceed standalone using the NetBox→InvenTree→Plane links
from Increment 2A as the baseline.

### 7.1 Scope

State-anchoring gap (g): there is no machine-readable index linking ADRs ↔ Plane
tracking issues ↔ Vault secret paths. This block creates `scripts/cross-index-validate.py`
and adds a probe section to the regression probe.

### 7.2 Execution

**Step 1 — Audit current cross-index state:**

```bash
# What's already indexed?
# Plane issues with external_id (from block 4.C upsert_issue calls)
python3 -c "
from framework.plane_connector import PlaneAPI, RateLimitError
api = PlaneAPI()
issues = api.list_all_issues()
with_ext = [i for i in issues if i.get('external_id')]
print(f'Issues with external_id: {len(with_ext)} of {len(issues)}')
for i in with_ext[:5]:
    print(f'  {i[\"external_id\"]} → {i[\"name\"][:60]}')
"

# ADRs in DECISION_REGISTER.md
grep -c "ADR-A-" docs/DECISION_REGISTER.md

# Vault paths
vault kv list secret/ 2>/dev/null
```

**Step 2 — Author `scripts/cross-index-validate.py`:**

```python
#!/usr/bin/env python3
"""
Cross-index validator: ADR <-> Plane <-> Vault coherence check.

Emits a gap report. Does NOT modify any system — read-only.

Usage:
    python3 scripts/cross-index-validate.py [--json]
"""
import json
import re
import sys
from pathlib import Path
from framework.plane_connector import PlaneAPI, RateLimitError

REPO_ROOT = Path(__file__).parent.parent
DECISION_REGISTER = REPO_ROOT / "docs" / "DECISION_REGISTER.md"


def load_adrs() -> list[dict]:
    """Parse ADR IDs and titles from DECISION_REGISTER.md."""
    adrs = []
    for line in DECISION_REGISTER.read_text().splitlines():
        m = re.match(r"\|\s*\[?(ADR-A-\d+)\]?.*?\|\s*(.+?)\s*\|", line)
        if m:
            adrs.append({"id": m.group(1), "title": m.group(2).strip()})
    return adrs


def load_plane_issues_with_adr() -> dict[str, dict]:
    """Return Plane issues whose external_id starts with ADR-."""
    api = PlaneAPI()
    try:
        issues = api.list_all_issues()
    except RateLimitError as exc:
        print(f"RATE-LIMIT: {exc}", file=sys.stderr)
        sys.exit(1)
    return {
        i["external_id"]: i
        for i in issues
        if (i.get("external_id") or "").startswith("ADR-")
    }


def main():
    adrs = load_adrs()
    plane_adr_issues = load_plane_issues_with_adr()

    gaps = []
    for adr in adrs:
        adr_id = adr["id"]
        if adr_id not in plane_adr_issues:
            gaps.append({
                "type": "missing_plane_issue",
                "adr": adr_id,
                "title": adr["title"],
            })

    covered = [a["id"] for a in adrs if a["id"] in plane_adr_issues]

    report = {
        "adrs_total": len(adrs),
        "adrs_with_plane_issue": len(covered),
        "adrs_missing_plane_issue": len(gaps),
        "gaps": gaps,
        "covered": covered,
    }

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        print(f"ADRs total: {report['adrs_total']}")
        print(f"Tracked in Plane: {report['adrs_with_plane_issue']}")
        print(f"Missing Plane issue: {report['adrs_missing_plane_issue']}")
        for g in report["gaps"]:
            print(f"  GAP: {g['adr']} — {g['title']}")

    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())
```

**Step 3 — Run the validator and review gaps:**

```bash
python3 scripts/cross-index-validate.py
# Review gap list. For each ADR without a Plane issue:
# - Determine if a tracking issue should exist (most Accepted ADRs should)
# - Create stub Plane issues for those that should be tracked
```

**Step 4 — Create stub Plane issues for untracked ADRs:**

```python
from framework.plane_connector import PlaneAPI, RateLimitError
import time

api = PlaneAPI()
# Use folded gates (A-013): first issue FULL IV&V, rest folded
UNTRACKED_ADRS = [...]  # from validator output

for i, adr in enumerate(UNTRACKED_ADRS):
    try:
        issue, created = api.upsert_issue(
            external_id=adr["id"],
            title=f"[{adr['id']}] {adr['title']}",
            description=f"Tracking issue for {adr['id']}. See docs/adr/.",
            state_name="Accepted",
            category="Architecture",
            priority="Low",
        )
        if i == 0 and created:
            # First-batch verify (canonical-pattern §4)
            if not api.verify_issue_field(issue["id"], "labels", []):
                raise SystemExit(2)
        print(f"  {'CREATED' if created else 'EXISTS'}: {adr['id']} → {issue['id']}")
        time.sleep(1.5)
    except RateLimitError as exc:
        print(f"  RATE-LIMIT: {exc} — sleeping 60s")
        time.sleep(60)
```

**Step 5 — Add probe section (g) to regression probe:**

Append to `docs/phase-13/h1-regression-probe.sh`:

```bash
# (g) Cross-index coherence
echo ""
echo "(g) Cross-index coherence (ADR → Plane)"
XINDEX_RESULT=$(python3 scripts/cross-index-validate.py 2>/dev/null; echo $?)
if [ "$XINDEX_RESULT" = "0" ]; then
    echo "  ✅ all ADRs have Plane tracking issues"
    PASS=$((PASS+1))
else
    echo "  ⚠️  cross-index gaps detected — run scripts/cross-index-validate.py for details"
    WARN=$((WARN+1))
fi
```

**Step 6 — Re-run regression probe to verify section (g) now passes:**

```bash
bash docs/phase-13/h1-regression-probe.sh d-xindex-final
# Expect: PASS count increases by 1 (section g now contributes a PASS)
# WARN count should stay ≤ 3
```

### 7.3 Exit gate

- [ ] `scripts/cross-index-validate.py` committed and passes with 0 gaps.
- [ ] Stub Plane issues created for all previously untracked ADRs.
- [ ] Section (g) added to regression probe; probe passes with FAIL=0.
- [ ] DECISION_REGISTER.md references are current (no stale ADR IDs).

**Commit:** `feat(phase-14-D-XINDEX): cross-index validator + regression probe section (g)`

---

## Part 8 — CL-14: Phase 14 closeout

**Estimate:** 2–3h. **Gate:** Full regression probe; git tag; closeout doc.

### 8.1 Pre-closeout audit

Before running the final probe, verify every block's exit gate manually:

```bash
# D-DOC addendum committed
grep -l "NF-14-2\|NF-14-1" docs/phase-14/PHASE_14_BLOCK_D_DOC_CLOSEOUT_2026-04-29.md

# Containers running
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E \
  "structurizr|mkdocs|loki|promtail|zabbix-exporter"
# All must show Up ... (healthy)

# Caddy routes serving
for host in structurizr.internal docs.internal loki.internal; do
    code=$(curl -s -o /dev/null -w "%{http_code}" "https://$host/")
    echo "$host → $code"
done
# All must be 200

# Cross-index validator
python3 scripts/cross-index-validate.py
# Must exit 0

# Restic repo health (from D-RST)
# Source creds from Vault; run restic check
export RESTIC_REPOSITORY=$(vault kv get -field=repository secret/backup)
export RESTIC_PASSWORD=$(vault kv get -field=password secret/backup)
restic check --read-data-subset=1%
unset RESTIC_REPOSITORY RESTIC_PASSWORD

# No plaintext credentials anywhere
grep -rn "Admin1234" ~/.claude/ docs/ 2>/dev/null | grep -v ".git"
# Must return nothing
```

### 8.2 A-012 equivalence harness re-runs

Per ADR-A-012: migrations completed during Phase 14 must be verified at closeout.

```bash
# 1. CMDB_SOURCE flip (D-DOC sub-task 15, commit 60aeb96)
python3 scripts/cmdb_source.py | head -3
# Must show NetBox-sourced services (not yaml-backed)

# 2. Plane admin rotation (NF-14-1)
# Hash of current Vault value must match hash recorded at rotation time
vault kv get -field=password secret/plane/admin | sha256sum | cut -c1-12
# Compare against hash recorded in D-DOC addendum

# 3. plex-mcp sidecar migration (D-DOC Phase G, commit b2b089b)
docker exec plex-mcp env | grep PLEX_TOKEN | sha256sum | cut -c1-12
# Must be non-empty hash (credential present)
```

### 8.3 Final regression probe

```bash
ssh -t admin@192.168.10.145 'cd ~/repos/integrated-ai-platform &&
    bash docs/phase-13/h1-regression-probe.sh phase-14-final |
    tee docs/phase-14/PHASE_14_FINAL_REGRESSION_2026-04-30.log'
```

**Pass criterion:** FAIL=0, WARN ≤ baseline (3). If section (g) now passes, total
PASS count will be 16. Acceptable: PASS=16 FAIL=0 WARN≤3.

If FAIL=1: **stop**. Do not tag or close. Surface for operator decision.

### 8.4 Closeout doc

Commit `docs/phase-14/PHASE_14_CLOSEOUT_2026-04-30.md` recording:

- All blocks: status (closed/deferred), commit hashes, gate results.
- All discoveries (numbered from #31 continuing from Increment 1.5's #30).
- A-012 equivalence harness results (§8.2 hashes).
- Final regression probe result.
- Items deferred to Phase 15+ (Uptime Kuma slug, mcp-docs-remote pre-built image,
  sms1obot hardening, Phase 13 Increments 2B–7 still in progress).
- CLAUDE.md sections updated (Known Hardening Trade-offs resolutions).

### 8.5 Git tag

```bash
git tag phase-14-final
git log --oneline -3  # confirm tag on correct commit
```

### 8.6 CLAUDE.md final update

Update the `## Quick Start / Current Phase` line:

```
**Current Phase:** Phase 14 CLOSED. Phase 15 / Phase 13 Increments 2B–7 in progress.
```

### 8.7 Exit criteria — Phase 14 CLOSED

- [ ] All D-* blocks closed (D-DOC incl. addendum, D-STR, D-MKD, D-ZBX, D-RST, D-LOG, D-XINDEX).
- [ ] CL-14 regression probe: FAIL=0, WARN ≤ 3.
- [ ] A-012 equivalence harness re-runs all pass.
- [ ] No plaintext credentials in any tracked or memory file.
- [ ] `docs/phase-14/PHASE_14_CLOSEOUT_2026-04-30.md` committed.
- [ ] `git tag phase-14-final` applied.
- [ ] CLAUDE.md "Current Phase" updated.

**Commit:** `docs(phase-14): CL-14 closeout — Phase 14 CLOSED`

---

## Hard stops — non-negotiable

These conditions require stopping and surfacing to the operator before proceeding:

1. **Any regression gate returns FAIL≥1.** Do not proceed to the next block.
2. **D-RST restore test fails.** R-CRITICAL (R-P14-7). Backup integrity unknown.
   Escalate before any other work.
3. **Plane curation: first-batch-verify fails.** Abort before bulk label writes.
4. **plex-mcp or zabbix-exporter: credentials not present in container.**
   Do not mark Phase G/D-ZBX complete until credential hash confirmed.
5. **`--no-verify` is never permitted** on any commit.
6. **Credential values must never appear** in terminal output, commit messages,
   log files, or this document. Hash-only, always.

---

## Commit message pattern

Every block follows the same pattern:

```
feat(phase-14-<BLOCK>): <one-line summary>

<Body: what changed, discoveries if any, gate result>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

---

## Summary table

| Block | Effort | Gate | Key hard stop |
|---|---|---|---|
| D-DOC addendum (NF-14-2/1 + curation) | 3–5h | Folded (sub-task addendum) | First-batch-verify on curation |
| D-STR | 2–4h | Full IV&V | Container healthy + Caddy 200 |
| D-MKD | 3–5h | Full IV&V | ADR-A-007 filename renders |
| D-ZBX | 2–4h | Full IV&V | Credentials from Vault sidecar |
| D-RST | 5–8h | Full IV&V + A-012 | Restore test PASS (R-CRITICAL if FAIL) |
| D-LOG | 6–10h | Full IV&V | Loki returns Caddy log entries |
| D-XINDEX | 4–8h | Full IV&V | Validator exits 0; probe (g) PASS |
| CL-14 | 2–3h | Full regression + tag | FAIL=0, WARN≤3; tag applied |
| **Total** | **27–47h** | | |
