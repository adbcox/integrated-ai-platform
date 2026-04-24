# RM-CORE-001

- **ID:** `RM-CORE-001`
- **Title:** Privacy-focused Tor access app for browsing, research, and controlled anonymous network use
- **Category:** `CORE`
- **Type:** `Feature`
- **Status:** `In progress`
- **Maturity:** `M1`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `1`
- **Target horizon:** `later`
- **LOE:** `M`
- **Strategic value:** `3`
- **Architecture fit:** `3`
- **Execution risk:** `3`
- **Dependency burden:** `2`
- **Readiness:** `later`

## Description
Provide a controlled privacy-focused Tor access application or integration surface for browsing and research.

## Why it matters
Useful as a specialized capability, but secondary to the shared runtime and developer-assistant priorities.

## Key requirements
- controlled access posture
- clear privacy/safety boundaries
- no backbone divergence from core platform

## Affected systems
- core app shell
- privacy/research workflows

## Expected file families
- future access/integration docs and UI surfaces

## Dependencies
- core UI shell and external-systems policy

## Risks and issues
### Key risks
- privacy/security misuse risk
### Known issues / blockers
- exact supported workflows and policy controls still need definition

## CMDB / asset linkage
- may later link to controlled network/tooling surfaces

## Grouping candidates
- `RM-UI-002`

## Grouped execution notes
- Shared-touch rationale: UI and policy overlap.
- Repeated-touch reduction estimate: low.
- Grouping recommendation: `Keep separate`

## Recommended first milestone
Define the supported use cases, policy boundaries, and external integration posture for a controlled Tor access surface.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: supported scenarios and controls are explicitly defined
- Validation / closeout condition: bounded privacy-access workflow exists with clear governance
