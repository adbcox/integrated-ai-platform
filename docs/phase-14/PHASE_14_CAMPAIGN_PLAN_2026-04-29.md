# Phase 14 Campaign Plan

**Date:** 2026-04-29
**Author:** session continuity (post-Increment-2A close; parallel-execution decision)
**Scope:** Phase 14 full arc — D-DOC (entry block) through CL-14 (closeout).
**Calibration baseline:** Block 4.C (8–12h estimate, 12h actual, 17 discoveries).
  Increment 1 (7.5–11.5h estimate, closed clean + 1 mid-stream scope add).
  Mechanical-pattern blocks land near estimate; novel-pattern blocks +50%.

---

## 1. Phase 13 → Phase 14 handoff condition

**Phase 14 entry is gated on:**

> **Increment 1.5 CLOSED** — regression probe `increment-1.5-final`
> recorded at FAIL=0 and WARN ≤ baseline (3). Closeout doc
> `docs/phase-13/INCREMENT_1.5_CLOSEOUT_<date>.md` committed.

Phase 14 does **not** wait for Increments 2–7 to close. Per the
2026-04-29 operator decision: parallel execution is authorized.
Increment 2B through Increment 7 continue on their own cadence (gated
on Mouser+DigiKey+CSV and subsequent block prereqs). Phase 14 runs
concurrently from a separate execution window once Increment 1.5 is
tagged done.

Rationale: D-DOC has no dependency on InvenTree (4.D), cross-index
(4.E+4.H), security baseline (4.J), or health-feed ingestion (HF-1/2).
It only needs the platform to be in a doctrine-stable state, which
Increment 1.5 provides.

---

## 2. Phase 14 day-1 verification — C6 #17 CMDB_SOURCE flip

Before any D-DOC execution work begins, verify or execute C6 #17.

### 2.1 Current state (as of 2026-04-29)

`scripts/cmdb_source.py` line 18: `CMDB_SOURCE` defaults to `yaml`.
The NetBox migration (Block 4.C) completed; `service-registry.yaml`
was renamed `service-registry.yaml.DEPRECATED`. NetBox has been the
authoritative source since then. The stability window (post-4.C) has
elapsed.

### 2.2 Verification step

On Mac Mini, run:

```bash
CMDB_SOURCE=netbox python3 scripts/cmdb_source.py 2>&1 | tail -5
```

If this returns the service list without error, the flip is safe.

### 2.3 Execution (if not yet done)

```bash
# In scripts/cmdb_source.py, change the docstring default line:
# FROM:   CMDB_SOURCE        yaml | netbox  (default: yaml)
# TO:     CMDB_SOURCE        yaml | netbox  (default: netbox)
# AND change the os.environ.get call default:
grep -n "os.environ.get.*CMDB_SOURCE" scripts/cmdb_source.py
# Edit that line: change default from "yaml" to "netbox"
```

Verify consumers still resolve:

```bash
CMDB_SOURCE=netbox python3 scripts/cmdb_source.py
python3 scripts/cmdb_source.py  # now also netbox
```

After flip: watch for 1 week. If no consumer errors surface, the
yaml fallback path can be left in place (it is the A-012 deprecation-
gate pattern; the DEPRECATED file stays until the code removes the
branch).

### 2.4 Gate

This is a folded gate (ADR-A-013) — mechanical application of a
decision already made in Block 4.C. Record result in D-DOC closeout.

---

## 3. Increment sequence

Phase 14 runs **8 increments** in the order below. Effort estimates
use the calibration from §1.

| # | Block ID | Name | Effort (h) | Gate type | Prereqs |
|---|---|---|---|---|---|
| 1 | **D-DOC** | Documentation closeout + hygiene | 10–15 | Full IV&V on sub-stages 6 and 14; folded on remainder | Increment 1.5 CLOSED |
| 2 | **D-STR** | Structurizr Lite adoption | 2–4 | Full IV&V (new container + Caddy route + Vault path) | D-DOC CLOSED |
| 3 | **D-MKD** | MkDocs + Material adoption | 3–5 | Full IV&V (new container + Caddy route) | D-DOC CLOSED |
| 4 | **D-LOG** | Loki for per-site Caddy logs | 6–10 | Full IV&V (novel infra) | D-DOC CLOSED |
| 5 | **D-RST** | Restic backup runbook + quarterly restore test | 5–8 | Full IV&V on restore test; folded on runbook | D-DOC CLOSED |
| 6 | **D-ZBX** | Zabbix Prometheus exporter | 2–4 | Full IV&V (new container) | D-DOC CLOSED |
| 7 | **D-XINDEX** | State-anchoring (g) cross-index extension | 4–8 | Full IV&V (first ADR↔Vault path indexing) | Phase 13 Block 4.E CLOSED (preferred); may run standalone if 4.E is delayed |
| 8 | **CL-14** | Phase 14 closeout | 2–3 | Full regression probe; tag + closeout doc | All prior blocks CLOSED |

