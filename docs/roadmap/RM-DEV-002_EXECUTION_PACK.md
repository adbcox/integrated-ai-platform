# RM-DEV-002 Execution Pack

## Objective

Establish a machine-readable QC finding/result baseline for dual-model inline
review loops so bounded coding outputs can be classified, audited, and reused.

## Canonical machine-readable surfaces

- `governance/qc_finding_schema_rm_dev_002.v1.yaml`
- `governance/rm_dev_002_qc_result_template.v1.json`
- `governance/rm_dev_003_rm_intel_001_linkage.v1.yaml`
- `artifacts/governance/rm_integrated_5_item_validation.json`

## Required QC finding classes

- correctness
- safety
- structural
- style_noise

## Required QC output behavior

- machine-readable findings with severity and remediation guidance
- explicit target linkage to bounded task/run artifacts
- write-back envelope for pattern/memory accumulation

## Integration with other roadmap items

- validates bounded run outputs from `RM-DEV-003`
- uses local-autonomy boundaries from `RM-DEV-005`
- can apply verified OSS tooling candidates sourced from `RM-INTEL-002` / `RM-INTEL-001`
