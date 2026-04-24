# RM-HW-002

- **ID:** `RM-HW-002`
- **Title:** Flipper-style embedded shell for ESP32 and Nordic devices
- **Category:** `HW`
- **Type:** `Feature`
- **Status:** `In progress`
- **Maturity:** `M2`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `11`
- **Target horizon:** `later`
- **LOE:** `M`
- **Strategic value:** `3`
- **Architecture fit:** `4`
- **Execution risk:** `3`
- **Dependency burden:** `3`
- **Readiness:** `later`

## Description
Build a Flipper-style embedded shell or interaction model for ESP32 and Nordic devices as part of the platform’s hardware branch.

## Why it matters
Creates a distinctive embedded interaction surface but should remain subordinate to the shared platform and hardware workflows.

## Key requirements
- bounded shell/interaction model
- support ESP32 and Nordic devices
- align with future hardware inventory and firmware workflows

## Affected systems
- hardware branch
- embedded UI/interaction surfaces

## Expected file families
- future embedded-shell logic and device-support docs

## Dependencies
- `RM-HW-001`
- future firmware/device workflow support

## Risks and issues
### Key risks
- becoming a disconnected embedded mini-platform
### Known issues / blockers
- exact supported interaction model and device scope still need defining

## CMDB / asset linkage
- should later link to owned devices, boards, and supported hardware classes

## Grouping candidates
- `RM-HW-001`

## Grouped execution notes
- Shared-touch rationale: hardware support and device interaction surfaces overlap.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Define one bounded embedded interaction pattern for one supported device class.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: device class and interaction boundaries are explicitly defined
- Validation / closeout condition: one bounded embedded-shell slice exists for a supported target