**Total Phase 14: 34–57 h.** Point estimate: **~42 h.** Calendar at
typical operator availability: 5–9 weeks.

D-STR and D-MKD may run in either order; both depend only on D-DOC.
D-LOG, D-RST, D-ZBX are independent of each other; all depend on
D-DOC. D-XINDEX is the sole block that benefits from Phase 13
Block 4.E being closed first.

---

## 4. Block D-DOC — Documentation closeout + hygiene

### 4.1 Scope (17 sub-tasks)

Absorbs items from the architecture closeout plan (§4.2.1), plus the
two new Phase 14 follow-ups (NF-14-1 and NF-14-2) registered in the
addendum.

| # | Sub-task | Gate | Effort |
|---|---|---|---|
| 1 | Stale-runbook rewrites: `restart-services.md`, `rotate-credentials.md`, `add-new-mcp-server.md` — all reference `docker/.env` pattern; rewrite to Vault Agent sidecar + AppRole per `add-new-service.md` canonical | Folded (A-013) | 1–1.5h |
| 2 | `docs/architecture/mcp-server-architecture.md` rewrite — stale; documents `.env` credential pattern | Folded | 0.5h |
| 3 | `docs/runbooks/vault-restore-from-backup.md` — referenced from `vault-recovery-from-shamir.md` but does not exist. Author per Restic + Vault snapshot pattern | Folded | 1h |
| 4 | `docs/ARCHITECTURE.md` creation — referenced from CLAUDE.md "Quick Start" but does not exist. Author as top-level architecture overview superseding `PLATFORM_OVERVIEW.md`; pull service inventory from NetBox (authoritative per Block 4.C) | Folded | 1.5–2h |
| 5 | `PLATFORM_OVERVIEW.md` retirement — replace with redirect/archive note pointing to `ARCHITECTURE.md` + NetBox | Folded | 0.25h |
| 6 | H1 §8 detect-secrets baseline tightening — lower `HexHighEntropyString` threshold for YAML; add custom regex `(api[_-]?key\|API_KEY)\s*[:=]\s*[a-f0-9]{32,}`; rebuild baseline; verify catches historical Sonarr/Radarr key pattern | **Full IV&V** (A-011) | 0.5–1h |
| 7 | H1 §9 untracked-files cleanup — resolve `git status` untracked entries | Folded | 0.25h |
| 8 | H1 §10 dependency graph refresh + per-host vault.hcl verify — `docs/architecture/dependency-graph.md` for Block 4.C state; verify `config/vault-configs/*.hcl` | Folded | 0.5h |
| 9 | H1 §11 missing runbooks (net-new beyond sub-task 3) — vault-recovery, add-new-host, drift-detection-procedure, regression-probe-failure, credential-rotation, incident-response | Folded | 1.5–2h |
| 10 | H1 §12 Docker events capture — launchd/cron job for `docker events` → log aggregator | Folded | 0.25h |
| 11 | H1 §13 CLAUDE.md "Platform Rules" finalisation — review for post-Phase-13 drift; consolidate | Folded | 0.5h |
| 12 | Post-Block-2 #1 dead Caddy routes prune — remove 12 `*.internal` routes for non-existent services (manyfold, gitea, tautulli, overseerr, ragflow, portainer, netdata, dozzle, pgadmin, bookstack, n8n, filebrowser) | Folded | 0.5h |
| 13 | Post-Block-2 #2 homepage widget completion — verify Grafana SA token + Uptime Kuma slug render expected widgets on `homepage.internal` | Folded | 0.5h |
| 14 | Plane backlog curation — apply existing 64 labels to ~1100 issues via prefix-mapping script; target ≥95% labeled; re-triage urgent-priority (44 → <10); close ~88 Done items | **Full IV&V** (A-011) — 429-risk; first-batch-verify per canonical-pattern README §4 | 1–1.5h |
| 15 | C6 #17 CMDB_SOURCE default flip — verify or execute per §2 of this plan | Folded (A-013/A-012) | 0.25h |
| 16 | **NF-14-2 — Plane CE web auth configuration** — "No authentication methods available" on login page. Diagnose backend options (local / OIDC / magic-link email); pick and configure one that does not require standing up a new OIDC issuer. Document in `docs/runbooks/plane-web-auth.md`. | **Full IV&V** (A-011) — first-contact with Plane auth subsystem | 1–2h |
| 17 | **NF-14-1 — Plane admin password rotation** — current `admin@local.dev / Admin1234!` plaintext in `plane_deployment.md` memory file. Requires (a) NF-14-2 CLOSED first, (b) Vault path decision for `secret/plane/admin`, (c) rotation via Django shell or web UI, (d) Vault write + hash-only verification, (e) plaintext purge from memory file. | **Full IV&V** (A-011) + A-012 (rotation is a credential-migration) | 0.75–1h |

