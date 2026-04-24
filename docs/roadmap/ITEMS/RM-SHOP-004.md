# RM-SHOP-004

- **ID:** `RM-SHOP-004`
- **Title:** Outdoor structure concept design and architect handoff
- **Category:** `SHOP`
- **Type:** `Enhancement`
- **Status:** `In progress`
- **Maturity:** `M1`
- **Priority:** `High`
- **Priority class:** `P3`
- **Queue rank:** `17`
- **Target horizon:** `later`
- **LOE:** `L`
- **Strategic value:** `3`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `later`

## Description
Extend the woodworking/design capability so the system can generate outdoor-structure concept packages for fences, boat docks, and similar builds using adopted OSS design tools, producing architect-readable handoff material rather than final engineered packages.

## Why it matters
Creates a practical concept-to-handoff workflow for outdoor structure planning without overreaching into final engineering responsibility.

## Key requirements
- support concept design for outdoor structures
- produce architect-readable handoff packages
- use adopted design tools where suitable
- avoid presenting concept packages as final engineered outputs

## Affected systems
- workshop/design branch
- future concept-package generation surfaces

## Expected file families
- future concept-design workflow docs
- future handoff-output schemas or templates

## Dependencies

## Risks and issues
### Key risks
- confusing concept output with engineered output
### Known issues / blockers
- first bounded structure type and handoff format still need definition

## CMDB / asset linkage
- may later link to owned site/project records and tool/material inventories where relevant

## Grouping candidates

## Grouped execution notes
- Shared-touch rationale: concept design, 3D capture, and model-library reuse overlap.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Define one bounded outdoor-structure concept workflow and one architect-handoff output format.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: first structure type and output scope are explicitly defined
- Validation / closeout condition: one concept-design-to-handoff slice exists with clear output limits
