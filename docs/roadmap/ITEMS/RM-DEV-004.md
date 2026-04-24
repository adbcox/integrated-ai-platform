# RM-DEV-004

- **ID:** `RM-DEV-004`
- **Title:** Debug configuration for common IDEs
- **Category:** `DEV`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `3`
- **Target horizon:** `soon`
- **LOE:** `S`
- **Strategic value:** `4`
- **Architecture fit:** `5`
- **Execution risk:** `1`
- **Dependency burden:** `0`
- **Readiness:** `now`

## Description

Create ready-to-use debug configurations for major IDEs (VS Code, PyCharm, JetBrains) enabling one-click debugging of services and unit tests.

## Why it matters

Reduces context switching between tools. Eliminates manual debugger configuration. Makes stepping through code and inspecting state trivial.

## Key requirements

- VS Code launch.json templates
- PyCharm/JetBrains run configurations
- Breakpoint debugging support
- Conditional breakpoints
- Watch expressions and variable inspection
- Integration with local services
- Documentation for each IDE

## Affected systems

- development environment
- IDEs (VS Code, PyCharm, etc.)
- backend services
- test runners

## Expected file families

- .vscode/launch.json
- .idea/runConfigurations/
- docs/IDE_DEBUGGING.md

## Dependencies

- none

## Risks and issues

### Key risks
- IDE version compatibility
- configuration drift

### Known issues / blockers
- none; ready to start

## Recommended first milestone

VS Code debug configuration for backend service with attach and test debugging support.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: launch.json created
- Validation / closeout condition: one-click debugging works for all major services and tests
