# Architecture + Roadmap Closeout Plan — Phase 13 through Phase 14 horizon

**Date:** 2026-04-29
**Author:** session continuity (post-Increment-1 close, commit `718a6c2`)
**Scope:** Plan-only. Catalogs every major open item across the
platform's architecture and roadmap, classifies each by phase, and
proposes a Phase 14 entry block plus a beyond-Phase-14 horizon. **No
execution.**
**Calibration baseline:** Block 4.C estimated 8–12 h, actual ~12 h
with 17 discoveries. Increment 1 estimated 7.5–11.5 h, closed clean
with one mid-stream scope addition (F2). The "+50% discovery overhead"
norm for novel-pattern blocks holds; mechanical-pattern blocks land
near clean estimate.

This plan does not re-scope Phase 13 — the
[Phase 13 Closeout Campaign Plan](../phase-13/PHASE_13_CLOSEOUT_CAMPAIGN_PLAN_2026-04-29.md)
(Appendix D + E locked) is canonical for Increments 2–7. This plan
**adds** the items that campaign plan does not enumerate (predominantly
H1 deferred work, stale runbooks, doctrine-debt, future-state items),
proposes a phase boundary for each, and surfaces what Phase 14 should
own as its own work.

---

## 1. Executive summary

| | |
|---|---|
| Total open items catalogued | **38** (across Phase 13 in-scope, Phase 13 closeout backlog, Phase 14 entry, Phase 14 backlog, beyond-14 horizon) |
| Phase 13 in-scope (in current plan) | **7 increments** = 6 open blocks (4.D, 4.E+4.H, 4.J, 4.I, 4.G+4.F, HF-1+HF-2, CL) — see campaign plan §4 |
| **Phase 13 closeout backlog (NOT in current plan)** | **9 items** (~10–13 h) — H1 §6 sidecar rollout, H1 §7 hardening, H1 §8–§13 cluster, C6 follow-ups #7/#9/#17, Post-Block-2 follow-ups #1/#2 |
| **Phase 14 entry block (proposed)** | **1 block ("D-DOC")** — stale runbook rewrites, missing runbooks, ARCHITECTURE.md creation, PLATFORM_OVERVIEW retirement, Plane backlog curation. Estimate **8–12 h.** |
| **Phase 14 backlog (deferred from Phase 13)** | **6 items** (~30–45 h) — Structurizr Lite, MkDocs, Loki, Restic restore-test runbook, Zabbix Prometheus exporter, state-anchoring (g) cross-index extension beyond 4.E |
| **Beyond Phase 14** | **5 items** — MacBook Pro M5 parity refresh, Mac Studio M3 arrival, Linux/Threadripper arrival, OpenBao evaluation, Backstage re-evaluation |
| Total horizon effort | **~110–160 hours** point estimate ~135 h (Phase 13 closeout 80–100 h + Phase 14 entry 8–12 h + Phase 14 backlog 30–45 h, beyond-14 size depends on hardware-arrival timeline) |
| Realistic calendar | **Phase 13 close:** 6–10 weeks at one execution increment per week, per campaign plan §1. **Phase 14:** 3–6 weeks. **Beyond-14:** hardware-driven. |

**Bottom line.** The Phase 13 campaign plan describes the *novel-work*
arc through Phase 13 close. This plan describes the *closeout-debt*
arc that runs alongside it (the H1 §6/§7 cluster especially), plus
the Phase 14 entry block that sweeps doctrine debt and stale-runbook
debt before any Phase 14 novel work begins. Phase 13 closure is gated
on the closeout-backlog cluster being either swept or explicitly
deferred to Phase 14 — the operator's choice; this plan recommends
sweeping H1 §6 (sidecar rollout) inside Phase 13 (it is a non-
negotiable doctrine violation) and deferring the rest to Phase 14.

---

## 2. Item roster

Status legend: ✅ closed · 🟢 open, ready · 🟡 open, prereq pending · 🔵 deferred / future · ⛔ doctrine violation (must close before phase tag)

Phase column: **13** (in current Phase 13 campaign plan), **13c** (Phase 13 closeout backlog — should fold into the campaign or be explicitly deferred), **14** (Phase 14 entry block recommendation), **14b** (Phase 14 backlog — deferred from Phase 13), **>14** (beyond-Phase-14).

