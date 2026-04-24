# RM-TESTING-017

- **ID:** `RM-TESTING-017`
- **Title:** API contract testing (Pact/Postman)
- **Category:** `TESTING`
- **Type:** `Feature`
- **Status:** `Accepted`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `133`
- **Target horizon:** `near-term`
- **LOE:** `M`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `1`
- **Dependency burden:** `2`
- **Readiness:** `near`

## Description

Implement API contract testing using Pact or Postman to validate API contracts between consumers and providers.

## Why it matters

Contract testing enables:
- early detection of API incompatibilities
- independent service testing without integration
- prevention of breaking changes
- faster development cycles
- consumer-driven API design

## Key requirements

- Contract definition (Pact format or Postman collections)
- Consumer test generation
- Provider test validation
- Contract broker integration
- Breaking change detection
- Version compatibility checks
- Documentation from contracts

## Affected systems

- API development and testing
- service integration
- API versioning
- deployment coordination

## Expected file families

- tests/contracts/consumer/ — consumer tests
- tests/contracts/provider/ — provider tests
- contracts/ — contract definitions
- config/pact_config.yaml — contract config

## Dependencies

- `RM-TESTING-001` — test framework
- `RM-TESTING-017` — API testing

## Risks and issues

### Key risks
- contract maintenance burden
- false positives from overly strict contracts
- versioning complexity

### Known issues / blockers
- none; ready to start

## CMDB / asset linkage

- API testing, service integration, contract management

## Grouping candidates

- `RM-TESTING-016` (E2E testing)
- `RM-TESTING-018` (performance benchmarking)

## Grouped execution notes

- Works with E2E and integration tests
- Complements API versioning strategy

## Recommended first milestone

Implement Pact contract tests for critical API endpoints.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: contract framework
- Validation / closeout condition: consumer/provider contracts validated

## Notes

Enables confident API evolution and microservice development.
