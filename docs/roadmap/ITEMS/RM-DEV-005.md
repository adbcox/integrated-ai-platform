# RM-DEV-005

- **ID:** `RM-DEV-005`
- **Title:** Pre-commit hooks (linting, formatting, tests)
- **Category:** `DEV`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `4`
- **Target horizon:** `soon`
- **LOE:** `M`
- **Strategic value:** `4`
- **Architecture fit:** `5`
- **Execution risk:** `1`
- **Dependency burden:** `1`
- **Readiness:** `near`

## Description

Implement pre-commit hooks that automatically run linting, code formatting, type checking, and fast unit tests before allowing commits.

## Why it matters

Prevents broken code and style inconsistencies from entering the repository. Catches errors early in the development cycle. Maintains code quality standards automatically.

## Key requirements

- Black code formatting
- Flake8 linting
- MyPy type checking
- Pre-commit framework integration
- Fast unit test subset
- Clear failure messages
- Easy bypass option for emergencies
- Configuration for both Python and JavaScript

## Affected systems

- git workflow
- code quality
- CI/CD pipeline integration

## Expected file families

- .pre-commit-config.yaml
- .pre-commit-hooks.yaml
- scripts/pre-commit-tests.sh

## Dependencies

- code quality tools (Black, Flake8, MyPy)

## Risks and issues

### Key risks
- hooks too slow (blocking commits)
- false positives in linting
- developers bypassing hooks

### Known issues / blockers
- none; ready to start

## Recommended first milestone

Working pre-commit hook for Python code (formatting, linting, type checking) with < 5 second execution.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: .pre-commit-config.yaml created and tested
- Validation / closeout condition: all developers using hooks successfully
