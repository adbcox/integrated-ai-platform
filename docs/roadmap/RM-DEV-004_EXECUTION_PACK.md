# RM-DEV-004 Execution Pack

## Objective

Deliver a bounded embedded firmware assistant baseline for Nordic and ESP
platforms with machine-readable workflow and artifact contracts.

## Canonical machine-readable surfaces

- `governance/firmware_assistant_baseline.v1.yaml`
- `governance/trust_boundary_policy.v1.yaml`
- `governance/indexed_retrieval_backend.v1.yaml`
- `artifacts/governance/rm_bundle_6_closeout_validation.json`

## Required scope

- Nordic (`nRF52`, `nRF53`) and ESP (`ESP32`, `ESP32-S3`, `ESP32-C3`) support
- bounded workflow: plan → build → validate → QC
- artifact outputs per firmware run

## Integration

- retrieval support from `RM-DEV-007`
- QC output contract from `RM-DEV-002`
- trust-boundary enforcement from `RM-CORE-005`
