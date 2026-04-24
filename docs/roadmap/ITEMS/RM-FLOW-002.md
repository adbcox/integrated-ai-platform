# RM-FLOW-002

- **ID:** `RM-FLOW-002`
- **Title:** Automated changelog generation
- **Category:** `FLOW`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `Medium`
- **Priority class:** `P2`
- **Queue rank:** `2`
- **Target horizon:** `soon`
- **LOE:** `S`
- **Strategic value:** `3`
- **Architecture fit:** `4`
- **Execution risk:** `1`
- **Dependency burden:** `1`
- **Readiness:** `near`

## Description

Automatically generate changelog entries from commit messages and PR descriptions following conventional commits and semantic versioning.

## Why it matters

Maintains accurate, readable release notes automatically. Reduces manual documentation burden. Enables users to understand what changed. Supports release communication.

## Key requirements

- Conventional commits parsing
- PR-based changelog generation
- Version bump detection (major/minor/patch)
- Release note formatting
- Changelog file updates
- GitHub Releases integration
- Template customization

## Affected systems

- release management
- documentation
- CI/CD pipeline

## Expected file families

- .github/workflows/changelog.yml
- config/changelog.yaml
- CHANGELOG.md

## Dependencies

- conventional commits convention
- semantic versioning

## Risks and issues

### Key risks
- inaccurate or incomplete changelog
- improperly formatted commit messages
- difficult to maintain templates

### Known issues / blockers
- none; ready to start

## Recommended first milestone

Working changelog generation from conventional commits with release grouping.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: changelog generation script created
- Validation / closeout condition: changelog automatically updated on releases
