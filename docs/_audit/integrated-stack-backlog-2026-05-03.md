# D-17-32 — Prioritized hardening backlog

**Date:** 2026-05-03
**Source:** `integrated-stack-gaps-2026-05-03.md` (17 gaps across 6 flows + 3 cross-flow seams)
**Constraint:** Audit-only deliverable. No remediation deliverables auto-created here. Operator queues new deliverables in next planning pass.
**Operator confirmation:** ordering confirmed 2026-05-03 (B1 → B2 → B3 → B4 → D-tier → N-tier). F5 added late under operator instruction after empirical confirmation via separate Sonarr troubleshooting session (QNAP SMB mount break went undetected by all platform health signals).

---

## Tier B — Blocks autonomous coding outright (4 gaps)

| Rank | Gap | Effort | Existing roadmap item? | Action |
|------|-----|--------|------------------------|--------|
| **B1** | **F1** — `autonomous-coding` category missing in OpenProject; CLAUDE.md doctrine "filter by category=autonomous-coding" returns nothing. Sync falls back to `[auto]` description marker (21 items carry it; 0 carry the category). | ~15 min op + 5 min sync | **None** — D-17-31 closed assuming the category existed. | **NEW micro-deliverable proposed**: create category in OpenProject UI → re-run sync `--include-roadmap` → verify 21 RM items take the category → update CLAUDE.md if filter syntax changes. Highest leverage-per-minute in the audit. |
| **B2** | **X1** — Service registry has no MCP/agent surface. D#25 mandates consultation but the only path is a 4-line Python snippet pasted into CLAUDE.md. xindex MCP exposes services-as-NetBox-rows but not registry's port/credential/depends_on metadata. | ~3-5h | **None.** Closest: RM-16-B-008 (cross-index InvenTree axis) — adjacent but doesn't cover registry. | **NEW deliverable proposed**: `xindex_get_registry_record` tool OR standalone `registry-mcp` server. Wraps `~/.platform-registry/inventory.json` + `by-service/*.json` with last-refresh staleness signal. Closes D#25 doctrine ↔ execution gap. |
| **B3** | **C1** — No asset / firmware / OS state register exists. The 2026-05-02 macOS upgrade that triggered the D-17-25 reboot was AI-recommended without any state consult — there was nothing to consult. Spans hosts + accessories per Finding T scope. | ~30-50h (deliverable family) | **None active.** Asset-mgmt A/B/C/D scope is intake-doc'd in operator memory only — not framework-authored. | **NEW deliverable family proposed**: needs framework authoring before queueable. Author scope doc as separate intake deliverable in next planning pass; will become D-17-NN-A through D-17-NN-D (or Phase-18 candidates). |
| **B4** | **F5** — Container health checks validate liveness, not integration paths. Empirical: 2026-05-03 Sonarr/QNAP SMB mount break went undetected by all platform health signals (container `(healthy)`, Zabbix green, Uptime Kuma green) for unknown duration; surfaced only by operator-observed import failure in separate troubleshooting session. Agents trusting health-check signal will operate on false-positive state. | ~20-40h (deliverable family) | **None.** Phase 6/7 closeouts asserted "monitoring complete" at container layer — integration-layer claim is doctrine drift not previously surfaced. | **NEW deliverable family proposed**: end-to-end integration health checks. Tier examples: F5-A inference path (exo → litellm → Open WebUI roundtrip), F5-B media stack (SMB mount + container access + file move + library refresh), F5-C secret propagation (Vault → Vault Agent sidecar → `/proc/1/environ` per Finding DD), F5-D backup verification (Restic snapshot + restore-to-tmpdir). Doctrine outcome: explicit chronicle "container `(healthy)` is not `(integration working)`." Cross-cuts B3 — asset register catches firmware/OS drift; F5 catches *flow* drift. Both needed. |

---

## Tier D — Degrades autonomous coding quality (8 gaps)

