# RM-TESTING-002

- **ID:** `RM-TESTING-002`
- **Title:** Integration test automation for stage pipeline
- **Category:** `TESTING`
- **Type:** `Enhancement`
- **Status:** `Accepted`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `2`
- **Target horizon:** `immediate`
- **LOE:** `L`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `3`
- **Dependency burden:** `2`
- **Readiness:** `ready`

## Description

Build comprehensive integration tests for the stage RAG and manager pipelines. Test real interactions between modules, data flow integrity, and end-to-end execution paths without requiring live external systems.

## Why it matters

Integration tests catch failures that unit tests miss:
- data transformation correctness
- state management across stages
- execution flow and ordering
- fallback and error-recovery paths

This is critical for the core autonomy system where stage interactions are complex.

## Key requirements

- end-to-end stage pipeline execution tests
- test fixtures for synthetic code and query data
- validation of artifact generation and persistence
- error-recovery and timeout scenarios
- performance benchmarks for stage execution

## Affected systems

- stage_rag1 through stage_rag6 pipelines
- manager execution layers
- artifact persistence and state management
- scheduler and worker runtime

## Expected file families

- tests/integration/ — integration test suites
- tests/fixtures/synthetic_data.py — synthetic code and query fixtures
- tests/fixtures/artifact_validators.py — artifact format and content validation

## Dependencies

- `RM-TESTING-001` — requires isolated unit test fixtures first

## Risks and issues

### Key risks
- test execution time increases significantly
- flaky tests due to timing or resource contention
- difficulty isolating failures when tests fail

### Known issues / blockers
- none; ready to start after `RM-TESTING-001`

## CMDB / asset linkage

- stage_rag, manager, scheduler, worker_runtime components

## Grouping candidates

- none (depends on `RM-TESTING-001`)

## Grouped execution notes

- Blocked by `RM-TESTING-001`. Can be executed after fixtures are defined.

## Recommended first milestone

Implement end-to-end pipeline execution tests covering happy path and error cases.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: integration test skeleton with synthetic data fixtures
- Validation / closeout condition: 90%+ of stage interactions have integration test coverage

## Notes

Blocked by `RM-TESTING-001`. Critical for confidence in autonomy system reliability.
