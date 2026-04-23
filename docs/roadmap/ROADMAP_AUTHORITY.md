# Roadmap Authority Model

## Purpose

This document defines where roadmap truth lives, which roadmap files are derived views, and how closeout is accepted after post-convergence transition.

It exists to prevent split authority, stale status displays, and local-only closeout claims.

## Current authority model on `main`

### Layer 1 — canonical item-state authority
- `docs/roadmap/items/RM-*.yaml`

These per-item YAML files are the canonical roadmap item truth.
They control:
- item status
- archive status
- execution and validation posture
- closeout condition semantics
- dependency and sequencing metadata where recorded

If any other roadmap surface conflicts with canonical item YAML, the YAML wins.

### Layer 2 — derived planning and dependency truth
- `artifacts/planning/next_pull.json`
- `artifacts/planning/blocker_registry.json`
- `governance/roadmap_dependency_graph.v1.yaml`
- `docs/roadmap/data/roadmap_registry.yaml`
- `docs/roadmap/data/sync_state.yaml`

These surfaces must mirror canonical item truth and be regenerated through repo mechanisms.
They are not independently authoritative.

### Layer 3 — human-readable summary views
- `docs/roadmap/ROADMAP_STATUS_SYNC.md`
- `docs/roadmap/ROADMAP_MASTER.md`
- `docs/roadmap/ROADMAP_INDEX.md`

These files are summary, status-rollup, and inventory views.
They must agree with canonical item YAML and derived planning surfaces.
They must not override canonical item state.

### Layer 4 — planning and operating guidance
- `docs/roadmap/STANDARDS.md`
- `docs/roadmap/EXECUTION_PACK_INDEX.md`
- execution packs under `docs/roadmap/*_EXECUTION_PACK.md`
- `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`
- `docs/roadmap/POST_CONVERGENCE_OPERATING_MODE.md`
- `docs/roadmap/LOCAL_AUTONOMY_CRITICAL_PATH.md` (historical reference only after convergence)

These files guide planning and operation.
They do not independently control item completion state.

## Post-convergence rule

The repo is now operating in post-convergence mode.
That means:
- substrate-closure history is preserved, but not treated as current active status authority
- future work selection should assume the governed local-execution platform exists unless canonical repo truth shows regression
- closeout must remain bounded, artifact-backed, validation-backed, and truth-synchronized

## Closeout acceptance rule

No roadmap closeout is accepted until the change is:

1. committed
2. pushed
3. remote-visible

Local-only state is not accepted closeout.

## Rules

1. Always prefer canonical item YAML over summary docs.
2. Do not use `ROADMAP_MASTER.md` as direct item-status truth.
3. Do not use `ROADMAP_INDEX.md` as direct completion truth.
4. Do not use `ROADMAP_STATUS_SYNC.md` to override canonical item YAML; use it only as a synchronized status rollup.
5. Regenerate derived planning/dependency surfaces through repo mechanisms; do not hand-edit them as a substitute for canonical correction.
6. Execution packs make an item execution-ready; they do not by themselves mean the item is completed.
7. Patch success is not item completion; completion requires the item’s own canonical closeout condition to be truthfully satisfied.
8. Historical planning docs must be archived or clearly marked historical once superseded.

## Reader order

Read roadmap materials in this order:

1. `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`
2. `docs/roadmap/ROADMAP_AUTHORITY.md`
3. canonical item YAML under `docs/roadmap/items/`
4. derived planning/dependency/data surfaces
5. `docs/roadmap/ROADMAP_STATUS_SYNC.md`
6. `docs/roadmap/ROADMAP_MASTER.md`
7. `docs/roadmap/ROADMAP_INDEX.md`
8. `docs/roadmap/POST_CONVERGENCE_OPERATING_MODE.md`
9. planning/supporting docs as needed

## Repair note

This authority model replaces an earlier visible-status-first model that was useful during recovery but is no longer correct after convergence to canonical per-item YAML.