# RM-DEV-003 Execution Pack

## Objective

Establish a bounded autonomous coding baseline with explicit task contract fields,
artifact outputs, validation order, rollback rule, and promotion/escalation decision.

## Canonical machine-readable surfaces

- `governance/bounded_autonomous_codegen_contract.v1.yaml`
- `governance/rm_dev_003_rm_intel_001_linkage.v1.yaml`
- `artifacts/bounded_autonomy/runs/rm_dev_003_baseline_example.json`
- `artifacts/governance/rm_dev_003_rm_intel_001_baseline_validation.json`

## Required bounded task fields

The baseline contract requires:

- `objective`
- `allowed_files`
- `forbidden_files`
- `expected_file_posture`
- `validation_sequence`
- `rollback_rule`
- `artifact_outputs`
- `promotion_decision`

## Artifact baseline

Run artifact structure includes:

- run identity and timestamps
- bounded task contract snapshot
- planned changes and touched files
- validation results and decision
- rollback reference and emitted artifacts

## Contract usage baseline

For a bounded autonomous run:

1. Populate task fields defined in `governance/bounded_autonomous_codegen_contract.v1.yaml`.
2. Execute validation commands in `validation_sequence`.
3. Emit run evidence in `artifacts/bounded_autonomy/runs/<run_id>.json`.
4. Emit integrated governance validation evidence with `bin/run_rm_dev_003_rm_intel_001_check.py`.

## Integration with RM-INTEL-001

RM-DEV-003 depends on watchtower recommendations for key bounded-autonomy needs:

- code-edit transport adapter
- tool protocol boundary
- workspace/sandbox baseline
- retrieval memory substrate
- benchmark/qualification substrate
