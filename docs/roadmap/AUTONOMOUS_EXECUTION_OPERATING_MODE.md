# Autonomous Execution Operating Mode

This repository runs autonomous pull in governed mode:

- selector: `bin/compute_next_pull.py`
- queue surface: `artifacts/planning/next_pull.json`
- consistency gate: `bin/validate_roadmap_consistency.py`
- runtime sovereignty gate: `bin/run_local_execution_sovereignty_check.py`
- critical path authority: `docs/roadmap/LOCAL_AUTONOMY_CRITICAL_PATH.md`

## Loop contract

The governed loop is:

1. compute eligible normalized target set from canonical item files
2. execute bounded local-first slice for the chosen target
3. run truth/consistency validations
4. update authority surfaces and artifacts
5. recompute next eligible target

## Safety constraints

- archived or ready-for-archive items cannot be pulled
- blocked placeholder items cannot be pulled
- items blocked by `execution_contract.external_dependency_readiness` cannot be pulled
- items missing execution-contract requirements cannot be pulled
- local-first runtime remains the routine path
- roadmap item files remain canonical authority for status

## Required machine-readable governance outputs

- Queue artifact: `artifacts/planning/next_pull.json`
- Blocker artifact: `artifacts/planning/blocker_registry.json`

Autonomous execution is allowed only for items with:

- normalized canonical item file
- explicit `execution_contract.autonomous_execution_status`
- bounded `next_bounded_slice` and `max_autonomous_scope`
- explicit `validation_contract`
- explicit `artifact_contract`
- explicit `completion_contract`
