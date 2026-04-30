# Phase 14 D-DOC Closeout
**Date:** 2026-04-29
**Campaign:** D-DOC — Documentation, drift, and doctrine hygiene
**Regression probe:** `docs/phase-14/INCREMENT_2_REGRESSION_BASELINE_2026-04-29.log`
**Gate result:** PASS=15 FAIL=0 WARN=3 ✅

---

## Summary

Phase 14 D-DOC executed a 9-phase, 20-sub-task documentation and doctrine
hygiene campaign across the integrated AI platform. All mandatory sub-tasks
completed. Phases F, F2, F3 (Plane backlog curation and auth) are deferred
to Phase 15 per the ordering constraint in the campaign plan.

---

## Phase-by-Phase Disposition

| Phase | Sub-tasks | Status | Commits |
|-------|-----------|--------|---------|
| A — CMDB_SOURCE flip | 15 | ✅ Complete | see `git log --grep=phase-14-A` |
| B — Runbook rewrite | 1–5, 9 | ✅ Complete | 9 runbook files (add-new-service, vault-unseal, vault-restore-from-backup, drift-detection-procedure, regression-probe-failure, incident-response, add-new-host, plus 2 from prior session) |
| C — detect-secrets IV&V | 6 | ✅ Complete | Baseline adequate; HexHighEntropyString + KeywordDetector confirmed catching in-repo credential patterns |
| D — Architecture cleanup | 7–8, 10–11 | ✅ Complete | ARCHITECTURE.md (new, supersedes PLATFORM_OVERVIEW.md), dependency-graph.md refreshed (74 nodes/15 categories), CLAUDE.md doctrine updates, docker-events launchd agent |
| E — Caddy + homepage hygiene | 12–13 | ✅ Complete | 13 dead Caddy routes pruned; Grafana SA token confirmed; Uptime Kuma slug gap documented (pre-existing) |
| F — Plane backlog curation | 14 | ⏸ Deferred to Phase 15 | NF-14-1: requires Plane web auth before labeling |
| F2 — Plane web auth | 16 | ⏸ Deferred to Phase 15 | NF-14-2: "No authentication methods available" — local auth backend needs config |
| F3 — Plane admin rotation | 17 | ⏸ Deferred to Phase 15 | Blocked on F2 |
| G — plex-mcp sidecar migration | 18 | ✅ Complete | D#26 remediated; sidecar ExitCode=0; PLEX_TOKEN hash fdf0c486bdca; /healthz → ok |
| H — Non-compose hardening | 19–20 | ✅ Complete | mcp-docker-remote compose migration + cap_drop:[ALL]; KI-004 authored |
| I — Closeout | — | ✅ Complete | This document |

---

## Doctrine Violations Discovered and Remediated

| ID | Discovery | Remediation | Commit |
|----|-----------|-------------|--------|
| D#26 | plex-mcp credentials in `environment:` blocks | Vault Agent sidecar pattern; compose rewrite | `b2b089b` |
| D#29 | mcp-docs-remote: apt+npm on every restart (crash loop) | `--ignore-scripts` flag; KI-004 authored | `7a9e7e4` |
| D#30 | sms1obot containers not compose-managed or hardened | Documented as permanent KI; CLAUDE.md updated | `44d2c6b` |

---

## New Artifacts

### Documentation
- `docs/ARCHITECTURE.md` — authoritative platform architecture doc (supersedes PLATFORM_OVERVIEW.md)
- `docs/architecture/dependency-graph.md` — 74-node/15-category graph (from NetBox Block 4.C state)
- `docs/runbooks/add-new-service.md`
- `docs/runbooks/add-new-host.md`
- `docs/runbooks/vault-unseal.md`
- `docs/runbooks/vault-restore-from-backup.md`
- `docs/runbooks/drift-detection-procedure.md`
- `docs/runbooks/regression-probe-failure.md`
- `docs/runbooks/incident-response.md`
- `docs/known-issues/KI-004-mcp-docs-remote-startup.md`

### Configuration
- `config/vault-policies/plex-mcp-policy.hcl` — added arr/sonarr + arr/radarr read paths
- `docker/vault-agent-plex-mcp/agent.hcl` — plex-mcp Vault Agent sidecar config
- `docker/vault-agent-plex-mcp/credentials.env.tmpl` — credential template (6 vars)
- `docker/mcp/docker-compose.yml` — rewritten with sidecar + node-based healthcheck
- `docker/mcp/docker-compose.mcp-docker-remote.yml` — new compose file for mcp-docker-remote
- `docker/obot-stack.yml` — mcp-docs-remote `--ignore-scripts` fix
- `docker/caddy/Caddyfile` — 13 dead routes pruned