**Ordering constraint:** Sub-task 17 (NF-14-1) requires sub-task 16
(NF-14-2) CLOSED. All other sub-tasks are unordered within the block.

### 4.2 Revised effort estimate

Base scope (sub-tasks 1–15): 8–12h (as in architecture closeout plan).
NF-14-2 (+1–2h) + NF-14-1 (+0.75–1h): **revised total 10–15h.**

At typical session length (3–4h), this is a 3–4 session block. The
Full IV&V sub-stages (6, 14, 16, 17) each warrant their own
validation checkpoint before folded work resumes.

### 4.3 Gate structure

| Sub-stage grouping | Gate type | Validation |
|---|---|---|
| 1–5, 7–13, 15 (doc rewrites, cleanup, flip) | Folded (A-013) | Reviewer read of each doc + `git diff` |
| 6 (detect-secrets baseline) | Full IV&V (A-011) | Deliberate test commit on sandbox branch catches the Sonarr/Radarr key pattern; pre-commit passes on non-secret files |
| 14 (Plane curation) | Full IV&V (A-011) | First-batch-verify per canonical-pattern §4; probe passes with FAIL=0 post-curation |
| 16 (NF-14-2 web auth) | Full IV&V (A-011) | Login page no longer shows "No authentication methods"; admin can log in; document auth backend in runbook |
| 17 (NF-14-1 admin rotation) | Full IV&V (A-011) + A-012 | Hash in Vault matches expected; Django auth confirms login with new cred; plaintext purged from memory file |
| D-DOC close | Full regression probe | Gate ID `phase-14-doc-final`; FAIL=0, WARN ≤ 3 |

### 4.4 Exit criteria

- [ ] All stale runbooks rewritten (sub-tasks 1, 2, 9).
- [ ] All referenced-but-missing runbooks exist (sub-tasks 3, 9).
- [ ] `docs/ARCHITECTURE.md` exists; `PLATFORM_OVERVIEW.md` archived with redirect (sub-tasks 4, 5).
- [ ] detect-secrets baseline catches historical Sonarr/Radarr key pattern (sub-task 6).
- [ ] Plane issues: ≥95% labeled; urgent count <10; ~88 Done items closed (sub-task 14).
- [ ] CMDB_SOURCE default is `netbox` in `scripts/cmdb_source.py` (sub-task 15).
- [ ] Plane web auth configured; admin can log in via browser (sub-task 16).
- [ ] Plane admin password rotated; plaintext purged from memory file (sub-task 17).
- [ ] Regression probe `phase-14-doc-final`: FAIL=0, WARN ≤ 3.
- [ ] Closeout doc `PHASE_14_BLOCK_D_DOC_CLOSEOUT_<date>.md` committed.

---

## 5. Block D-STR — Structurizr Lite adoption

**Estimate:** 2–4 h. **Gate:** Full IV&V (new container + Caddy route + Vault path for API key if needed).

Structurizr Lite provides a self-hosted C4-model diagram server. Per
state-anchoring recommendation, it closes gap (g) of the cross-index
taxonomy (visual platform topology in a queryable, version-controlled
format — not just doc prose).

**Scope:**
1. Deploy `structurizr/lite` container; pin image tag.
2. Container hardening: `cap_drop:[ALL]`, `no-new-privileges:true`.
3. Caddy route `structurizr.internal` → Structurizr container.
4. Initial C4 workspace file committed to `docs/architecture/workspace.dsl`
   reflecting Phase 13 platform state.
5. Vault path for API key (if Structurizr Lite requires one for remote
   API access — check; Lite may be auth-free for local use).

**Discovery budget:** 2–3 (novel container, first C4 workspace).

