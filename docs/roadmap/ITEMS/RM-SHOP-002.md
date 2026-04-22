# RM-SHOP-002

- **ID:** `RM-SHOP-002`
- **Title:** 3D capture, guided measurement, and reconstruction stack
- **Category:** `SHOP`
- **Type:** `Program`
- **Status:** `Accepted`
- **Maturity:** `M1`
- **Priority:** `High`
- **Priority class:** `P3`
- **Queue rank:** `15`
- **Target horizon:** `later`
- **LOE:** `XL`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `3`
- **Dependency burden:** `3`
- **Readiness:** `later`

## Description
Add a 3D workflow that guides photo capture for measurement tasks, supports room-scale spatial estimation, integrates with the purchased 3D scanner, and enables photo-based reconstruction of smaller objects and parts.

## Why it matters
Provides a meaningful workshop/design capability with reuse across physical projects.

## Key requirements
- guided photo capture
- measurement support
- room/object reconstruction paths
- integration with owned scanning hardware

## Affected systems
- workshop/3D branch
- future model library and planning surfaces

## Expected file families
- future 3D capture/reconstruction workflow docs and configs

## Dependencies
- owned scanning hardware context
- `RM-SHOP-003`

## Risks and issues
### Key risks
- workflow complexity across room-scale and object-scale capture
### Known issues / blockers
- first bounded scanning/capture flow still needs definition

## CMDB / asset linkage
- should link to scanner hardware and related 3D asset inventories

## Grouping candidates
- `RM-SHOP-003`
- `RM-SHOP-004`

## Grouped execution notes
- Shared-touch rationale: 3D capture, model reuse, and concept handoff overlap.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Define one bounded photo-capture-to-measurement or reconstruction flow for a single target class.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: first capture workflow and target class are explicitly defined
- Validation / closeout condition: one bounded capture/reconstruction slice produces usable outputs
