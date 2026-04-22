# RM-SHOP-003

- **ID:** `RM-SHOP-003`
- **Title:** 3D model inventory, reuse, and external sourcing library
- **Category:** `SHOP`
- **Type:** `System`
- **Status:** `Accepted`
- **Maturity:** `M1`
- **Priority:** `High`
- **Priority class:** `P3`
- **Queue rank:** `16`
- **Target horizon:** `later`
- **LOE:** `XL`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `3`
- **Readiness:** `later`

## Description
Inventory local 3D models, attach semantic metadata, support whole-model and partial-geometry reuse, and search trusted external model repositories so future design work does not restart from zero.

## Why it matters
Turns accumulated 3D assets into a reusable capability rather than one-off project leftovers.

## Key requirements
- local 3D model inventory
- semantic metadata and reuse tagging
- external trusted model search
- geometry provenance and reuse lineage

## Affected systems
- workshop/3D branch
- inventory/capability-adjacent model library surfaces

## Expected file families
- future model-library schemas, search adapters, and metadata surfaces

## Dependencies
- `RM-SHOP-002`
- inventory identity discipline

## Risks and issues
### Key risks
- weak provenance or duplicate model identity
### Known issues / blockers
- first model schema and trusted-source policy still need definition

## CMDB / asset linkage
- should remain linkable to owned hardware, projects, and capability inventories where useful

## Grouping candidates
- `RM-SHOP-002`
- `RM-SHOP-004`

## Grouped execution notes
- Shared-touch rationale: 3D asset capture, reuse, and concept handoff overlap.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Define a bounded 3D model record schema and one local-plus-external search/reuse flow.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: schema, provenance rules, and initial source set are defined
- Validation / closeout condition: one bounded model-library slice supports reuse and traceable provenance