---

## 6. Block D-MKD — MkDocs + Material adoption

**Estimate:** 3–5 h. **Gate:** Full IV&V (new container + Caddy route).

MkDocs with Material theme publishes the `docs/` tree as a searchable
internal site. Closes the (g) gap alongside Structurizr.

**Scope:**
1. Deploy `squidfunk/mkdocs-material` container (or build-and-serve
   pattern); pin image tag.
2. Container hardening: `cap_drop:[ALL]`, `no-new-privileges:true`.
3. Caddy route `docs.internal` → MkDocs container.
4. `mkdocs.yml` committed; `docs/` navigation structure defined.
5. ADR-A-007 collision note: the existing ADR README references a
   renumber that occurred when the A-007 slot was reused. Verify
   mkdocs navigation handles the filename correctly (the file is
   `ADR-A-007-media-sync-syncthing.md`).
6. Verify PDF/search features work for the runbook tree.

**Discovery budget:** 2–4 (config, nav, ADR file naming edge case).

---

## 7. Block D-LOG — Loki for per-site Caddy logs

**Estimate:** 6–10 h. **Gate:** Full IV&V (novel infra — first Loki deployment).

Closes the CLAUDE.md "Known Hardening Trade-offs" open item: Caddy
2.11.2 exposes no `host` label on Prometheus metrics; per-site
analysis requires Loki-tailing the JSON access.log.

**Scope:**
1. Deploy Grafana Loki + Promtail (or Alloy) stack.
2. Container hardening: `cap_drop:[ALL]` on all new containers.
3. Promtail config: tail `/var/log/caddy/access.log`; parse `host`
   field from JSON entries; ship to Loki.
4. Caddy route `loki.internal` if Loki HTTP API needs external access.
5. Grafana data source for Loki; per-site dashboard: requests/s, error
   rate, p99 latency, grouped by `host` field.
6. Vault path for Loki API token if Loki auth is enabled.
7. Update CLAUDE.md "Known Hardening Trade-offs" to mark the Caddy
   per-site log item as RESOLVED (Loki in place).

**Discovery budget:** 3–5 (Loki config, promtail log-path bind,
Grafana LogQL queries).

---

## 8. Block D-RST — Restic backup runbook + quarterly restore test

**Estimate:** 5–8 h. **Gate:** Full IV&V on restore test; folded on runbook.

CLAUDE.md "Backup Policy" mandates quarterly restore tests. No test
has been documented. This block makes the test repeatable.

**Scope:**
1. Author `docs/runbooks/backup-restore.md` — full Restic restore
   procedure from QNAP (or local) repository. Include: AppRole
   credential path, `restic restore` command, post-restore Vault
   unseal sequence.
2. Verify `vault-restore-from-backup.md` (authored in D-DOC sub-task 3)
   is consistent with the backup-restore runbook.
3. Run one full restore test to a temporary directory on the Mac Mini.
   Document results (snapshot ID, restored bytes, verification command
   output) in `docs/runbooks/backup-restore-test-2026.md`.
4. Add launchd plist or cron annotation reminding operator to repeat
   quarterly.

**Discovery budget:** 2–3 (Restic auth from AppRole in an interactive
shell, restore path issues, verify command).

---

## 9. Block D-ZBX — Zabbix Prometheus exporter

**Estimate:** 2–4 h. **Gate:** Full IV&V (new container + Grafana data source).

Zabbix 7.4 does not natively expose `/metrics`. Per CLAUDE.md "Known
Hardening Trade-offs," adding a `zabbix-prometheus-exporter` is an
additive deployment deferred to when its metrics are needed in Grafana.
This block delivers that.

**Scope:**
1. Identify and pin a Zabbix Prometheus exporter image (e.g.,
   `untergeek/zabbix-exporter` or equivalent). Verify maintained.
2. Deploy container; `cap_drop:[ALL]`, `no-new-privileges:true`.
3. Grafana data source and dashboard for Zabbix alert/trigger counts.
4. Vault path for Zabbix API credentials the exporter needs.
5. Update CLAUDE.md "Known Hardening Trade-offs" to mark the Zabbix
   Prometheus exporter item as RESOLVED.

**Discovery budget:** 1–3 (exporter image quality varies; Vault path
for Zabbix API token).

---

## 10. Block D-XINDEX — State-anchoring cross-index extension

**Estimate:** 4–8 h. **Gate:** Full IV&V (first ADR↔Plane↔Vault path indexing).

