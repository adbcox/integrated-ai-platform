# Roadmap Standards

Roadmap rules:

- repo remains canonical
- each roadmap item has a stable `RM-*` identifier
- one machine-readable file per roadmap item
- execution and validation linkage remain in canonical records
- allowed files / forbidden files / validation order / rollback rule / artifact outputs are first-class AI-operability fields
- execution contracts are first-class canonical fields for autonomous pull eligibility
- Plane may hold operational state only
- unrestricted bidirectional sync is not allowed

## Autonomous execution contract standard

Autonomous pull is permitted only when an item has a populated `execution_contract` with:

- `autonomous_execution_status`
- `next_bounded_slice`
- `max_autonomous_scope`
- `validation_contract`
- `artifact_contract`
- `completion_contract`
- `truth_surface_updates_required`
- `external_dependency_readiness`

`completion_contract.small_patch_is_not_completion` must be `true`.

Missing contract fields, external dependency readiness blockers, and placeholder conflicts must be surfaced in machine-readable blocker output at:

- `artifacts/planning/blocker_registry.json`
