# RM-FLOW-001

- **ID:** `RM-FLOW-001`
- **Title:** Auto-merge for passing PRs
- **Category:** `FLOW`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `1`
- **Target horizon:** `soon`
- **LOE:** `S`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `1`
- **Readiness:** `near`

## Description

Implement automatic merging of pull requests that pass all checks and meet approval criteria without manual intervention.

## Why it matters

Reduces manual overhead in merge process. Speeds up deployment pipeline. Prevents stale PRs. Enables continuous deployment workflow.

## Key requirements

- Auto-merge trigger on passing checks
- Approval requirement configuration
- Branch protection rule integration
- Squash/rebase/merge strategy options
- Clear PR status indicators
- Cancellation support
- Audit trail of auto-merges

## Affected systems

- CI/CD pipeline
- GitHub workflows
- deployment process

## Expected file families

- .github/workflows/auto-merge.yml
- config/merge-policy.yaml

## Dependencies

- CI/CD pipeline established

## Risks and issues

### Key risks
- merging broken code if CI is insufficient
- lost visibility into what was merged

### Known issues / blockers
- none; ready to start

## Recommended first milestone

GitHub Actions workflow that auto-merges PRs when all checks pass and required approvals exist.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: workflow file created
- Validation / closeout condition: auto-merge working reliably with clear audit trail