Extends Block 4.E (NetBox+InvenTree+Plane+ADRs+Vault cross-index)
to ADR↔Plane↔Vault paths that 4.E may not cover. The state-anchoring
(g) gap taxonomy item.

**Prereq preference:** Phase 13 Block 4.E CLOSED. May run standalone
if 4.E is delayed, using the NetBox→InvenTree→Plane links from 2A/2B
as the existing cross-index baseline.

**Scope:**
1. Audit current cross-index state: what is indexed (NetBox→InvenTree,
   Plane issue→external_id, ADR status in DECISION_REGISTER.md)?
2. Identify gaps: which Vault paths have no corresponding ADR or Plane
   issue? Which ADRs have no Plane tracking issue?
3. Author `scripts/cross-index-validate.py` — reads NetBox, Plane,
   and DECISION_REGISTER.md; emits a gap report.
4. Create stub Plane issues for un-tracked ADRs.
5. Add cross-index validation to the regression probe
   (`h1-regression-probe.sh`) as a new probe section (g).

**Discovery budget:** 3–5 (first-contact with full cross-index query,
Plane API rate limits, ADR parsing).

---

## 11. Block CL-14 — Phase 14 closeout

**Estimate:** 2–3 h. **Gate:** Full regression probe; git tag; closeout doc.

**Scope:**
1. Run full regression probe with gate ID `phase-14-final`.
   Pass criteria: FAIL=0, WARN ≤ baseline.
2. Run `--verify-roundtrip` probes (A-012) for any migrations
   completed during Phase 14 (CMDB_SOURCE flip, Plane admin rotation,
   Restic restore path).
3. Commit closeout doc `docs/phase-14/PHASE_14_CLOSEOUT_<date>.md`.
4. Git tag `phase-14-final`.
5. Update CLAUDE.md for any new "Known Hardening Trade-offs" resolved
   or deferred during Phase 14.
6. Surface operator summary: items closed, items deferred to Phase 15+,
   new open questions.

---

## 12. Cross-cutting constraints

### 12.1 Calibration

| Block | Pattern class | Estimate basis |
|---|---|---|
| D-DOC | Doctrine sweep + doc authoring — mechanical with 4 IV&V sub-stages | Lower buffer (doc work, no novel infra) |
| D-STR, D-MKD, D-ZBX | Novel container deployments — established Docker pattern | Mid buffer (+30–40%) |
| D-LOG | Novel log-shipping infra — first Loki deployment | High buffer (+50%) |
| D-RST | Operational test — depends on Restic restore path working first try | High buffer (+50%) |
| D-XINDEX | First-contact cross-index scripting — novel query surface | Mid-high buffer (+40%) |

### 12.2 Concurrency with Phase 13

Phase 14 D-DOC is authorized to run in parallel with Phase 13
Increments 2B–7. The following interactions must be managed:

- **Plane backlog curation (D-DOC sub-task 14)** must not overlap
  with any Phase 13 Plane-writing operation (e.g., Block 4.E
  cross-index writes). If both are active in the same window, the
  operator serializes them: Phase 13 write completes, then curation
  runs. Curation is read-heavy with append-only label writes; a
  collision is recoverable but confusing.
- **CMDB_SOURCE flip (D-DOC sub-task 15)** must not overlap with
  Phase 13 Block 4.E's NetBox cross-reference work. Flip after 4.E
  or before 4.E; do not flip mid-increment.
- **detect-secrets baseline tightening (D-DOC sub-task 6)** is in-
  repo pre-commit mutation. Any Phase 13 commits in flight must pass
  the new baseline. Coordinate: tighten the baseline first, confirm
  existing in-flight commits pass, then proceed.

### 12.3 Doctrine bindings

| Block | ADR-A-011 | ADR-A-012 | ADR-A-013 |
|---|---|---|---|
| D-DOC | ✅ 4 Full IV&V sub-stages | ✅ NF-14-1 rotation + C6 #17 flip | ✅ folded on 13 sub-tasks |
| D-STR | ✅ full IV&V | — | — |
| D-MKD | ✅ full IV&V | — | — |
| D-LOG | ✅ full IV&V | — | — |
| D-RST | ✅ restore-test IV&V | ✅ restore-verify probe | — |
| D-ZBX | ✅ full IV&V | — | — |
| D-XINDEX | ✅ full IV&V | ✅ cross-index harness | ✅ stub-issue creation folded |
| CL-14 | ✅ regression probe | ✅ re-runs migration harnesses | ✅ folded report |

