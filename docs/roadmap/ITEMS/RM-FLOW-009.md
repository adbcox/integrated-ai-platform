# RM-FLOW-009

- **ID:** `RM-FLOW-009`
- **Title:** Stale PR cleanup automation
- **Category:** `FLOW`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `9`
- **Target horizon:** `later`
- **LOE:** `S`
- **Strategic value:** `2`
- **Architecture fit:** `5`
- **Execution risk:** `1`
- **Dependency burden:** `0`
- **Readiness:** `now`

## Description

Automatically close inactive pull requests that have been stale for a configured duration with helpful comments.

## Why it matters

Keeps repository clean and focused. Reduces confusion about active work. Prevents accumulation of dead PRs. Improves developer efficiency.

## Key requirements

- Configurable staleness thresholds (default 30 days)
- Activity detection (comments, commits, pushes)
- Automated closure with explanation
- Label-based filtering (WIP, blocked, etc.)
- GitHub Actions automation
- Option to reopen closed PRs

## Affected systems

- GitHub repository management
- CI/CD pipeline
- developer workflow

## Expected file families

- .github/workflows/stale-pr-close.yml
- config/stale-pr-policy.yaml

## Dependencies

- GitHub Actions

## Risks and issues

### Key risks
- closing PRs that are legitimately stalled but important
- excessive closures if thresholds too aggressive
- losing work on closed PRs

### Known issues / blockers
- none; ready to start

## Recommended first milestone

GitHub Actions workflow that closes inactive PRs after 30 days with explanation.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: workflow file created
- Validation / closeout condition: stale PR cleanup working with appropriate warnings
