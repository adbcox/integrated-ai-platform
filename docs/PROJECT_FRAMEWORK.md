# Project Framework — labels, lifecycle, communication

**Status**: Living doctrine (this document is updated when conventions change)
**Adopted**: 2026-05-01 during Phase 15
**Context**: PMP-aligned project structure + ITIL-aligned operational classification

This document is the canonical reference for how work on the Integrated AI Platform is labeled, sequenced, and communicated. The operator's background is PMP + ITIL; control / execution windows align with these conventions to make rollup, status, and cross-window communication unambiguous.

For historical phase records, see `docs/PHASE_LOG.md`.
For upcoming roadmap, see `docs/PHASE_ROADMAP.md`.
For multi-window operating discipline, see `docs/runbooks/operating-model.md`.

---

## 1. Project structure (PMP-aligned)

| Term | Meaning here | Example |
|---|---|---|
| **Project** | The platform as a whole | Integrated AI Platform |
| **Phase** | Numbered milestone block with charter, deliverables, closeout | Phase 15 |
| **Deliverable** | Concrete tracked output of a phase | D-15-02 (information architecture hygiene) |
| **Work Package** | Smallest planned executable unit; one execution-window run | WP-15-02-T4 (ADR README index) |
| **Task** | A single named action inside a work package | T4 (read-then-add ADR rows) |

### Phase lifecycle

Each phase has four stages:

1. **Open** — phase opens with a written charter listing planned deliverables
2. **Execute** — work packages dispatched to execution window, one or more per deliverable
3. **Verify** — each work package surfaces with PASS / SKIP / FAIL status; each deliverable closes when its tasks resolve (PASS or explicitly deferred)
4. **Close** — phase closeout doc authored when all deliverables resolved; phase tagged in git as `phase-NN-final`

A phase does NOT close while deliverables are open without an explicit deferral decision recorded in the closeout doc. Drift between "scope said" and "actually closed" must be visible.

---

## 2. Operational classification (ITIL-aligned)

| Term | Meaning here | Example |
|---|---|---|
| **Service** | Deployed thing tracked in `config/service-registry.yaml` (or NetBox post ADR-A-014) | NetBox, Vault, AnythingLLM |
| **Change Record** | Tracked modification with pre-flight, execution, verification | CR-15-001 (audit + validation commit) |
| **Incident** | Unplanned outage, severity-classified, postmortem required | Sev-2 Vault cascade 2026-04-30 |
| **Problem** | Root cause behind one or more incidents | "No PreToolUse hooks for destructive Vault operations" |
| **Risk** | Identified but not-yet-realized issue with mitigation plan | R-01 backup chain broken |
| **Known Issue** | Documented limitation accepted as live | KI-001 plane-api OOM (resolved); KI-003 obot dev-mode (open) |

A change record is the unit of work-package execution; when a WP runs, it IS a change. The pre-flight + surface format ARE the change-control gate.

### Severity scale (incidents)

| Severity | Definition |
|---|---|
| Sev-1 | Platform unavailable; data loss imminent or in progress |
| Sev-2 | Major capability lost; recovery in progress with concrete fallback |
| Sev-3 | Service degraded; capability impaired but not lost |
| Sev-4 | Issue identified; no user-visible impact yet |

---

## 3. Label format conventions

