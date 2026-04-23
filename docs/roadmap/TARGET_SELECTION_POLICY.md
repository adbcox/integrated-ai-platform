# Autonomous Target Selection Policy

Canonical target selection for governed autonomous pull is produced by:

- `bin/compute_next_pull.py`
- `artifacts/planning/next_pull.json`

Source of truth is always Layer 1 roadmap item files:

- `docs/roadmap/items/RM-*.yaml`

## Eligibility requirements

An item is eligible for autonomous pull only when all are true:

1. `status` is plannable (`proposed`, `planned`, `ready`, `in_progress`, `in_execution`, `planned_for_execution`)
2. `archive_status` is not `archived` and not `ready_for_archive`
3. all `dependencies.depends_on` items are terminal complete (`complete` or `completed`)
4. bounded execution shape exists under `ai_operability`:
   - `allowed_files`
   - `forbidden_files`
   - `validation_order`
   - `rollback_rule`
   - `artifact_outputs`
5. architecture/governance linkage is present:
   - `governance.phase_target`
   - `governance.architectural_lane`
6. execution contract is present and complete:
   - `execution_contract.autonomous_execution_status`
   - `execution_contract.next_bounded_slice`
   - `execution_contract.max_autonomous_scope`
   - `execution_contract.validation_contract`
   - `execution_contract.artifact_contract`
   - `execution_contract.completion_contract`
   - `execution_contract.truth_surface_updates_required`
   - `execution_contract.external_dependency_readiness`
7. external dependency readiness is not blocking:
   - if `external_dependency_readiness.required=true` and
     `external_dependency_readiness.blocks_autonomous_execution=true`,
     then `external_dependency_readiness.readiness_status` must be `ready`

## Explicit ineligibility

Blocked placeholder state is ineligible by rule:

- item is plannable by `status`
- but both `execution.execution_status` and `validation.validation_status` are already terminal complete/passed

These items remain blocked until canonical status is reconciled.

## Derived prioritization factors

`bin/compute_next_pull.py` uses deterministic weighted ranking from:

- priority class
- strategic value
- architecture fit
- execution risk
- dependency burden
- readiness
- autonomous execution status
- grouped execution relevance
