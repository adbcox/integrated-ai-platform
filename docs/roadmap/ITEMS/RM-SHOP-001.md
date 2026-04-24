# RM-SHOP-001

- **ID:** `RM-SHOP-001`
- **Title:** Woodworking design and project-planning app
- **Category:** `SHOP`
- **Type:** `Feature`
- **Status:** `In progress`
- **Maturity:** `M1`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `14`
- **Target horizon:** `later`
- **LOE:** `M`
- **Strategic value:** `3`
- **Architecture fit:** `3`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `later`

## Description
Build a woodworking design and project-planning application that provides suggestions, evaluation, and level-of-effort support for woodworking work.

## Why it matters
Provides a practical specialist branch with clear user utility, but remains secondary to the core platform priorities.

## Key requirements
- project-planning support
- suggestion/evaluation support
- level-of-effort guidance
- bounded UI flow

## Affected systems
- woodworking/shop branch
- future design/planning surfaces

## Expected file families
- future shop-app logic and UI surfaces

## Dependencies
- primary app shell
- inventory/capability awareness for tools/materials over time

## Risks and issues
### Key risks
- could stay too generic without bounded use cases
### Known issues / blockers
- first workshop-specific workflow still needs defining

## CMDB / asset linkage
- should later link to tools, materials, and related inventory/capability surfaces

## Grouping candidates
- `RM-SHOP-002`
- `RM-SHOP-003`

## Grouped execution notes
- Shared-touch rationale: woodworking/shop branch surfaces overlap with later 3D capture/model library work.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Define one bounded woodworking project-planning flow with LOE and suggestion support.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: first woodworking use case and output expectations are defined
- Validation / closeout condition: one bounded woodworking-planning slice exists with useful outputs
