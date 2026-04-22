# RM-INTEL-001 Execution Pack

## Objective

Establish an OSS watchtower baseline that tracks candidates, update posture, and
adoption recommendations for roadmap-linked implementation decisions.

## Canonical machine-readable surfaces

- `governance/oss_watchtower_candidates.v1.yaml`
- `governance/verified_oss_capability_harvest_rm_intel_002.v1.yaml`
- `governance/rm_dev_003_rm_intel_001_linkage.v1.yaml`
- `artifacts/governance/rm_integrated_5_item_validation.json`

## Required candidate fields

Each candidate entry includes:

- `name`
- `category`
- `source_url`
- `license`
- `maintenance_signal`
- `integration_role`
- `roadmap_linkage`
- `recommendation_class` (`adopt-now`, `evaluate`, `watch`, `reject`)
- `removal_fallback_posture`
- `notes`

## Starter shortlist for local development assistant stack

- Ollama
- Aider
- MCP
- OpenHands SDK
- Qdrant
- gVisor
- SWE-bench
- Continue

## Integration with RM-DEV-003

Watchtower recommendations are linked directly to RM-DEV-003 bounded-autonomy needs
through:

- capability-needs to candidate mappings
- recommendation rationale per need
- fallback posture for safe bounded operation

## Integration with RM-INTEL-002

Watchtower entries are projected from verified harvest outputs in:

- `governance/verified_oss_capability_harvest_rm_intel_002.v1.yaml`