### Out-of-Repo (logged, not committed)
- `~/Library/LaunchAgents/com.iap.docker-events.plist` — docker events capture launchd agent

---

## Regression Probe Results

Gate tag: `phase-14-doc-final`
Timestamp: 2026-04-29T22:48:02-04:00

```
PASS=15 FAIL=0 WARN=3
```

**Warns (all pre-existing / expected):**
- `openhands.internal` not in DNS cache — not recently browsed; not a regression
- Restic snapshot list inaccessible — credentials are Vault-fetched at backup runtime only
- No gate-specific dependency probes defined for generic tag — expected

---

## Open Items → Phase 15

1. **Plane backlog curation:** Apply ~64 labels to ~1100 issues; first-batch-verify mandatory; target ≥95% labeled. (NF-14-2 now closed unblocks this.)
2. **mcp-docs-remote pre-built image:** KI-004 recommendation; reduce cold-start from 60s to <5s; eliminate apt/npm network dependency at startup.
3. **Uptime Kuma slug for homepage widget:** Pre-existing gap; 0 monitors assigned to slug config.

---

## Addendum — NF-14-2 / NF-14-1 Post-Gate Resolution (2026-04-30)

**Authorized:** Post-gate addendum; D-DOC regression probe already at PASS=15 FAIL=0 WARN=3.

### NF-14-2 — Plane web auth fix

**Root cause:** `makeplane/plane-frontend:stable` ships `nginx.conf` with only a
static catch-all (`try_files $uri $uri/ /index.html`). The Next.js SPA
fetches `/api/instances/` relative to its origin (port 3001). nginx returned
`index.html` for it; the SPA parsed HTML as JSON, failed, and showed "No
authentication methods available." `ENABLE_EMAIL_PASSWORD = 1` was already
correct in the `instance_configurations` DB table — this was purely a proxy
routing defect in the stock image config.

**Fix:** Override `nginx.conf` via compose bind mount to add `proxy_pass`
rules for `/api/` and `/auth/` → `http://plane-api:8000`.

**IV&V:**
- `curl http://localhost:3001/api/instances/` → JSON with `"is_email_password_enabled": true`
- Login via form POST with CSRF → HTTP 302 Location: `http://localhost:3001` (no error_code)

**Commit:** `ce76590`
**Files:** `docker/plane-nginx/nginx.conf`, `docker/docker-compose-plane.yml`, `docs/runbooks/plane-web-auth.md`

### NF-14-1 — Plane admin password rotation

**Disposition:** Already done in Block 2 P2.1 (2026-04-28). `secret/plane/admin`
exists in Vault with `password`, `email`, `rotated=2026-04-28`, `reason` keys.
Password hash: `14e715e688a8`. No further rotation required. Plaintext purged
from `plane_deployment.md` memory file.

**Commit:** `ce76590` (memory file update folded into NF-14-2 commit)

### D-DOC exit criteria — final state

All D-DOC exit criteria now met:

| Criterion | Status |
|-----------|--------|
| Stale runbooks rewritten (sub-tasks 1, 2, 9) | ✅ |
| Missing runbooks exist (sub-tasks 3, 9) | ✅ |
| `docs/ARCHITECTURE.md` exists; `PLATFORM_OVERVIEW.md` archived | ✅ |
| detect-secrets baseline catches historical key pattern (sub-task 6) | ✅ |
| CMDB_SOURCE default is `netbox` (sub-task 15) | ✅ |
| Plane web auth configured; admin can log in (sub-task 16) | ✅ (`ce76590`) |
| Plane admin password in Vault; plaintext purged (sub-task 17) | ✅ (2026-04-28 + purge) |
| Plane issues ≥95% labeled; urgent <10; ~88 Done closed (sub-task 14) | ⏸ Deferred → Phase 15 (unblocked by NF-14-2) |
| Regression probe PASS=15 FAIL=0 WARN=3 | ✅ (2026-04-29) |
| Closeout doc committed | ✅ |

**D-DOC is fully closed.** Remaining open item (Plane backlog curation) is
deferred to Phase 15 by operator decision — it is a standalone operation
with no blocking dependencies now that auth works.

---

## CLAUDE.md Updates Applied This Session

- Phase header: Phase 13 Block 4.C closed → Phase 14 D-DOC
- Docs pointer: PLATFORM_OVERVIEW.md → ARCHITECTURE.md throughout
- CMDB_SOURCE: default confirmed as `netbox` (transition window closed)
- Container Hardening: D#30 note (sms1obot containers permanently unhardened)
- Backup Policy: runbook pointer updated to `vault-restore-from-backup.md`
- Operating Doctrine: D#25 (AppRole provisioning), §6/§7 final state
- Project Structure: ARCHITECTURE.md as start-here doc