| Rank | Gap | Effort | Existing item? | Action |
|------|-----|--------|----------------|--------|
| **D1** | **A3** — Studio Ollama not in litellm gateway; single-node only on Mini. | ~1-2h | RM-16-A-001 + 002 (queued) | Carry-over; queue when Studio inference is re-attempted. Already correctly tracked. |
| **D2** | **A1** — Inference route enumeration is 3-step process for agent (registry → bearer → `/v1/models`). | ~2h | None | NEW micro-deliverable proposed: registry record per litellm route with backend pointer. |
| **D3** | **B1** — InvenTree empty + cross-index has no InvenTree axis → Flow B inoperative end-to-end. | ~25-40h | RM-16-B-004 (CSV import), RM-16-B-008 (cross-index axis), RM-16-B-005/006 (suppliers) | Carry-over from Phase-16 backlog; promote into active phase if asset family is started (overlaps with B3). |
| **D4** | **B2** — Hardware substrate (Mac Mini / Studio / accessories) not catalogued; InvenTree is for *parts*, NetBox is for *nodes*; no surface for "this Mini's NVMe firmware + RAM supplier + connected accessories". | family scope | None (subsumed by B3) | Subsumed by B3 (asset-management family). |
| **D5** | **C2** — Container image staleness has no surface. | ~6-8h | RM-16-C-003 (queued) | Carry-over; depends on Studio rotation. |
| **D6** | **D1** — Provenance JSONs in `docs/_provenance/` not enumerable by agent. | ~3-4h | None | NEW micro-deliverable proposed: xindex axis or MCP getter for provenance state. |
| **D7** | **E1** — Architecture-facts chronicles not searchable via xindex (`xindex_get_architecture_fact` missing; chronicles not in FTS5 corpus). | ~3-5h | None | NEW micro-deliverable proposed: add `architecture-facts` axis to xindex. |
| **D8** | **F2** — CLAUDE.md documents `--query-backlog` flag that doesn't exist in sync script. | ~5 min (doc fix) OR ~30 min (implement flag) | None | Doctrine fix: edit CLAUDE.md to match actual flags. Implementation of `--query-backlog` would actually be useful (read-only backlog query); operator decision. |
| **D9** | **F4** — `RM-HW-001` / `RM-HW-002` (ESP32 / Nordic hardware design scope) stranded in `docs/_archive/plane-export-2026-05-02.json`; never carried into OpenProject during D-17-04 plane retirement (regex didn't match `RM-HW-*`). | ~30 min triage + 0-2h | Archive only | **NEW deliverable proposed**: triage carry-forward (Phase-18 candidates as `RM-18-A-006/007`) OR explicit deliberate-not-carried documentation. Operator decision in next planning pass. |

---

## Tier N — Nice-to-have hardening (6 gaps)

| Rank | Gap | Notes |
|------|-----|-------|
| **N1** | **A2** — Ollama+Goose tool-calling streaming gap. | Upstream-blocked (Findings 1+2 in `local-tool-calling.md`). No action; revisit signal documented. |
| **N2** | **D2** — Wrapper-enforcement is convention, not enforced. | Pre-commit hook or shell alias; low-priority because D6 (D1 enumeration) catches violations after-the-fact. |
| **N3** | **E2** — CLAUDE.md hardware IP drift (Studio listed `.146`, actual `.142`). | Already captured by D-17-18 SMOKE; trivial doctrine edit; can be folded into next CLAUDE.md cycle. |
| **N4** | **F3** — 621 unversioned WPs from legacy Plane import contributing to backlog noise. | Bulk-assign to `Imported-Pre-Sync` version OR ignore. Low priority. |
| **N5** | **X2** — launchd not registered for registry refresh. | Auto-recovers on next operator login per macOS launchd convention. |
| **N6** | **X3** — Vault cold-start order not automated. | Reserved post-demo per Finding Z. Architectural decision; not a bug. |

---

## Recommended next-phase queue actions

These are **not auto-created** by D-17-32. Operator decides at next planning pass.

| New deliverable proposed | Closes gap(s) | Sized | Priority |
|--------------------------|---------------|-------|----------|
| Create `autonomous-coding` category + re-sync | F1 (B1) | ~20 min | Immediate |
| Registry MCP surface | X1 (B2) | ~3-5h | High |
| Asset-management family scope authoring | C1 (B3) — intake | ~2-3h authoring | High |
| Asset-management family A/B/C/D | C1 (B3) — implementation | ~30-50h | After scope authored |
| Integration health-check family scope authoring | F5 (B4) — intake | ~2-3h authoring | High |
| Integration health-check family A/B/C/D | F5 (B4) — implementation | ~20-40h | After scope authored |
| litellm route enumeration | A1 (D2) | ~2h | Medium |
| Provenance enumeration MCP | D1 (D6) | ~3-4h | Medium |
| Architecture-facts xindex axis | E1 (D7) | ~3-5h | Medium |
| RM-HW-* triage | F4 (D9) | ~30 min + decision | Medium |
| CLAUDE.md doctrine drift fixes | F2 (D8) + E2 (N3) | ~15 min combined | Low (housekeeping) |

---

## Doctrine takeaway

**Stack-integration audit becomes a recurring deliverable at every phase boundary.**

Subsystem-level closure does not equal integrated-system-level capability. Phase 17 produced 25 deliverables that each closed on their own scope; this audit found 17 gaps in how those subsystems compose into the autonomous-coding flow the operator's goal requires.

Going forward, every phase plan must include a stack-integration audit as a phase-close deliverable (named `D-NN-INT` or equivalent). Audit format: enumerate target flows for the phase's autonomous-coding posture, trace each end-to-end, classify gaps B/D/N, surface back to operator before queueing remediation.

This audit (D-17-32) is the canonical reference for the format.

**Companion doctrine (F5):** "container `(healthy)` is not `(integration working)`." Phase 6/7 monitoring scope was container-layer; the integration-layer scope was assumed-but-not-built. Going forward, any deliverable that asserts "monitoring complete" must explicitly state which layer (container liveness vs integration-path validation) and not the other.

---

## Notable secondary findings

1. **D-17-31 close-loose-ends (3 gaps).** F1 (missing category), F2 (nonexistent flag in CLAUDE.md), and the description-marker fallback path were all close-loose-ends from D-17-31. Future deliverables that assert doctrine ("agents should filter by X") must verify the surface exists at close time, not assume.

2. **Parallel-session cross-check (negative datapoint).** Operator concern about a parallel Claude session creating an ESP32 roadmap artifact via a different chat window was investigated as part of WP-04. Audit trail: zero new commits in last 3 hours, zero new files, zero new WPs in OpenProject matching ESP32/KiCad/EDA scope. The two RM-HW items in the plane archive are pre-existing (D-17-04 close-loose-end → Gap F4). **D-17-31's roadmap → OpenProject sync mechanism remains untested by external work since its 2026-05-03 close.** Do not claim positive validation that didn't happen.

3. **B-tier concentration in seams, not in subsystems.** All 3 B-severity gaps (F1, X1, C1) live in seams *between* subsystems, not within any single subsystem. Consistent with the operator's framing: subsystems work; integration is what's missing.
