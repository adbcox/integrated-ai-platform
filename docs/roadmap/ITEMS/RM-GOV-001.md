# RM-GOV-001

- **ID:** `RM-GOV-001`
- **Title:** Integrated roadmap-to-development tracking system with CMDB linkage, standardized metrics, enforced naming, and impact transparency
- **Category:** `GOV`
- **Type:** `System`
- **Status:** `Completed`
- **Maturity:** `M3`
- **Priority:** `Critical`
- **Priority class:** `P1`
- **Queue rank:** `5`
- **Target horizon:** `soon`
- **LOE:** `XL`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `3`
- **Dependency burden:** `3`
- **Readiness:** `near`

## Description

Build an integrated roadmap-to-development tracking system that connects roadmap items to execution, completion, and system inventory with standardized metrics, CMDB linkage, naming enforcement, impact transparency, and grouped-execution support.

## Why it matters

This item is one of the central governance systems of the platform. It reduces planning drift, creates continuity from architecture to roadmap to execution, and improves the quality of future autonomous or semi-autonomous work by making scope, priority, dependencies, and impact more explicit.

## Key requirements

- structured roadmap items with stable IDs and normalized fields
- explicit metrics for LOE, value, fit, risk, and sequencing
- naming enforcement and impact-scope declaration
- roadmap linkage to systems, assets, and future CMDB surfaces
- grouped execution support for shared-touch packages
- clear movement from intake to execution to completion

## Affected systems

- roadmap governance layer
- architecture alignment layer
- future CMDB and capability-mapping surfaces
- future operational roadmap layer such as Plane
- issue/PR/execution-pack traceability surfaces

## Expected file families

- `docs/roadmap/*`
- future sync/integration files
- future governance automation surfaces
- future issue/PR template surfaces

## Dependencies

- architecture source-of-truth stability
- CMDB-linkage model
- grouped execution logic
- status and standards governance docs

## Risks and issues

### Key risks

- could become bureaucratic if too many required fields slow real usage
- could drift if summary surfaces and per-item files are not maintained together

### Known issues / blockers

- still requires broader per-item normalization across active items to achieve full consistency
- future operational tooling must remain subordinate to repo-doc canonical planning

## CMDB / asset linkage

- this item is explicitly responsible for strengthening roadmap-to-system and roadmap-to-asset linkage
- should remain compatible with current CMDB-lite posture and future authoritative CMDB direction

## Grouping candidates

- `RM-GOV-003`

## Grouped execution notes

- Shared-touch rationale: this item is the anchor governance system for roadmap structure, naming, impact analysis, grouped execution, and future operational overlays.
- Repeated-touch reduction estimate: very high if implemented and maintained alongside the active governance cluster.
- Grouping recommendation: `Bundle now`

## Recommended first milestone

Stabilize the canonical roadmap schema and operating model, ensure all active strategic-cluster items have normalized item files, and preserve clean linkage between architecture, roadmap, external-system catalog, and execution surfaces.

## Status transition notes

- Expected next status: `Planned`
- Transition condition: active-cluster normalization, sequencing rules, and operating conventions are sufficiently stable for broader rollout
- Validation / closeout condition: roadmap-to-execution governance is consistently used across active work without split-authority drift

## Notes

This item is not just backlog management. It is the platform’s planning and governance operating system.