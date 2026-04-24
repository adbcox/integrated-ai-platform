# RM-TESTING-028

- **ID:** `RM-TESTING-028`
- **Title:** Smoke test suite (critical paths)
- **Category:** `TESTING`
- **Type:** `Feature`
- **Status:** `Accepted`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `144`
- **Target horizon:** `near-term`
- **LOE:** `S`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `1`
- **Dependency burden:** `1`
- **Readiness:** `near`

## Description

Implement fast-running smoke test suite for critical user workflows and API endpoints to validate basic functionality.

## Why it matters

Smoke tests enable:
- quick validation of basic functionality
- fast feedback on breaking changes
- early failure detection
- rapid CI turnaround
- deployment confidence

## Key requirements

- Critical path identification
- Fast test execution (<1 min)
- Minimal test setup
- Clear pass/fail indicators
- Integration with CI pipeline

## Affected systems

- testing infrastructure
- CI/CD pipeline
- deployment validation

## Expected file families

- tests/smoke/test_critical_paths.py — smoke tests
- tests/smoke/conftest.py — smoke configuration

## Dependencies

- `RM-TESTING-001` — test framework

## Risks and issues

### Key risks
- smoke tests missing critical issues
- false confidence from smoke test pass

### Known issues / blockers
- none; ready to start

## CMDB / asset linkage

- testing infrastructure, deployment validation

## Grouping candidates

- `RM-TESTING-027` (regression suite)
- `RM-TESTING-029` (browser compatibility)

## Grouped execution notes

- Fast subset of regression tests
- Validates critical paths

## Recommended first milestone

Implement smoke tests for critical API endpoints and workflows.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: smoke tests implemented
- Validation / closeout condition: critical paths covered

## Notes

Quick validation of basic system functionality.