| Pattern | Meaning |
|---|---|
| `Phase-NN` | Phase NN |
| `D-NN-MM` | Deliverable MM under Phase NN |
| `WP-NN-MM-XX` | Work Package XX under Deliverable D-NN-MM |
| `T-N` (or `Tn`) | Task N within a work package |
| `CR-NN-NNN` | Change Record (zero-padded) |
| `R-NN` | Risk |
| `S-NN` | Audit/finding signal (used inline in audits, e.g. S9-F1) |
| `D#NN` | Doctrine point captured during a phase (e.g. D#25) |
| `XF-N` | Cross-cutting finding (used in audits) |
| `KI-NNN` | Known Issue (Phase 7-era convention; preserved) |
| `Sev-N` | Incident severity |

Labels are stable once issued. If scope changes, the label is closed (`SUPERSEDED by`, `DEFERRED to`) and a new label is issued. Re-using a label for new scope creates traceability rot and is forbidden.

---

## 4. Surface format template

When a work package runs, the execution-window surface format is mandatory:

```
STATUS: <WP-id> <PASS|PASS-PARTIAL|SKIP|FAIL>
<task-1-id>: <PASS commit-hash | SKIP reason | FAIL>
<task-2-id>: ...
DELIVERABLE <D-NN-MM> STATE: <N of M tasks complete>
PHASE <NN> STATE: <N of M deliverables complete>
COMMITS LANDED THIS RUN: <count + hashes>
ERRORS LOGGED: <count, one-line summary each>
WORKING TREE NOW: <git status --short output>
TIME ELAPSED: <minutes>
```

This makes phase rollup automatic. A status request ("where are we on Phase 15?") is answered with deliverable counts and concrete commit hashes, not narrative.

The surface format is part of the change-control gate. Skipping it converts a Change Record into an undocumented change — which is the precondition the platform is being hardened against.

---

## 5. Phase numbering — historical note

Phase numbering was **consolidated at commit `a6253c3` (2026-04-29)**.

Prior to consolidation, phases were micro-numbered (Phase 7 Caddy CA Trust, Phase 10 Strava OAuth, the old Phase 16 Vault Architecture Restoration — note that the old "Phase 16" predates and is unrelated to the future new Phase 16 work). After consolidation, phases are larger blocks with named tracks inside.

Mapping between numbering schemes is preserved in `docs/PHASE_LOG.md` with a renumbering note dividing the two regions of the file.

For any phase number referenced in code, docs, or commits, check the date — pre-2026-04-29 references use the old scheme. The current numbering line continues forward from Phase 13 / 14 / 15.

---

## 6. Multi-window operating model

The platform is operated across multiple Claude windows by design. Roles split as:

| Window | Role | What it does |
|---|---|---|
| **Master Project Manager** (control / planning) | Plans, verifies, sequences | Drafts WP prompts; cross-references with audits + chats; surfaces decisions |
| **Execution** (Claude Code on Mac Mini) | Executes bounded WPs | Runs pre-flight, applies changes, surfaces |
| **Sibling planning** (other chats) | May run in parallel | Subject to MPM verification before any output is forwarded to execution |

Detailed multi-window discipline lives in `docs/runbooks/operating-model.md`.

The MPM never bypasses the Execution window for repository changes. The Execution window never expands scope beyond the WP it received.

---

## 7. Phase 15 — current state

**Phase 15 — Vault Recovery + Information Architecture Hygiene** (opened 2026-04-30)

Originally chartered for Vault cascade recovery + Mac Studio Day-1 integration. Mac Studio Day-1 deferred per Path C scope decision (operator, 2026-05-01) and re-targeted to Phase 16. Phase 15 closeout scope is now audit-driven.

| Deliverable | Status | Reference |
|---|---|---|
| D-15-01: Audit + validation committed | DONE | commit 3105f07 |
| D-15-02: Information architecture hygiene | IN PROGRESS | T2/T3/T4/T5/T6 done; T1+T1' pending |
| D-15-03: Backup chain repaired | NOT STARTED | R-01 |
| D-15-04: Vault audit device re-enabled | NOT STARTED | R-02 |
| D-15-05: PreToolUse hooks shipped | NOT STARTED | R-03 |
| D-15-06: vault-test instance live | NOT STARTED | R-08 |
| D-15-07: ADR-A-007 dirty edit resolved (Path B) | NOT STARTED | S9-F3 |
| D-15-08: Loose-doc retirement pass | NOT STARTED | beyond-audit |
| D-15-09: Phase 15 closeout doc + tag `phase-15-final` | NOT STARTED | last |
| D-15-10: This framework doc committed | IN PROGRESS | (this doc) |

**Phase 15 deferred to Phase 16:**
- Mac Studio Day-1 (3 pre-actions still apply when re-opened)
- Block 4.D retroactive closeout (InvenTree)
- Block 4.E cross-index service (structural blocker for autonomous coding)

When a deliverable closes, this table receives a commit hash and status flips to DONE. The table is the single source of truth for Phase 15 progress; sibling sources (chat history, prior plans) are advisory only.

---

## 8. References

- `docs/PHASE_LOG.md` — historical phase records (pre and post consolidation)
- `docs/PHASE_ROADMAP.md` — upcoming roadmap
- `docs/runbooks/operating-model.md` — multi-window operating discipline
- `docs/adr/` — architectural decisions (immutable once Accepted)
- `CLAUDE.md` — current operational truth (root)
- `docs/ARCHITECTURE.md` — current architecture (supersedes PLATFORM_OVERVIEW.md)
- `docs/phase-15/COMPREHENSIVE_AUDIT_2026-05-01.md` — current-phase audit (committed 3105f07)
- `docs/phase-15/COMPREHENSIVE_AUDIT_VALIDATION_2026-05-01.md` — current-phase audit validation (committed 3105f07)
