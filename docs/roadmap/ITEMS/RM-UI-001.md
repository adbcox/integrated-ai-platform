# RM-UI-001

- **ID:** `RM-UI-001`
- **Title:** Master control center for the system with web-first UI, tablet support, and later app-based surfaces
- **Category:** `UI`
- **Type:** `Feature`
- **Status:** `Completed`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `6`
- **Target horizon:** `soon`
- **LOE:** `L`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `3`
- **Dependency burden:** `3`
- **Readiness:** `near`

## Description
Create the master control center as the primary operator/admin surface for the platform, starting web-first with tablet support and later app-based surfaces.

## Why it matters
It is the main human-facing control surface for operations, monitoring, governance summaries, and future branch control.

## Key requirements
- web-first control center
- tablet-capable layouts
- operator/admin oriented information hierarchy
- integration with monitoring, inventory, and selected branch surfaces

## Affected systems
- UI/control surfaces
- ops and governance dashboards
- branch summary surfaces

## Expected file families
- future UI/layout components and supporting docs

## Dependencies
- `RM-OPS-001`
- `RM-OPS-004`
- `RM-OPS-005`

## Risks and issues
### Key risks
- dashboard clutter and role confusion
### Known issues / blockers
- must avoid outrunning the underlying system capabilities

## CMDB / asset linkage
- should expose system, service, and asset summaries over time

## Grouping candidates
- `RM-UI-002`
- `RM-OPS-001`

## Grouped execution notes
- Shared-touch rationale: control surfaces and ops summaries overlap.
- Repeated-touch reduction estimate: high.
- Grouping recommendation: `Bundle now`

## Recommended first milestone
Define and build the minimum viable operator dashboard with system status, alerts, and core navigation.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: first operator surface and information hierarchy are defined
- Validation / closeout condition: usable control-center slice exists for real platform operations
