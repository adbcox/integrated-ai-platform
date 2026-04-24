# RM-QA-001

- **ID:** `RM-QA-001`
- **Title:** Code coverage threshold enforcement (>80%)
- **Category:** `QA`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `1`
- **Target horizon:** `soon`
- **LOE:** `M`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `1`
- **Dependency burden:** `1`
- **Readiness:** `near`

## Description

Enforce minimum code coverage thresholds (target >80%) for pull requests and block merges that fail to meet coverage requirements.

## Why it matters

Ensures adequate test coverage. Prevents untested code from reaching production. Improves code quality and reliability. Catches regression risks early.

## Key requirements

- Code coverage measurement (pytest-cov, etc.)
- GitHub Actions integration
- PR coverage comparison (diff coverage)
- Configurable thresholds per file/area
- Clear coverage reports in PR comments
- Exclusion rules for auto-generated code
- Historical coverage tracking

## Affected systems

- CI/CD pipeline
- testing infrastructure
- code quality gates

## Expected file families

- .github/workflows/coverage-check.yml
- .coveragerc or pyproject.toml coverage config
- scripts/generate-coverage-report.py

## Dependencies

- pytest and coverage tools
- CI/CD pipeline

## Risks and issues

### Key risks
- coverage metrics not correlating with quality
- difficulty achieving high coverage on some code
- test complexity increasing to meet thresholds

### Known issues / blockers
- none; ready to start

## Recommended first milestone

Working coverage measurement and PR blocking at < 80% coverage threshold.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: coverage workflow created
- Validation / closeout condition: all PRs blocked if coverage < 80%
