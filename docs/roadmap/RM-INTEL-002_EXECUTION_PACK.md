# RM-INTEL-002 Execution Pack

## Objective

Establish a verified OSS capability-harvest layer that validates candidate fit and
risk posture before watchtower recommendation decisions are promoted.

## Canonical machine-readable surfaces

- `governance/verified_oss_capability_harvest_rm_intel_002.v1.yaml`
- `governance/oss_watchtower_candidates.v1.yaml`
- `governance/rm_dev_003_rm_intel_001_linkage.v1.yaml`
- `artifacts/governance/rm_integrated_5_item_validation.json`

## Required harvest decision classes

- `adopt-now`
- `evaluate`
- `watch`
- `reject`

## Required compatibility/risk checks per candidate

- architecture fit vs current local-first stack
- duplication risk against existing shortlist/surfaces
- privacy/local-first constraint posture
- architecture drift risk
- watchtower projection linkage

## Integration with other roadmap items

- feeds validated candidate outcomes into `RM-INTEL-001` watchtower registry
- supplies governed adoption directions to `RM-DEV-005`
- informs bounded tooling/sandbox/retrieval choices for `RM-DEV-003`
- supplies QC/tooling candidates consumed by `RM-DEV-002` finding workflows
