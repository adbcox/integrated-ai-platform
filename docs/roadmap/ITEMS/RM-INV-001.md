# RM-INV-001

- **ID:** `RM-INV-001`
- **Title:** AI-generated full hardware inventory for all project systems and equipment
- **Category:** `INV`
- **Type:** `Feature`
- **Status:** `Accepted`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `9`
- **Target horizon:** `soon`
- **LOE:** `M`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `near`

## Description
Create an AI-generated full hardware inventory of project systems and equipment including servers, network devices, printers, scanners, 3D printers, and related hardware.

## Why it matters
Provides the baseline visibility needed for capability-aware planning and future CMDB/inventory linkage.

## Key requirements
- capture complete hardware inventory
- maintain consistent device identity and categorization
- support later linkage to capability and operations views

## Affected systems
- inventory branch
- CMDB-linkage surfaces
- future monitoring and procurement views

## Expected file families
- future inventory records and supporting docs

## Dependencies
- `RM-INV-002`
- canonical naming and identity rules

## Risks and issues
### Key risks
- incomplete or inconsistent inventory identity
### Known issues / blockers
- exact import/capture path still needs shaping

## CMDB / asset linkage
- directly adjacent to CMDB-lite and future asset authority surfaces

## Grouping candidates
- `RM-INV-002`
- `RM-INV-003`

## Grouped execution notes
- Shared-touch rationale: asset identity and capability surfaces overlap strongly.
- Repeated-touch reduction estimate: high.
- Grouping recommendation: `Bundle now`

## Recommended first milestone
Create a normalized baseline hardware inventory covering the main owned system classes.

## Status transition notes
- Expected next status: `Planned`
- Transition condition: inventory capture boundary and baseline categories are defined
- Validation / closeout condition: a bounded baseline inventory exists and supports later capability-aware use
