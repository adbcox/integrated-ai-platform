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

## Explicit ineligibility

Blocked placeholder state is ineligible by rule:

- item is plannable by `status`
- but both `execution.execution_status` and `validation.validation_status` are already terminal complete/passed

These items remain blocked until canonical status is reconciled.
