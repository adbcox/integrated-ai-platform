# RM-FLOW-003

- **ID:** `RM-FLOW-003`
- **Title:** Release tagging automation
- **Category:** `FLOW`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `3`
- **Target horizon:** `soon`
- **LOE:** `S`
- **Strategic value:** `4`
- **Architecture fit:** `5`
- **Execution risk:** `1`
- **Dependency burden:** `1`
- **Readiness:** `near`

## Description

Automatically create git tags and GitHub releases for new versions using semantic versioning and conventional commits.

## Why it matters

Eliminates manual tagging errors. Creates consistent release artifacts. Enables automated deployments keyed to releases. Maintains clear version history.

## Key requirements

- Semantic version detection (major/minor/patch)
- Automatic git tag creation
- GitHub Releases creation with notes
- Release asset handling
- Pre-release and draft support
- Version number incrementation
- Rollback capability

## Affected systems

- release management
- git repository
- deployment pipeline

## Expected file families

- .github/workflows/release.yml
- config/version-config.yaml

## Dependencies

- conventional commits convention
- changelog generation (RM-FLOW-002)

## Risks and issues

### Key risks
- incorrect version bumping
- duplicate release creation
- incomplete release information

### Known issues / blockers
- none; ready to start

## Recommended first milestone

GitHub Actions workflow that creates git tags and releases on version changes.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: release workflow created
- Validation / closeout condition: automatic releases working with proper versioning
