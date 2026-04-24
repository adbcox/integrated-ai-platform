# RM-HW-001

- **ID:** `RM-HW-001`
- **Title:** AI-assisted electrical design workflow for ESP32 and Nordic hardware
- **Category:** `HW`
- **Type:** `Feature`
- **Status:** `Accepted`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P3`
- **Queue rank:** `3`
- **Target horizon:** `later`
- **LOE:** `L`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `3`
- **Dependency burden:** `3`
- **Readiness:** `later`

## Description
Build an AI-assisted electrical design workflow to support ESP32 and Nordic device design, evaluation, and design-support tasks within the platform.

## Why it matters
Extends the platform into a high-value hardware-support branch while remaining connected to the shared developer and inventory/capability context.

## Key requirements
- design support for ESP32 and Nordic workflows
- guidance on component choices and design review
- integration with future firmware and hardware inventory surfaces

## Affected systems
- hardware branch
- developer assistant/hardware workflows
- inventory/capability surfaces

## Expected file families
- future hardware-workflow/adapters
- future design knowledge/config surfaces

## Dependencies
- `RM-DEV-001`
- hardware inventory/capability awareness

## Risks and issues
### Key risks
- domain complexity and verification burden
### Known issues / blockers
- exact first bounded hardware-design slice still needs shaping

## CMDB / asset linkage
- should later link to owned boards, components, and tool inventory

## Grouping candidates
- `RM-INV-002`

## Grouped execution notes
- Shared-touch rationale: hardware branch, component awareness, and developer assistant overlap.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Define a bounded ESP32/Nordic electrical-design advisory flow with explicit component/context inputs.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: first bounded use case and required design inputs are defined
- Validation / closeout condition: one governed hardware-design support flow exists with useful outputs
