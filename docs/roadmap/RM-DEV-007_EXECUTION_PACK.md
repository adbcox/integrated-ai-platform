# RM-DEV-007 Execution Pack

## Objective

Establish indexed code search and multi-repo retrieval baseline with explicit
backend decisions and integration posture for coding + firmware workflows.

## Canonical machine-readable surfaces

- `governance/indexed_retrieval_backend.v1.yaml`
- `framework/codebase_repomap.py`
- `governance/asset_execution_linkage.v1.yaml`
- `artifacts/governance/rm_bundle_6_closeout_validation.json`

## Required scope

- primary backend selected and documented (`repomap_generator`)
- secondary options classified (`ast-grep`, `zoekt`)
- multi-repo contract (roots/excludes/output types)

## Integration

- supports `RM-DEV-004` firmware context retrieval
- supports `RM-DEV-002` QC-guided coding path
- constrained by `RM-CORE-005` trust boundary policy
