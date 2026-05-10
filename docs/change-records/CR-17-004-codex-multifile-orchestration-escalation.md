---
cr: CR-17-004
title: Codex / multifile orchestration agentic work escalated to Phase 18 agentic-execution-layer
status: applied
source_phase: Phase-17
target_phase: Phase-18
discovered: 2026-05-11
applied: 2026-05-11
affected_deliverables: [D-17-117, D-17-118, D-17-124, D-17-125, D-17-126, D-17-127, D-17-128, D-17-129]
summary: 8 deliverables covering Codex replacement benchmark, multi-task envelope benchmarking, routing classifier alignment, agent trace pipeline, and recurrence calibration retrospectively escalated to Phase 18 agentic-execution-layer.
---

# CR-17-004: Codex / multifile orchestration escalation

## Summary

Eight deliverables represent agentic execution improvement work
parallel to (and partly overlapping) the Aider stack from CR-17-001:
Codex 5.x replacement benchmarking, multi-task envelope benchmarks,
routing classifier alignment, internal agent trace pipeline,
multi-file orchestration recurrence reduction, recurrence calibration,
and codex51 campaign expansion. Same Phase 18 target.

## Affected deliverables

| ID | Title | Status |
|---|---|---|
| D-17-117 | Multi-task envelope benchmark + wrapper E2E regression | DONE |
| D-17-118 | Routing classifier alignment with empirical envelope | IN PROGRESS |
| D-17-124 | Internal agent trace pipeline | DONE |
| D-17-125 | Codex 5.x replacement benchmark, attribution, and learning loop | DONE |
| D-17-126 | Multi-file orchestration recurrence reduction candidate | IN PROGRESS |
| D-17-127 | Commit D-126 pending work + recurrence calibration | DONE |
| D-17-128 | Calibrate recurrence_rate metric for small task_count + close D-17-127 | DONE |
| D-17-129 | Expand codex51 campaign run set to N>=30 distinct tasks | NOT STARTED |

## Rationale

Codex (OpenAI's CLI) joined Claude Code + Goose as a third execution
surface during Phase 17 execution. The associated benchmarking
infrastructure (multi-task envelope, agent trace pipeline, recurrence
metrics) is execution-surface-improvement work, not Phase 17 audit /
consolidate / governance scope.

The routing classifier work (D-17-118) directly composes with
CR-17-001's D-17-95 three-tier classifier; both belong in the same
Phase 18 agentic-execution-layer grouping.

The CR mechanism wasn't enforced when these landed; retrospective
escalation aligns them with the agentic-execution-layer grouping.

## Disposition

- All 8 deliverables retain their `D-17-NN` IDs.
- Intrinsic status preserved (5 DONE + 2 IN PROGRESS + 1 NOT STARTED).
- Phase grouping moves to Phase 18 agentic-execution-layer (with CR-17-001).
- §9 rows gain `→ ESCALATED-TO-PHASE-18 via CR-17-004 (2026-05-11)` annotation.
- Phase 17 closeout criteria do NOT block on these deliverables.

## Cross-references

- Sibling CR: `CR-17-001` (Aider agentic stack — same Phase 18 target).
- Sibling CR: `CR-17-005` (Goose Phase-13+ stack — same Phase 18 target).
- D-17-13 (Goose agent CLI integration) — Phase 17 in-spirit precursor establishing the multi-surface pattern.
- D-17-53 (Local AI execution-surface migration framework) — Phase 17 in-spirit doctrine governing the migration these deliverables enact.

## Audit trail

- 2026-05-11: CR authored retrospectively. Phase 17 scope triage Stage 2 bulk processing.
