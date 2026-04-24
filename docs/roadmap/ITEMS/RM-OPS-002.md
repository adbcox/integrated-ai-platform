# RM-OPS-002

- **ID:** `RM-OPS-002`
- **Title:** TP-Link Deco BE95 mesh system integration for monitoring, alerting, and control-surface visibility
- **Category:** `OPS`
- **Type:** `Feature`
- **Status:** `In progress`
- **Maturity:** `M1`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `4`
- **Target horizon:** `later`
- **LOE:** `M`
- **Strategic value:** `3`
- **Architecture fit:** `3`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `later`

## Description
Integrate TP-Link Deco BE95 network-system monitoring and alerting into platform control surfaces.

## Why it matters
Adds targeted network-visibility value but is secondary to core platform runtime/governance work.

## Key requirements
- network health visibility
- alerting where feasible
- dashboard integration

## Affected systems
- ops monitoring layer
- control surfaces

## Expected file families
- future network integration adapters and dashboards

## Dependencies
- `RM-OPS-001`

## Risks and issues
### Key risks
- vendor API/visibility limits
### Known issues / blockers
- exact feasible telemetry coverage may vary by environment

## CMDB / asset linkage
- should link to network device inventory over time

## Grouping candidates
- `RM-OPS-001`

## Grouped execution notes
- Shared-touch rationale: monitoring and dashboard surfaces overlap.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Establish a bounded network-visibility slice for Deco system health in dashboards.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: feasible telemetry and UI scope are defined
- Validation / closeout condition: bounded network-health visibility is working in-platform
