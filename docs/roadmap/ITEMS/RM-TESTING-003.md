# RM-TESTING-003

- **ID:** `RM-TESTING-003`
- **Title:** E2E test automation with real code scenarios
- **Category:** `TESTING`
- **Type:** `Enhancement`
- **Status:** `Completed`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `3`
- **Target horizon:** `near-term`
- **LOE:** `L`
- **Strategic value:** `4`
- **Architecture fit:** `5`
- **Execution risk:** `4`
- **Dependency burden:** `3`
- **Readiness:** `now`

## Description

Build end-to-end test automation that exercises the full system on realistic code scenarios. Tests should cover real modification tasks, artifact generation, and success/failure evaluation.

## Why it matters

E2E tests validate the entire system from user request through code generation and validation. They catch:
- system-level interactions and data flow
- user-facing behavior correctness
- real-world performance characteristics
- integration with external tools (aider, ollama)

## Key requirements

- test harness for real code modification scenarios
- support for synthetic and real repository data
- artifact collection and validation
- success/failure criteria definition per scenario
- performance and resource monitoring

## Affected systems

- all system components
- external integrations (aider, ollama)
- artifact and state management

## Expected file families

- tests/e2e/ — E2E test suites
- tests/fixtures/real_scenarios/ — realistic code modification tasks
- tests/validators/ — success/failure criteria evaluators

## Dependencies

- `RM-TESTING-001` — unit test fixtures
- `RM-TESTING-002` — integration test patterns

## Risks and issues

### Key risks
- tests may be fragile due to external system dependencies
- long execution time requiring dedicated test infrastructure
- difficult to reproduce failures in development environments

### Known issues / blockers
- external system availability (ollama, aider) dependencies

## CMDB / asset linkage

- aider integration, ollama inference, full platform components

## Grouping candidates

- none (depends on `RM-TESTING-002`)

## Grouped execution notes

- Blocked by `RM-TESTING-002`. Can be executed after integration patterns are established.

## Recommended first milestone

Implement E2E test framework with 5 realistic code modification scenarios.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: E2E test harness with synthetic scenarios defined
- Validation / closeout condition: 5+ realistic scenarios with documented success/failure criteria

## Notes

Critical for validating system reliability and user experience.
