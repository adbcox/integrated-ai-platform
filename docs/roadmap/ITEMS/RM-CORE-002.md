# RM-CORE-002

- **ID:** `RM-CORE-002`
- **Title:** Installable edition-builder for the AI system with selectable feature sets for macOS and Windows
- **Category:** `CORE`
- **Type:** `Program`
- **Status:** `Accepted`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `4`
- **Target horizon:** `soon`
- **LOE:** `XL`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `3`
- **Dependency burden:** `4`
- **Readiness:** `later`

## Description
Create an installable system-builder that can generate edition-specific packages of the AI platform with selectable feature sets for macOS and Windows.

## Why it matters
This supports productization and controlled deployment once the shared platform stabilizes.

## Key requirements
- selectable feature sets
- platform-specific install guidance and artifacts
- preserve architecture/governance surfaces across editions

## Affected systems
- packaging and deployment surfaces
- core app/platform structure

## Expected file families
- future packaging/build docs and configs

## Dependencies
- shared runtime stability
- core UI and configuration discipline

## Risks and issues
### Key risks
- packaging premature before core substrate stabilizes
### Known issues / blockers
- edition boundaries and packaging model still need definition

## CMDB / asset linkage
- should later link to host/platform inventory and install targets

## Grouping candidates
- `RM-UI-001`

## Grouped execution notes
- Shared-touch rationale: packaging and primary product surfaces overlap.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Define edition boundaries, packaging assumptions, and the minimum viable installable system shape.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: edition model and packaging assumptions are explicitly defined
- Validation / closeout condition: bounded installable edition proof exists for one platform path
