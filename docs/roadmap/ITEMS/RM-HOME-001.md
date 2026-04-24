# RM-HOME-001

- **ID:** `RM-HOME-001`
- **Title:** Indoor air quality monitoring and purifier automation app with Home Assistant integration
- **Category:** `HOME`
- **Type:** `Feature`
- **Status:** `Completed`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `8`
- **Target horizon:** `soon`
- **LOE:** `M`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `3`
- **Readiness:** `near`

## Description
Build an indoor air quality monitoring and purifier automation app that integrates with Home Assistant while keeping reporting, room status, alerts, and policy logic in this platform.

## Why it matters
Creates a practical environment-control capability and demonstrates the preferred pattern of integrating strong external systems while keeping platform-owned policy and user experience local.

## Key requirements
- ingest indoor air-quality signals
- automate purifier control based on policy
- report room-level status and trends
- use Home Assistant as bridge, not primary UI

## Affected systems
- home/environment branch
- Home Assistant integration layer
- dashboard/control surfaces

## Expected file families
- future HA adapters
- future room policy/reporting surfaces

## Dependencies
- Home Assistant integration posture
- `RM-UI-001`

## Risks and issues
### Key risks
- device variability and threshold noise
### Known issues / blockers
- room model and supported sensor/purifier set still need bounded definition

## CMDB / asset linkage
- should remain linkable to sensor, purifier, and room/device inventory over time

## Grouping candidates
- `RM-UI-003`

## Grouped execution notes
- Shared-touch rationale: dashboard and environment-reporting surfaces overlap.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Define one room-level dashboard and threshold automation loop using Home Assistant-connected sensors and purifier control.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: supported entities, room model, and initial policy rules are defined
- Validation / closeout condition: one bounded room automation/reporting slice works end to end
