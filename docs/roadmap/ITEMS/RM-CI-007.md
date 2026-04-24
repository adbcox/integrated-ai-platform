- **ID:** `RM-CI-007`
- **Title:** PR preview environments
- **Category:** `CI/CD`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `7`
- **Target horizon:** `later`
- **LOE:** `L`
- **Strategic value:** `4`
- **Architecture fit:** `3`
- **Execution risk:** `3`
- **Dependency burden:** `2`
- **Readiness:** `near`

## Description

Automatically create preview environments for each PR: deploy PR changes to ephemeral environment, enable testing and review, tear down after merge.

## Why it matters

Enables reviewers to test code before merge. Catches environment-specific issues. Reduces post-merge surprises. Improves code quality.

## Key requirements

- Automatic environment provisioning per PR
- Preview URL generation and sharing
- Preview environment access control
- Environment cleanup and deprovisioning
- Preview-specific configuration
- Concurrent preview environments
- Preview status monitoring
- Cost tracking and limits

## Affected systems

- CI/CD pipeline
- Deployment infrastructure
- Pull request workflow

## Expected file families

- `.github/workflows/preview-*.yml`
- `deployment/preview_manager.py`

## Dependencies

- RM-DEPLOY-001 (Blue/green deployment)
- RM-CI-002 (Multi-stage build pipeline)

## Risks and issues

### Key risks
- Infrastructure cost of preview environments
- Stale previews consuming resources
- Data isolation between previews

### Known issues / blockers
- none; ready to start

## Recommended first milestone

PR preview environments with automatic provisioning and cleanup.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: Preview environment system operational
- Validation / closeout condition: PR previews deployed and accessible for testing