### 12.4 Increment size discipline

Per operating-model §6: no increment exceeds ~18 h. D-DOC at 10–15h
fits as a single increment if the operator drives it in 3–4 sessions.
If it grows past 15h mid-execution, split at the nearest Full IV&V
boundary (sub-task 14 or 16 are natural split points).

---

## 13. Risk register (Phase 14 specific)

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-P14-1 | Plane backlog curation hits 429 rate budget before labeling completes | Medium | Low (recoverable, idempotent) | Use `_with_429_retry` from `scripts/backfill-plane-labels.py`; first-batch-verify before bulk run |
| R-P14-2 | detect-secrets baseline tightening causes false-positive cascade on in-repo files | Low | Medium (blocks commits) | Test on a sandbox branch before merging baseline change; scope regex narrowly |
| R-P14-3 | NF-14-2 Plane web auth requires OIDC issuer not yet deployed | Medium | Medium (defers NF-14-1 too) | Prefer local-auth backend (username+password); defer OIDC to a future increment if complexity is high |
| R-P14-4 | Loki deployment conflicts with existing VictoriaMetrics stack (port/namespace collision) | Low | Medium | Audit port assignments before deploy; Loki uses 3100 by default (check against platform port registry) |
| R-P14-5 | D-XINDEX cross-index script surfaces more ADR↔Plane↔Vault gaps than estimated | Medium | Low (planning visibility, not breakage) | Scope the script to report-only first; gap closure is deferred to subsequent increments |
| R-P14-6 | Phase 13 Increments 2B–7 introduce platform changes that conflict with D-DOC doc state | Low | Low | D-DOC's doc outputs reference NetBox (live) and git state, not stale snapshots; update ARCHITECTURE.md after each Phase 13 increment if needed |
| R-P14-7 | Restic restore test fails (corrupted or inaccessible repo) | Low | High (backup integrity unknown) | If restore fails, escalate as R-CRITICAL before proceeding; do not defer |

---

## 14. External prerequisites

Phase 14 has **no external prerequisites**. All blocks use in-repo
or on-platform tooling. The only external dependency is the Plane CE
instance itself (for D-DOC sub-task 14 and NF-14-1/NF-14-2), which is
already running at `plane.internal`.

D-ZBX requires identifying a maintained Zabbix exporter image — a
10-minute lookup, not a dependency on any external service.

---

## 15. Open questions

| ID | Question | Blocks if unresolved | Default if no answer |
|---|---|---|---|
| Q-P14-1 | For NF-14-2 Plane web auth: local username+password auth backend vs. OIDC? | NF-14-2, NF-14-1 | Default: local auth backend (minimal footprint; OIDC deferred) |
| Q-P14-2 | Vault path for Plane admin creds: `secret/plane/admin` or `secret/plane/admin_creds`? | NF-14-1 | Default: `secret/plane/admin` (matches existing `secret/plane/*` pattern from Plane AppRole provisioning) |
| Q-P14-3 | D-XINDEX: should it run before or after Phase 13 Block 4.E closes? | D-XINDEX sequencing | Default: after 4.E if it closes in ≤4 weeks; else standalone |
| Q-P14-4 | D-LOG: Promtail vs. Grafana Alloy for Caddy log shipping? | D-LOG implementation | Default: Promtail (simpler, already used in the Grafana ecosystem; Alloy is the successor but adds complexity) |

---

## 16. References

- Architecture closeout plan + addendum: `docs/phase-14/ARCHITECTURE_CLOSEOUT_PLAN_2026-04-29.md`
- Phase 13 campaign plan (Increments 2–7): `docs/phase-13/PHASE_13_CLOSEOUT_CAMPAIGN_PLAN_2026-04-29.md`
- Increment 1.5 inventory (§7 execution basis): `docs/phase-13/INCREMENT_1.5_INVENTORY_2026-04-29.md`
- Increment 1.5 regression baseline: `docs/phase-13/INCREMENT_1.5_REGRESSION_BASELINE_2026-04-29.log`
- Operating model: `docs/runbooks/operating-model.md`
- ADR-A-011 (IV&V loop), ADR-A-012 (equivalence harness), ADR-A-013 (folded gates)
- DECISION_REGISTER.md
- Canonical Plane connector pattern: `docs/canonical-patterns/plane-connector-usage.md`
- Increment 2A closeout (InvenTree baseline): `docs/phase-13/PHASE_13_INCREMENT_2A_CLOSEOUT_2026-04-29.md`
