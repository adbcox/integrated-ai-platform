# RM-UI-002

- **ID:** `RM-UI-002`
- **Title:** No-code primary user interface with click-tile navigation for apps and functions
- **Category:** `UI`
- **Type:** `Feature`
- **Status:** `Accepted`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `7`
- **Target horizon:** `soon`
- **LOE:** `L`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `3`
- **Readiness:** `near`

## Description
Create a no-code primary user interface with click-tile navigation so major apps and functions can be accessed without coding or external interface hopping.

## Why it matters
It is the main user-facing shell that makes the platform practical beyond technical operator use.

## Key requirements
- tile/click-based navigation
- clear app/function selection
- minimal friction UX
- consistent linkage to major platform functions

## Affected systems
- primary UI shell
- app/function launcher surfaces
- user-facing control/navigation layer

## Expected file families
- future UI shell/layout files
- future navigation/state model docs

## Dependencies
- `RM-UI-001`
- core platform and branch surfaces worth exposing

## Risks and issues
### Key risks
- becoming a thin wrapper with poor information hierarchy
### Known issues / blockers
- should not be designed independently of the actual app/function inventory

## CMDB / asset linkage
- may later expose capability-aware app/function recommendations based on systems/assets

## Grouping candidates
- `RM-UI-001`
- `RM-UI-003`

## Grouped execution notes
- Shared-touch rationale: UI shell and dashboard surfaces overlap strongly.
- Repeated-touch reduction estimate: high.
- Grouping recommendation: `Bundle now`

## Recommended first milestone
Define the first tile-based shell and expose a bounded set of core functions through it.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: app/function hierarchy and shell assumptions are defined
- Validation / closeout condition: a working no-code shell exists for a bounded core-function set
