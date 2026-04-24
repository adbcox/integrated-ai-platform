- **ID:** `RM-CI-009`
- **Title:** Branch protection rules
- **Category:** `CI/CD`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `Medium`
- **Priority class:** `P2`
- **Queue rank:** `9`
- **Target horizon:** `soon`
- **LOE:** `S`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `1`
- **Dependency burden:** `1`
- **Readiness:** `near`

## Description

Enforce branch protection rules: require status checks to pass before merge, require PR reviews, dismiss stale reviews, require code owner reviews, auto-delete branches.

## Why it matters

Enforces code quality standards. Prevents bad code from reaching main. Ensures review process compliance. Maintains code health.

## Key requirements

- Required status checks (CI, security, code coverage)
- Require PR reviews before merge
- Require code owner approval
- Dismiss stale reviews on new commits
- Administrator force-push prevention
- Automatic branch cleanup
- Branch protection rule configuration UI
- Audit trail of protection changes

## Affected systems

- Pull request workflow
- Code quality enforcement
- Repository management

## Expected file families

- `config/branch-protection.yaml`
- `scripts/enforce-branch-rules.py`
- `.github/workflows/branch-protect.yml`

## Dependencies

- RM-CI-003 (Automated security scanning)
- RM-QA-001 (Code coverage thresholds)

## Risks and issues

### Key risks
- Overly strict rules blocking legitimate work
- Administrator override requiring careful governance

### Known issues / blockers
- none; ready to start

## Recommended first milestone

Basic branch protection requiring CI checks and PR review.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: Branch protection rules configured
- Validation / closeout condition: Protection rules enforced on main branch
