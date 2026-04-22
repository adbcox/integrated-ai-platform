# RM-DEV-001

- **ID:** `RM-DEV-001`
- **Title:** Add Xcode and Apple-platform coding capability to the developer assistant
- **Category:** `DEV`
- **Type:** `Feature`
- **Status:** `Accepted`
- **Maturity:** `M2`
- **Priority:** `Medium`
- **Priority class:** `P2`
- **Queue rank:** `3`
- **Target horizon:** `soon`
- **LOE:** `M`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `3`
- **Dependency burden:** `3`
- **Readiness:** `near`

## Description
Add bounded Xcode and Apple-platform coding support to the developer assistant under the same runtime, artifact, and governance rules as the broader coding stack.

## Why it matters
This extends the local developer assistant into an important platform domain without creating a separate execution backbone.

## Key requirements
- explicit Apple toolchain profiles
- bounded build/test/simulator actions
- no hidden mutation of signing/release state
- same runtime and artifact rules as other coding work

## Affected systems
- developer assistant runtime
- Apple-platform toolchain integration
- validation and artifact surfaces

## Expected file families
- future Apple-toolchain adapters
- future build/test execution docs and configs

## Dependencies
- shared runtime substrate
- `RM-DEV-005` legacy completed autonomy work as context

## Risks and issues
### Key risks
- toolchain/signing complexity
### Known issues / blockers
- exact Apple execution boundaries still need tightening

## CMDB / asset linkage
- should later remain linkable to macOS/Xcode-capable hosts and toolchains

## Grouping candidates
- `RM-AUTO-001`
- `RM-HW-001`

## Grouped execution notes
- Shared-touch rationale: code runtime and developer-assistant surfaces overlap.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Support bounded Apple build/test/simulator tasks under the governed coding runtime.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: Apple-specific action classes and safety boundaries are defined
- Validation / closeout condition: bounded Apple-platform tasks run through the same governed runtime model
