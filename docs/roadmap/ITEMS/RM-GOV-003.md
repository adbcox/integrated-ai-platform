# RM-GOV-003

- **ID:** `RM-GOV-003`
- **Title:** Feature-block package planner for grouped roadmap execution and shared-touch LOE optimization
- **Category:** `GOV`
- **Type:** `Enhancement`
- **Status:** `Completed`
- **Maturity:** `M3`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `2`
- **Target horizon:** `next`
- **LOE:** `L`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `near`

## Description
Build a feature-block package planner that analyzes multiple roadmap items together, detects shared files/systems/dependencies, and suggests grouped implementation packages that reduce repeated touches and total LOE.

## Why it matters
This makes the roadmap materially smarter and better suited for autonomous pull planning.

## Key requirements
- detect shared touch surfaces
- compare grouped vs separate LOE
- recommend bundle/keep-separate decisions
- support explainable package recommendations

## Affected systems
- roadmap governance layer
- grouped execution logic
- future operational roadmap overlays

## Expected file families
- `docs/roadmap/*`
- future planning/sync tooling

## Dependencies
- `RM-GOV-001`
- canonical impact and grouping fields

## Risks and issues
### Key risks
- over-grouping unrelated work
### Known issues / blockers
- depends on reasonably accurate impact modeling

## CMDB / asset linkage
- shared-subsystem and shared-asset analysis should later leverage CMDB-linked data

## Grouping candidates
- `RM-GOV-001`
- `RM-GOV-002`

## Grouped execution notes
- Shared-touch rationale: belongs to the governance core.
- Repeated-touch reduction estimate: high.
- Grouping recommendation: `Bundle now`

## Recommended first milestone
Create a first grouped-execution advisor using active backlog items and shared-touch heuristics.

## Status transition notes
- Expected next status: `Planned`
- Transition condition: grouping inputs and output model are defined
- Validation / closeout condition: grouped recommendations are produced and used in pull planning
