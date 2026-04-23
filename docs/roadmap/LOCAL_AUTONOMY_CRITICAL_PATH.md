# Local Autonomy Critical Path

This document captures the current critical path for maintaining trustworthy local-first
roadmap autonomy after RM-OPS-007 archive convergence.

## Purpose

- Define the minimum authoritative path that must stay healthy for governed autonomous pull.
- Keep canonical-vs-derived truth rules explicit while roadmap state changes quickly.
- Prevent drift between item files, planning artifacts, and human summary surfaces.

## Canonical Rule

- Canonical authority is always `docs/roadmap/items/RM-*.yaml`.
- Derived planning and summary surfaces must mirror canonical item truth.
- If any contradiction exists, item files win and derived layers must be repaired.

## Current Runtime Posture (2026-04-23)

- Local execution sovereignty is affirmative (`verdict: YES`):
  - `governance/local_execution_sovereignty_status.v1.yaml`
  - `artifacts/autonomy/local_execution_sovereignty_verdict.json`
- Governed selector is active:
  - `bin/compute_next_pull.py`
  - `artifacts/planning/next_pull.json`
  - `artifacts/planning/blocker_registry.json`

## Critical Path Gates

1. Canonical item truth integrity:
   - Item status/archive fields must remain coherent.
   - Execution/validation evidence fields must support terminal-state claims.

2. Derived planning integrity:
   - `next_pull.json` and `blocker_registry.json` must be regenerated after canonical changes.
   - `governance/roadmap_dependency_graph.v1.yaml` must remain in sync.

3. Summary-layer integrity:
   - `ROADMAP_MASTER.md`, `ROADMAP_INDEX.md`, and `ROADMAP_STATUS_SYNC.md` must reflect canonical states.
   - Archived items must not be represented as active or pull-eligible.

4. Archive convergence integrity:
   - RM-OPS-007 convergence decisions must remain machine-readable:
     - `artifacts/operations/rm_ops007_archive_convergence_report.json`
     - `artifacts/validation/rm_ops007_convergence_validation.json`
   - Held `ready_for_archive` items require explicit reasoned hold until evidence changes.

## Current Hold Set

- none

## Required Validation Order

1. `python3 bin/compute_next_pull.py`
2. `python3 bin/validate_roadmap_consistency.py`
3. `python3 bin/validate_roadmap_execution_contracts.py`
4. `make check`
5. `make quick`

## Stop Conditions

- Stop and repair immediately if:
  - canonical item truth conflicts with derived planning outputs, or
  - summary docs contradict canonical archive/status state, or
  - governed selector exposes archived items as eligible.