| # | Item | Phase | Effort (h) | Risk | Doctrine binding | Status |
|---|---|---|---|---|---|---|
| 1 | Block 4.D — InvenTree + Mouser/DigiKey + 129-CSV import + NetBox cross-ref | 13 | 8–14 | recoverable | A-011 (full IV&V), **A-012** (4.D.3 migration) | 🟡 prereq: Mouser+DigiKey API keys, components CSV |
| 2 | Block 4.E — cross-index (NetBox+InvenTree+Plane+ADRs+Vault) | 13 | 6–10 | recoverable | A-011, **A-012** (per A-D-2) | 🟡 blocked by 4.D |
| 3 | Block 4.H — upgrade-watcher service | 13 | 4–7 | recoverable | A-013 (folded against drift-watcher pattern) | 🟢 open |
| 4 | Block 4.J — network discovery → NetBox dcim | 13 | 6–10 | recoverable (write-into-NetBox) | A-011, **A-012** | 🟢 open |
| 5 | Block 4.I — Gmail receipt ingestion → InvenTree drafts | 13 | 6–10 | recoverable | A-011, **A-012** | 🟡 prereq: Gmail OAuth + vision-API decision (Q-7) |
| 6 | Block 4.G — vision-recognition InvenTree plugin | 13 | 6–10 | recoverable | A-011 (first plugin) | 🟡 blocked by 4.D |
| 7 | Block 4.F — BLE label maker | 13 | 4–8 | cosmetic | A-013 (folds against 4.G plugin pattern) | 🟡 hardware prereq |
| 8 | Block HF-1 — Oura Ring 4 ingestion | 13 | 5–8 | recoverable | A-011, **A-012** (TS store choice promoted to prereq per A-D-3) | 🟡 prereq: Oura OAuth + TS-store choice |
| 9 | Block HF-2 — Garmin Fenix/Edge ingestion | 13 | 5–8 | recoverable | A-013 (folds against HF-1) | 🟡 prereq: Garmin auth path (Q-10) |
| 10 | Block CL — Phase 13 closeout (`phase-13-final` regression, tag, doc) | 13 | 2–3 | cosmetic | A-013 (folded), A-012 §req-art-#4 (re-runs all migration harnesses) | 🟡 blocked by all prior blocks-or-defer |
| 11 | **H1 §6 — sidecar rollout, 12 services not yet rewired** | 13c | 3–4 | recoverable | A-011 (first-contact per service), CLAUDE.md non-negotiable #1 | ⛔ doctrine violation (12 services consume `.env` for credentials) |
| 12 | **H1 §7 — container hardening, 22 root-running containers** | 13c | 3–4 | recoverable | CLAUDE.md "Container Hardening" | ⛔ doctrine violation |
| 13 | H1 §8 — pre-commit + detect-secrets baseline tightening | 13c | 0.5 | low | CLAUDE.md "Secrets Management" | 🟢 open |
| 14 | H1 §9 — untracked files cleanup | 13c | 0.5 | cosmetic | hygiene | 🟢 open |
| 15 | H1 §10 — service dependency graph + per-host vault.hcl | 13c | 1 | low | A-011 §audit | 🟢 open |
| 16 | H1 §11 — runbooks (7 missing files) | 13c | 2 | low | doctrine reproducibility | 🟢 open |
| 17 | H1 §12 — Docker events capture (launchd/cron) | 13c | 0.25 | low | observability | 🟢 open |
| 18 | H1 §13 — CLAUDE.md "Platform Rules" finalisation | 13c | 0.25 | low | doctrine | 🟢 open |
| 19 | C6 #7 + #9 — revoke memory-file plaintext Plane API token | 13c | 0.25 | **security** | CLAUDE.md "Secrets Management" hash-only rule | ⛔ doctrine violation (plaintext credential in memory file) |
| 20 | C6 #17 — flip `CMDB_SOURCE` default yaml→netbox | 13c | 0.5 | low | A-012 §lifecycle (deprecation gate) | 🟢 open (post-stability-window) |
| 21 | Post-Block-2 #1 — prune 12 dead `*.internal` Caddy routes | 13c | 0.5 | low | hygiene | 🟢 open |
| 22 | Post-Block-2 #2 — homepage widget completion | 13c | 0.5 | low | hygiene | 🟢 open |
| 23 | **Phase 14 entry — D-DOC: stale-runbook rewrites + ARCHITECTURE.md + Plane backlog curation** | 14 | 8–12 | low | A-011 (doctrine block), CLAUDE.md "Verification Doctrine" | 🟢 open (this plan's recommendation) |
| 24 | Phase 14 — Structurizr Lite adoption | 14b | 2–3 | low | state-anchoring (g) cross-index | 🔵 deferred |
| 25 | Phase 14 — MkDocs + Material adoption | 14b | 3–4 | low | state-anchoring (g), ADR-A-007 collision forcing-function | 🔵 deferred |
| 26 | Phase 14 — Loki for per-site Caddy logs | 14b | 6–10 | medium | CLAUDE.md "Known Hardening Trade-offs" | 🔵 deferred |
| 27 | Phase 14 — Restic backup runbook + quarterly restore test | 14b | 4–6 | recoverable | CLAUDE.md "Backup Policy" | 🔵 deferred |
| 28 | Phase 14 — `vault-restore-from-backup.md` runbook (referenced but missing) | 14b | 1–2 | recoverable | CLAUDE.md "Vault Operations" | 🔵 deferred |
| 29 | Phase 14 — Zabbix Prometheus exporter | 14b | 2–4 | low | CLAUDE.md trade-off | 🔵 deferred |
| 30 | Phase 14 — state-anchoring (g) cross-index extension beyond 4.E | 14b | 4–8 | recoverable | extends 4.E to ADR↔Plane↔Vault paths | 🔵 deferred (consider after 4.E) |
| 31 | >14 — MacBook Pro M5 parity refresh | >14 | 6–10 | recoverable | ADR-A-001, ADR-A-008 (no fork), CLAUDE.md heterogeneous architecture | 🔵 hardware-arrival-driven |
| 32 | >14 — Mac Studio M3 arrival + topology rewrite | >14 | 12–20 | high (topology) | ADR-A-001 portability, R-7 | 🔵 hardware-driven |
| 33 | >14 — Linux/Threadripper arrival | >14 | 12–20 | high | ADR-A-001, R-7 | 🔵 hardware-driven |
| 34 | >14 — OpenBao parallel-deploy evaluation (Vault successor) | >14 | 4–8 | recoverable | ADR-A-009 (Vault canonical), ADR-A-010 (adopt-vs-build) | 🔵 long-horizon |
| 35 | >14 — Backstage re-evaluation (vs current NetBox+Structurizr+MkDocs) | >14 | 8–16 | low | ADR-A-010 | 🔵 long-horizon |
| 36 | >14 — `secret/anthropic/api` Vault path deletion (Phase 13.5 §6 carry-over) | >14 | 0.25 | low | LLM Access Doctrine | 🔵 deferred (no consumer) |
| 37 | >14 — `cadvisor` `id="/docker/<sha>"` label resolution (Linux migration) | >14 | — | cosmetic | trade-off documented | 🔵 hardware-driven |
| 38 | >14 — `service-registry.yaml.DEPRECATED` deletion (post-soak window) | >14 | 0.25 | low | A-012 §deprecation gate | 🔵 deferred (yaml fallback in `cmdb_source.py`) |

**Summary by phase:**

| Phase | Items | Effort range (h) |
|---|---|---|
| 13 (in plan) | 10 | 52–88 |
| **13c (closeout backlog)** | 12 | 12.25–17.25 |
| **14 (entry block)** | 1 | 8–12 |
| 14b (Phase 14 backlog) | 7 | 22–37 |
| >14 (beyond) | 8 | 42.5–74.5 (hardware-driven) |
| **Total** | **38** | **136.75–228.75** (point estimate ~165 h) |

The **point estimate of ~165 h** matches a 13–18 month horizon at the
operator's typical 12–18 h/wk peak with slack windows — i.e., this is
"the full architecture closeout from today through next-platform
arrival."

---

## 3. Phase 13 closeout map

This section is **a reference, not a re-scope**. The
[Phase 13 Closeout Campaign Plan](../phase-13/PHASE_13_CLOSEOUT_CAMPAIGN_PLAN_2026-04-29.md)
remains canonical for Increments 2–7. This map shows where each
campaign plan increment fits relative to the closeout-backlog cluster.

### 3.1 Increments and their canonical references

| Increment | Item refs | Reference |
|---|---|---|
| 1 (✅ CLOSED) | D-OP + D-CN + back-fill | `INCREMENT_1_CLOSEOUT_2026-04-29.md` |
| 2 | Item 1 (Block 4.D) | Campaign plan §4 + Appendix D §D.2 |
| 3 | Items 2 + 3 (Block 4.E + 4.H) | Campaign plan §4 + Appendix D §D.2 |
| 4a | Item 4 (Block 4.J) | Campaign plan Appendix D §D.2 (split-from-original-4) |
| 4b | Item 5 (Block 4.I) | Campaign plan Appendix D §D.2 (split-from-original-4) |
| 5 | Items 6 + 7 (Block 4.G + 4.F) | Campaign plan §4 + Appendix D §D.2 |
| 6 | Items 8 + 9 (HF-1 + HF-2) | Campaign plan §4 + Appendix D §D.2 |
| 7 | Item 10 (CL) | Campaign plan §4 |

### 3.2 Closeout backlog (items 11–22) — proposed disposition

This plan **does not modify the campaign plan**. It surfaces the
closeout-backlog items as an addendum the operator may either:

(a) **Fold into Phase 13 closeout** (recommended for items 11, 12, 19 — the doctrine violations) by inserting a sub-stage at the start of the next available increment window, or by running them as a dedicated "platform stabilisation v2" increment between Increment 1 and Increment 2.

(b) **Defer to Phase 14 entry block (D-DOC)** for items 13–18, 20–22 (low-risk hygiene + post-stability-window flips + cosmetic doctrine completion).

**Recommendation per item:**

| # | Item | Recommendation | Rationale |
|---|---|---|---|
| 11 | H1 §6 sidecar rollout (12 services) | **Fold into Phase 13** as "Increment 1.5" or as the first sub-stage of Increment 2 | ⛔ doctrine violation: 12 services still consume `.env` credentials. Cannot tag Phase 13 with this open. |
| 12 | H1 §7 hardening (22 containers) | **Fold into Phase 13** as Increment 1.5b | ⛔ doctrine violation: containers run as root. Cannot tag Phase 13 with this open. |
| 19 | C6 #7/#9 memory-file plaintext token | **Immediate** (next operator window, ~15 min) | ⛔ active credential exposure. Operator-only action (Plane UI revoke + memory file edit). Should not wait for any increment. |
| 13 | H1 §8 detect-secrets baseline | Phase 14 D-DOC | low risk; the leak class is documented; sweep with other doctrine items |
| 14 | H1 §9 untracked files | Phase 14 D-DOC | trivial |
| 15 | H1 §10 dependency graph + per-host vault.hcl | Phase 14 D-DOC | piece of architecture-doc work |
| 16 | H1 §11 runbooks (7 files) | Phase 14 D-DOC | overlaps with stale-runbook rewrites |
| 17 | H1 §12 Docker events capture | Phase 14 D-DOC | trivial |
| 18 | H1 §13 CLAUDE.md "Platform Rules" | Phase 14 D-DOC | trivial |
| 20 | C6 #17 `CMDB_SOURCE` flip | **Increment 2 kickoff or D-DOC** | A-012 deprecation gate — once flipped, watch for ≥1 week, then proceed. May land in Increment 2 prep. |
| 21 | Post-Block-2 #1 dead Caddy routes | Phase 14 D-DOC | hygiene |
| 22 | Post-Block-2 #2 homepage widgets | Phase 14 D-DOC | hygiene |

**Net effect on campaign plan:** if the operator accepts the
recommendation, **two new sub-stages are inserted between Increment 1
and Increment 2** (call them 1.5a + 1.5b) and the rest of the
closeout backlog rolls into Phase 14's entry block (D-DOC).

The 1.5a + 1.5b cluster is ~6–8 h. Splitting the existing campaign
plan's "next increment is 4.D" pattern is the doctrine-aligned move:
A-011 §stop-and-surface mandates that an operator cannot start
Increment 2 with 12 services consuming `.env` credentials when the
canonical pattern is Vault Agent sidecar. The 12-service rewire is
**mechanical** (per H1 checkpoint §6.1, the canonical pattern is
built and proven; what remains is per-service application).

### 3.3 Increment 1.5 proposed structure

If the operator accepts the fold:

**Increment 1.5 — Doctrine-violation closeout** (proposed addendum)

- **Blocks:** H1 §6 sidecar rollout + H1 §7 container hardening + C6 #7/#9 (memory file revoke).
- **Estimate:** 6–8 h.
- **Gate structure:**
  - 1.5a §6 audit (per-service entrypoint shape — 12 services): full IV&V (A-011 — 12 stateful surfaces).
  - 1.5a §6 execution per Phase A→F dependency order: folded per-service after the first one (A-013 — vaultwarden establishes pattern).
  - 1.5b §7 hardening per container (22 services): folded as one IV&V step (A-013 — uniform `cap_drop:[ALL]` + `no-new-privileges` + `read_only` where image supports).
  - C6 #7/#9: trivial (operator-only action; not folded into the increment but recorded as completed before the regression probe).
  - Increment 1.5 close: full regression probe (`increment-1-5-final`).
- **Doctrine citation:** A-011 (12-service first-contact); A-013
  (per-service fold after the first); CLAUDE.md non-negotiable #1.
- **Operator decision:** confirm the fold, or explicitly defer §6/§7
  to Phase 14 (would breach CLAUDE.md non-negotiable #1 until then).

---

## 4. Phase 14 entry plan

### 4.1 Goal

Phase 14 enters with the platform's *novel-work arc* completed
(Phase 13 close), the *doctrine debt* swept (Increment 1.5 if
adopted, plus C6 #7/#9), and the *hygiene debt* still pending. The
Phase 14 entry block sweeps the remaining hygiene + missing-doc debt
in one increment, before any new feature work.

This matches the operating-model doctrine: blocks of doctrine work
have the highest decay rate and the lowest external prerequisites.
Sweeping them at phase entry keeps the platform readable for a
reviewer (operator-self in 6 months, OMSCS reader, future ops
partner) and avoids accumulating two phases' worth of doctrine debt.

### 4.2 Block D-DOC — Documentation closeout + hygiene

**Estimate:** 8–12 h.
**Prereqs:** none beyond Phase 13 close.
**Reversibility:** trivial (docs only) for ~80% of scope; the
detect-secrets baseline tightening and the Plane backlog curation
are the only execution-bearing sub-stages.

#### 4.2.1 Scope

1. **Stale-runbook rewrites (3 files)** — `restart-services.md`,
   `rotate-credentials.md`, `add-new-mcp-server.md` all reference
   `docker/.env` patterns that pre-date Vault doctrine. Rewrite
   each to use Vault Agent sidecar + AppRole pattern (canonical
   per `docs/runbooks/add-new-service.md`).
2. **`docs/architecture/mcp-server-architecture.md` rewrite** —
   stale; documents docker/.env credential pattern.
3. **`docs/runbooks/vault-restore-from-backup.md`** — referenced
   from `vault-recovery-from-shamir.md` but does not exist. Author
   per Restic + Vault snapshot pattern.
4. **`docs/ARCHITECTURE.md` creation** — referenced from CLAUDE.md
   "Quick Start" (line 19) but file does not exist. Author as
   top-level architecture overview that supersedes
   `PLATFORM_OVERVIEW.md`. Pull current state from NetBox where
   possible (per Block 4.C precedent — NetBox is now authoritative
   for service inventory).
5. **`PLATFORM_OVERVIEW.md` retirement** — replace with a redirect
   or archive note pointing at `ARCHITECTURE.md` + NetBox.
6. **H1 §8 detect-secrets baseline tightening** — lower
   `HexHighEntropyString` threshold for YAML files; add custom
   regex `(api[_-]?key|API_KEY)\s*[:=]\s*[a-f0-9]{32,}`; rebuild
   baseline; verify against the historical Sonarr/Radarr keys
   (state-anchoring discovery §1.6.4 finding).
7. **H1 §9 untracked files cleanup** — sweep `git status` and
   resolve.
8. **H1 §10 service dependency graph + per-host vault.hcl** — refresh
   `docs/architecture/dependency-graph.md` for Block 4.C state;
   verify per-host Vault configs (`config/vault-configs/*.hcl`).
9. **H1 §11 missing runbooks (7 files)** — overlaps with stale-
   runbook rewrites above; net new: vault-recovery, backup-restore,
   add-new-host, drift-detection-procedure, regression-probe-failure,
   credential-rotation, incident-response.
10. **H1 §12 Docker events capture** — launchd/cron job for
    `docker events` → log aggregator. Trivial.
11. **H1 §13 CLAUDE.md "Platform Rules" finalisation** — review,
    consolidate.
12. **Post-Block-2 #1 dead Caddy routes prune** — remove 12
    `*.internal` routes for non-existent services.
13. **Post-Block-2 #2 homepage widget completion** — verify Grafana
    SA token + Uptime Kuma slug config render correctly.
14. **Plane backlog curation** — apply existing 64 labels to the
    1100 issues via prefix-mapping (44 of 47 prefix tokens have
    exact-string label matches per state-anchoring discovery §B2);
    target ~1 h scripted back-fill plus operator review of the
    3 unmatched prefixes. Reduce urgent-priority count from 44 to
    <10 by re-triage. Close the ~88 already-Done items.
15. **C6 #17 `CMDB_SOURCE` default flip** if not yet executed —
    flip default in `cmdb_source.py`, watch for ≥1 week, then
    proceed.

#### 4.2.2 Gate structure

| Sub-stage | Gate type | Reasoning |
|---|---|---|
| 1–5 (doc rewrites + creation) | Folded (A-013) | Mechanical; canonical patterns exist (`add-new-service.md` for sidecar shape; NetBox API for inventory). Peer review is the validation. |
| 6 (detect-secrets baseline) | **Full IV&V** (A-011) | Active mutation against pre-commit hook config; must verify the known leak is now caught without false-positive cascade. |
| 7–11 (H1 §9–§13 cleanup) | Folded | Trivial. |
| 12 (Caddy routes prune) | Folded | Mechanical; Caddyfile is one file. |
| 13 (homepage widgets) | Folded | Mechanical; widget render verification is the validation. |
| 14 (Plane backlog curation) | **Full IV&V** (A-011) | Active mutation against 1100 issues; 429 risk per R-1. Must use `framework/plane_connector.py` with first-batch-verify (Discovery #15, A-013 §worked-example for back-fills). |
| 15 (C6 #17 flip) | Folded | A-012 §deprecation-gate — flip after stability window; mechanical. |
| D-DOC close | Full regression probe | Standard. |

#### 4.2.3 Exit gate

- All stale runbooks rewritten and referenced runbooks present.
- `docs/ARCHITECTURE.md` exists; `PLATFORM_OVERVIEW.md` archived
  with redirect.
- detect-secrets baseline catches the historical Sonarr/Radarr key
  pattern; verified by deliberate test commit against a sandbox
  branch.
- 1100 Plane issues have labels applied (target: ≥95% labeled, with
  the unmatched prefix subset surfaced for operator decision).
- Regression probe `phase-14-doc-final` PASS, no new FAIL/WARN.
- Closeout doc `PHASE_14_BLOCK_D_DOC_CLOSEOUT_<date>.md`.

### 4.3 Increments after D-DOC

D-DOC is the entry block. Subsequent Phase 14 increments consume the
backlog (items 24–30) one at a time, in roughly this order:

1. **D-DOC** (entry block) — items 13, 14, 15, 16, 17, 18, 21, 22 (folded into D-DOC); plus stale-runbook rewrites, ARCHITECTURE.md creation, Plane curation, detect-secrets tightening.
2. **D-STR** — Structurizr Lite adoption (item 24). 2–3 h.
3. **D-MKD** — MkDocs + Material adoption (item 25). 3–4 h.
4. **D-LOG** — Loki for per-site Caddy logs (item 26). 6–10 h.
5. **D-RST** — Restic backup runbook + restore-test (items 27, 28). 5–8 h combined.
6. **D-ZBX** — Zabbix Prometheus exporter (item 29). 2–4 h.
7. **D-XINDEX** — state-anchoring (g) cross-index extension beyond 4.E (item 30). 4–8 h.
8. **CL-14** — Phase 14 closeout. 2–3 h.

Total Phase 14: **8 increments**, **30–48 h** point estimate ~38 h.
Calendar: 4–8 weeks at typical operator availability.

D-STR + D-MKD are deliberately separate from D-DOC because they
introduce running services (Caddy routes, Vault paths, container
hardening), which earn their own A-011 IV&V gate per the operating
model doctrine. They cannot fold into the doctrine-only D-DOC.

D-LOG is large because the Caddy 2.11.2 missing-`host`-label
limitation requires log-shipping infrastructure (Loki + promtail or
equivalent) plus per-site dashboard authoring. Sized as a novel-
pattern block per CLAUDE.md "Known Hardening Trade-offs."

D-RST contains a quarterly restore-test commitment per CLAUDE.md
"Backup Policy" — the runbook is a one-time effort; the test cadence
is doctrine going forward.

D-XINDEX should run **after** Block 4.E (cross-index) closes in
Phase 13. It extends the cross-index to ADR↔Plane↔Vault paths that
4.E does not necessarily cover. Could be folded into 4.E if the
operator scopes broadly, or left to Phase 14 as currently planned.

---

## 5. Beyond Phase 14

### 5.1 Hardware-arrival items

Three items wait on hardware arrival (items 31–33). The campaign
plan's R-7 risk register entry already captures the topology-rewrite
risk if any of these arrives mid-Phase-13; this plan extends that to
Phase 14:

- **MacBook Pro M5 parity refresh (item 31)** — Block 3 was closed
  in Phase 13 with MacBook Pro M5 as a control-plane satellite per
  CLAUDE.md "Heterogeneous Architecture." Refresh required only if
  the MacBook Pro hardware changes (unlikely in 12 months) or if
  Mac Studio arrival reshapes the role distribution.
- **Mac Studio M3 arrival (item 32)** — pre-flagged by ADR-A-001
  "portability-first" + CLAUDE.md "future blocks beyond Block 3."
  Triggers a topology rewrite: Mac Mini may demote to "operator
  workstation" with Mac Studio taking on heavy-compute (training,
  inference, large-model orchestration). Effort 12–20 h
  (deployment + per-host vault.hcl + service migration + regression
  probe extension to two hosts).
- **Linux/Threadripper arrival (item 33)** — per-host vault config
  exists (`config/vault-configs/vault-config-linux.hcl`). Triggers
  topology rewrite, likely larger than Mac Studio (different OS,
  different observability primitives, different cAdvisor behaviour
  per CLAUDE.md). Effort 12–20 h.

If two of three arrive in close succession, expect the topology
rewrite to consume a single large increment (15–25 h) rather than
two sequential ones. Planning-time recommendation: signal expected
arrival windows ≥4 weeks ahead so the planner can size the
intervening Phase 14 increments accordingly.

### 5.2 Long-horizon evaluation items

- **OpenBao parallel-deploy (item 34)** — OpenBao is the open-source
  Vault successor (BSL→MPL fork). Evaluate as a parallel deploy
  alongside Vault, with traffic split by service over a soak window,
  before any cutover decision. ADR-A-009's "Vault as authoritative"
  decision would be re-opened by OpenBao adoption; that's a
  superseding-ADR-level change. 4–8 h evaluation; cutover (if
  approved) is a multi-increment block in its own right.
- **Backstage re-evaluation (item 35)** — `STATE_AND_TOOLING_RECOMMENDATION_2026-04-29.md`
  flagged Backstage as the right answer "in 2 years" rather than
  today. Re-evaluate after the NetBox + Structurizr + MkDocs trio
  has been live long enough to surface its pain points (typically
  6–12 months). 8–16 h evaluation; adoption (if approved) is a
  multi-increment block.

### 5.3 Cosmetic / deferred deletions

- **Item 36 — `secret/anthropic/api` Vault path deletion** (Phase 13.5
  §6 carry-over) — already gated on "no platform service consumes it";
  Phase 13.5 closed with this still pending. Per LLM Access Doctrine,
  no service should depend on it. Verify and delete in any post-13
  Vault hygiene pass.
- **Item 37 — cAdvisor friendly-name labels** — resolves on Linux
  migration; no action while platform stays Mac Mini control-plane.
- **Item 38 — `service-registry.yaml.DEPRECATED` deletion** — A-012
  §deprecation-gate. Wait until the post-flip soak window confirms no
  consumer hits the YAML fallback; then delete the file and remove
  the YAML branch from `cmdb_source.py`. ~15 min once the soak window
  is satisfied.

---

## 6. Cross-cutting concerns

### 6.1 Doctrine binding map

Each item in §2's roster has been doctrine-bound. Cross-cutting
threads:

- **A-011 (IV&V loop):** every full-IV&V sub-stage. The closeout
  backlog cluster (items 11–22) is heavy on full-IV&V because most
  involve first-contact with a per-service entrypoint or per-
  container hardening surface.
- **A-012 (equivalence harness):** five Phase 13 migrations
  (4.D.3, 4.E, 4.J, 4.I, HF-1). One Phase 14 candidate
  (D-XINDEX if it extends into write-path territory). One
  long-horizon (OpenBao cutover, if pursued).
- **A-013 (folded gates):** the doctrine that allows the backlog
  cluster to compress from "12 first-contacts" into "1 first-
  contact + 11 folds" once the canonical pattern is proven
  load-bearing.
- **CLAUDE.md non-negotiables:** the §6 sidecar rollout (item 11)
  and the §7 container hardening (item 12) are the two open items
  that breach existing platform doctrine *today*. They cannot be
  deferred to "after Phase 13" without breaching the doctrine; they
  can be deferred to "after Phase 13 close" only if the operator
  explicitly accepts the doctrine-violation tag on Phase 13's
  closeout.

### 6.2 Calendar arithmetic

| Phase | Effort (h, range) | Calendar (typical operator) |
|---|---|---|
| 13 in-scope (Increments 2–7) | 52–80 | 6–10 weeks |
| 13c closeout backlog (if folded) | 12–17 | 1–2 weeks (one increment) |
| 14 entry (D-DOC) | 8–12 | 1 week |
| 14 backlog (D-STR through CL-14) | 22–37 | 3–6 weeks |
| **Total Phase 13 + 14** | **94–146** | **11–19 weeks** |

Hardware-arrival items add 12–60 h on top, depending on which arrive.

### 6.3 Parallelism windows

D-DOC is single-operator-friendly: every sub-stage is independent
read/write against `docs/`, `config/vault-policies/`, `Caddyfile`, or
`Plane API`. Can be split across multiple short windows without
state hazard.

D-STR + D-MKD are stateful (new running containers); serialise
relative to each other but parallelise relative to D-DOC.

D-LOG is stateful (Loki + Promtail) and adds a major dependency
into the Caddy access-log path; serialise against any in-flight
Caddy work.

### 6.4 Doctrine decay risk

The campaign plan's R-8 entry is "Doctrine drift if D-OP slips."
That risk closed with Increment 1. The equivalent Phase 14 risk:
"D-DOC slips beyond ~4 weeks after Phase 13 close, the H1 §6 / §7
patterns and the Block 4.C C6 follow-ups decay into tribal knowledge
again." Mitigation: D-DOC is the **first** Phase 14 increment.
Same shape as Increment 1's role in Phase 13.

---

## 7. Risk register — top 10

Risks in priority order. Each lists *probability × impact* (rough,
based on 4.C / Increment 1 calibration), then mitigation. Inherits
all risks from the campaign plan §7 (R-1 through R-10 + R-A/R-B);
this section adds risks specific to the wider closeout horizon.

### R-11 — Hardware delivery slips into mid-block — *high × high*
Mac Studio M3 or Linux/Threadripper arriving mid-Phase-14 forces
either an interrupt-and-rewire (high blast radius) or a defer-and-
finish-current-block (calendar slip).
**Mitigation:** operator signals expected arrival ≥4 weeks ahead;
planner sizes the intervening increments to fit before arrival.
If arrival is unscheduled, finish-and-close current increment first
per R-7's mitigation, then open hardware-rewrite as a separate block.

### R-12 — Operator availability falls below ~12 h/wk — *medium × high*
Realistic calendar arithmetic assumes 12–18 h/wk peak. If operator
load drops (real-life events, illness, day-job pressure), the
6–10 weeks for Phase 13 close balloons proportionally and doctrine
decay takes hold (R-8 reborn).
**Mitigation:** prioritise doctrine-decay-sensitive blocks (D-OP-
equivalent, D-DOC) at the front of every phase. Defer novel-work
blocks rather than letting them slip while doctrine erodes. This
is the rationale for Increment 1's place in Phase 13 and D-DOC's
place in Phase 14.

### R-13 — Doctrine decay accumulates between operator windows — *high × medium*
Each block produces a closing report and updates CLAUDE.md, but
PLATFORM_OVERVIEW.md and ARCHITECTURE.md drift; ADRs accumulate
without index review. State-and-tooling discovery noted this in
2026-04-29 — A-007 ID collision and A-009 numbering jump.
**Mitigation:** D-DOC schedules an ADR-index audit + numbering
review. After D-MKD lands, the MkDocs build itself becomes a
forcing function (collisions break the nav build at edit time).

### R-14 — H1 §6 sidecar rollout surfaces silent-failure on a service entrypoint — *medium × high*
Per H1 checkpoint §6.1, the canonical pattern is built but
unproven against most images. Vaultwarden was authored as the
canonical example but not deployed. Each service's entrypoint
override (`sh -c '. /vault/secrets/credentials.env && exec
<original>'`) is image-specific; some images may not tolerate
the sourcing pattern (e.g., images using `tini` or a non-shell
PID-1).
**Mitigation:** apply per-category verification per H1 §6 amendment 2
(web=API+delivered-key check; worker=log scan; db=pg_isready;
mcp=/healthz+env; vault=token lookup). Strict 6-phase gate per
H1 §6 amendment 3 (A standalone → B db → C db-client → D infra →
E caddy → F vault). Stop and surface on first surprise.

### R-15 — Plane backlog curation 429s the platform during D-DOC — *medium × medium*
1100 issues × ~1.5 s pacing = ~28 minutes of writes; well within
60/min budget if done correctly. But concurrent platform consumers
(roadmap-sync cron, MCP server polls) compete for the same bucket.
**Mitigation:** schedule curation in a window when no other Plane
write-consumer runs. Use `framework/plane_connector.py` (with
`RateLimitError` explicit catch + first-batch verify per
`canonical-patterns/plane-connector-usage.md`). The connector was
hardened in Increment 1 specifically to make this kind of bulk
operation safe.

### R-16 — `CMDB_SOURCE` default flip surfaces a consumer that depends on YAML behaviour — *low × medium*
NetBox round-trip equivalence was proven byte-identical at C5.2
(four sha256-prefixed comparisons). But consumer behaviour over a
soak window may surface a pattern the static comparison missed
(e.g., a consumer relying on YAML's deterministic ordering vs
NetBox API's order-by-id).
**Mitigation:** flip happens after ≥1 week stable post-4.C
operational period (per campaign plan §6 prereq #4). Roll back to
`CMDB_SOURCE=yaml` is a single env-var change; effort to revert
< 5 min.

### R-17 — Memory-file plaintext token has been used between Block 4.C close and revocation — *medium × high*
The token was placed in `~/.claude/.../memory/plane_deployment.md`
during Plane setup. Its scope is workspace-wide. If a third party
gained shell access to the operator's machine between then and
now, the token is exposed.
**Mitigation:** revoke the token via Plane UI **before** doing any
other Increment 2 work. Generate a new token. Update memory file
to redact (or remove the entry entirely). Audit Plane session log
for any unrecognized API calls in the window between Block 4.C
close and revocation; if any, escalate.

### R-18 — Phase 14 backlog deferred too long, doctrine debt becomes structural — *medium × medium*
If D-STR and D-MKD slip beyond ~3 months after Phase 13 close, the
forcing functions they create (build-time ADR collision detection,
generated architecture surface) never materialise; the platform
relies on operator memory for what those tools would render.
**Mitigation:** include D-STR + D-MKD in Phase 14's first month.
They are small (2–3 h + 3–4 h) and cheap relative to their forcing-
function value.

### R-19 — Backstage adoption locks in a stack the operator regrets — *low × high*
Backstage at solo-operator scale was already evaluated as
overweight (`STATE_AND_TOOLING_RECOMMENDATION` §2.3 candidate
matrix). If the platform later expands to a small team, Backstage
becomes attractive — but adopting it without that team scale
imports an ongoing maintenance burden that NetBox + Structurizr +
MkDocs avoid.
**Mitigation:** keep Backstage adoption as a **conditional**
Phase 14+ item: only triggers if the operator-team size grows
or if NetBox+Structurizr+MkDocs surface persistent friction at
6–12 months in.

### R-20 — Doctrine A-013 fold creep — *low × medium*
A-013 explicitly limits folds to "this session." If a planning
session folds a sub-stage based on a pattern proven *in a previous
session*, the doctrine is breached and silent-failure surfaces
recur (the exact failure mode A-011 §regression closes against).
**Mitigation:** every fold decision in this plan and the campaign
plan cites the in-session precedent (e.g., "C5.2a" or "the first
consumer in §6"). Reviewers should flag any fold that cites a
cross-session precedent.

---

## 8. External prerequisites

Consolidated from campaign plan §6 plus Phase 14 entry / backlog
items. Operator-side actions only; planning or execution sessions
cannot do them unattended.

### 8.1 Already-flagged in campaign plan §6

1. Mouser API key (for 4.D / Increment 2).
2. DigiKey API credentials (for 4.D / Increment 2).
3. Components CSV at `docs/inventory/components-2026-04.csv` (for 4.D.3).
4. `CMDB_SOURCE` flip decision timing (for Increment 2 prep).
5. Gmail OAuth scope (for 4.I / Increment 4b).
6. Vision-API decision (for 4.I — claude-pro vs local).
7. Bluetooth label maker hardware (for 4.F / Increment 5).
8. Oura OAuth client (for HF-1 / Increment 6).
9. Garmin Connect access path (for HF-2 / Increment 6).
10. Local TS-store choice (HF-1 prereq per A-D-3 — VictoriaMetrics
    vs TimescaleDB vs dedicated).

### 8.2 Added by this plan

11. **Plane API token rotation** — operator action via Plane UI.
    Required before any Increment 2 work touches Plane (item 19 /
    C6 #7+#9). 5–15 min; trivial but blocking.
12. **D-DOC kickoff signal** — operator confirms whether to fold
    H1 §6/§7 + memory-token revoke into Phase 13 (Increment 1.5)
    or defer to Phase 14 D-DOC. If deferred, Phase 13 closes with
    documented doctrine violations on the books.
13. **Plane label discipline confirmation** — for the 1100-issue
    backlog curation in D-DOC, the operator must confirm whether
    the existing 64 labels are the canonical taxonomy or if a
    re-design is needed. State-anchoring discovery flagged 44/47
    prefix tokens have exact label matches; the 3 unmatched
    prefixes need operator decision.
14. **NetBox vs Backstage timeline** — explicit operator decision
    point at Phase 14 close: continue with NetBox+Structurizr+MkDocs
    trio, or evaluate Backstage. Default if no answer: continue
    trio (per `STATE_AND_TOOLING_RECOMMENDATION` recommendation).
15. **Hardware-arrival ETAs** — operator signals when Mac Studio M3
    and Linux/Threadripper are expected, ≥4 weeks ahead. Defaults
    to "no expected arrival" if unspecified.

### 8.3 Hardware-arrival gates (out-of-band)

Same as campaign plan §6, restated for completeness:

- Mac Studio M3 arrival → topology rewrite (item 32, 12–20 h).
- Linux/Threadripper arrival → topology rewrite (item 33, 12–20 h).
- Either arrival mid-block: finish-and-close current block per R-7
  / R-11 mitigation; topology rewrite is its own block.

---

## 9. Open questions for operator

These are decisions surfaced by the planning work that the operator
must answer before Phase 13 closeout. Listed in priority order; the
defaults are the recommended path if the operator does not respond.

### Q-14-1 — Fold H1 §6 / §7 / memory-token into Phase 13 (Increment 1.5)?

**Why it matters:** Items 11, 12, 19 are doctrine violations
(`.env` consumption + root-running containers + plaintext token).
Tagging Phase 13 with these open means the closeout document
records "Phase 13 closed with three documented doctrine violations
deferred to Phase 14." The operator may prefer that, or may prefer
to sweep them.

**Default if no answer:** insert Increment 1.5 (6–8 h) between
Increment 1 and Increment 2; sweep §6 + §7 + memory-token revoke
inside Phase 13. Phase 13 closes clean.

**Operator-judgement angle:** the only way to defer is a calendar
trade — Increment 1.5 is ~6–8 h and pushes Phase 13 close ~1
week. If the operator cannot afford that week, deferral is
defensible *if explicitly recorded* in the closeout doc.

### Q-14-2 — Phase 14 entry: D-DOC as the first block?

**Why it matters:** D-DOC is doctrine + hygiene work. It produces
no new running services. The alternative is to enter Phase 14 with
a feature-bearing block (e.g., D-LOG for Loki, D-STR for
Structurizr) and let doctrine debt accumulate.

**Default if no answer:** D-DOC first. Mirrors Increment 1's role
in Phase 13. Doctrine decay is the cheapest debt to pay early.

**Operator-judgement angle:** if Phase 14 has a hard external
deadline (admissions, customer demo, conference talk), D-STR or
D-MKD may be more demonstrable artifacts than D-DOC. The operator
can re-order accordingly without breaching doctrine — D-DOC
becomes Phase 14 increment 2 in that case.

### Q-14-3 — Plane backlog curation depth in D-DOC?

**Why it matters:** D-DOC includes a 1-h scripted label back-fill
(prefix → label) for the 1100-issue backlog, but full curation
(re-triage of 44 urgent → <10, close 88 done items, retire stale
items) is a separate ~4–6 h discipline pass. The plan currently
includes the back-fill but defers full curation.

**Default if no answer:** back-fill in D-DOC; full curation
deferred to a later Phase 14 hygiene increment.

**Operator-judgement angle:** the back-fill alone makes the
backlog *queryable* (priority signal returns); full curation makes
it *actionable*. Whether to invest in actionability now or later
depends on whether the operator plans to consume the backlog
themselves vs hand it to an agent or third party.

### Q-14-4 — Hardware-arrival expected ETAs?

**Why it matters:** items 31–33 size very differently depending on
whether they arrive in 6 weeks, 6 months, or 18 months. The plan
above assumed "no near-term arrival." If the operator expects Mac
Studio M3 within 8 weeks, Phase 14's calendar should reserve a
topology-rewrite increment after D-MKD rather than at the end.

**Default if no answer:** plan as written (no near-term arrival).

**Operator-judgement angle:** even an estimated month helps.
"Probably Q3" is enough information to push the topology rewrite
to Phase 14 increment 5 or 6 vs hold for Phase 15.

### Q-14-5 — OpenBao evaluation: when?

**Why it matters:** OpenBao is the BSL→MPL fork of Vault. The
platform standardised on Vault per ADR-A-009. OpenBao adoption
would re-open A-009 and is a multi-increment block (parallel
deploy + soak + cutover). The evaluation itself is 4–8 h.

**Default if no answer:** defer indefinitely. ADR-A-009's "Vault
canonical" decision is fine; the operator re-opens it only when
external pressure (license-change concerns, ecosystem migration)
materialises.

**Operator-judgement angle:** an explicit "not now, revisit in
12 months" answer prevents this item from quietly dropping off the
radar. It's a low-urgency item but the implications are platform-
wide if the answer ever changes.

---

## 10. Top 5 questions blocking immediate next-window work

If only five questions can be answered before the next operator
window opens, these are the five:

1. **Q-14-1** — Fold H1 §6/§7/memory-token into Phase 13 as Increment 1.5, or defer? *(Doctrine-violation gate.)*
2. **Q-4** *(from campaign plan §9)* — Are Mouser + DigiKey credentials achievable in operator's typical timeframe for Increment 2? *(Increment 2 cannot start until both are in Vault.)*
3. **Q-5** *(from campaign plan §9)* — Components CSV source and shape? *(4.D.3 audit needs source format before deploy.)*
4. **Q-14-2** — D-DOC as Phase 14 entry block, or feature-bearing alternative?
5. **Q-14-4** — Hardware-arrival ETAs (if any)?

The remaining questions (Q-14-3, Q-14-5, plus campaign-plan Q-6
through Q-10) can be answered in parallel with the next increment
or at audit-time per the campaign plan defaults.

---

## Appendix A — Sources cited

- `CLAUDE.md` (project doctrine, post-Block-2 follow-up list, LLM
  access doctrine, known hardening trade-offs)
- `docs/phase-13/PHASE_13_CLOSEOUT_CAMPAIGN_PLAN_2026-04-29.md`
  (full body + Appendix A sources, Appendix B calibration,
  Appendix C Q-1/2/3 lock, Appendix D doctrine-driven re-slice,
  Appendix E Q-D-1/2/3/4 lock)
- `docs/phase-13/INCREMENT_1_CLOSEOUT_2026-04-29.md` (Increment 1
  closed; PASS=15 FAIL=0 WARN=3)
- `docs/phase-13/PHASE_13_BLOCK_4C_CLOSEOUT_2026-04-29.md` (17 C6
  follow-ups; NetBox 75 services + 16 custom fields + 19 tags;
  byte-identical equivalence sha256 prefixes)
- `docs/phase-13/PHASE_13_BLOCK_H1_RESULTS_2026-04-29.md` (§0–§5
  PASS, §6 PARTIAL with 12 services pending)
- `docs/phase-13/PHASE_13_BLOCK_H1_CHECKPOINT_2026-04-29.md`
  (resume protocol; 11–13 h remaining for §6+§7+§8–§14)
- `docs/phase-13/PHASE_13_FOUNDATION_AUDIT_2026-04-29.md` (47
  .env files; 22 root-running containers)
- `docs/phase-13/STATE_ANCHORING_DISCOVERY_2026-04-29.md` (a–g gap
  taxonomy; 8 fragmented state surfaces; plaintext Plane API token
  in memory file; 70 services in registry; 5/47 metric coverage;
  12/70 Kuma coverage)
- `docs/phase-13/STATE_AND_TOOLING_RECOMMENDATION_2026-04-29.md`
  (NetBox + Structurizr Lite + MkDocs trio recommendation; 13–21 h
  estimate)
- `docs/phase-13/POST_BLOCK_4C_NEXT_OPTIONS.md` (Options A/B/C)
- `docs/adr/ADR-A-001` through `ADR-A-013` (13 ADRs, all reviewed,
  including the renumber that resolved the A-007 collision)
- `docs/adr/README.md` (ADR index; immutability + supersedes
  governance)
- `docs/runbooks/operating-model.md` (practical companion to A-011/
  A-012/A-013)
- `docs/runbooks/{H1-rollback,add-new-service,vault-recovery-from-shamir,vault-rekey,vault-token-rotation,vault-unseal,what-changed-last-24h}.md`
  (Vault-doctrine compliant)
- `docs/runbooks/{restart-services,rotate-credentials,add-new-mcp-server}.md`
  (STALE — pre-Vault-doctrine; rewrite scope for D-DOC)
- `docs/architecture/{dependency-graph,mcp-server-architecture,portability}.md`
  (mcp-server-architecture STALE)
- `docs/canonical-patterns/plane-connector-usage.md` (authoritative
  Plane connector patterns post-Increment-1)
- `docs/known-issues/KI-001` through `KI-RETIRED-rclone-sftp.md`
  (all resolved or retired)
- `docs/DECISION_REGISTER.md` (ADR navigation index, 13 ADRs)
- `docs/phase-13/h1-regression-probe.sh` (regression probe for
  every gate close)
- `git log` — commits `718a6c2` (HEAD), `258b6f4`, `7d71ec1`,
  `f495229`, `818b845`, `e3d7c17`, `c1bd29e`, `1eed06c`, `c26cfd9`,
  `e3d90fe`, `78ab414`, `ff05159`, `bed7d26`

## Appendix B — Calibration notes

This plan inherits the campaign plan's calibration: novel-pattern
blocks expect a discovery cluster of 5–10 (Block 4.C as exemplar at
17 discoveries on a deployment-shape block); mechanical-pattern
blocks expect 1–3.

The closeout-backlog cluster (items 11–22) is mostly mechanical
(per-service application of an established pattern, or doctrine
sweep). Effort estimates use the lower discovery-buffer per
campaign plan Appendix B.

D-DOC is mostly doctrine + cleanup; expect 1–3 discoveries (e.g.,
detect-secrets baseline catching a pattern not previously known,
or Plane backlog surfacing an issue the curation script can't auto-
classify).

Phase 14 backlog blocks (D-STR, D-MKD, D-LOG, etc.) are first-contact
with new tooling; expect 3–5 discoveries each, sized accordingly.

Hardware-arrival blocks (items 32, 33) are highest-discovery: they
combine novel-OS-substrate deployment + topology rewrite + per-host
config split. Estimate 5–10 discoveries; size near the high end of
the 12–20 h range.

This calibration matches Block 4.C / Increment 1 actuals and is the
basis on which §6.2 calendar arithmetic was built.

---

**Plan is complete.** Increment 1 (Phase 13) is CLOSED at commit
`718a6c2`. Increment 2 / 1.5 (operator decision) opens next. Phase 14
entry block (D-DOC) is scoped and ready for kickoff once Phase 13
closes. Beyond-14 items are catalogued for visibility but not
scheduled — they are hardware- or external-trigger-driven.

No execution begun.
