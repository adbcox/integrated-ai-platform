- **ID:** `RM-CI-008`
- **Title:** Automated release notes
- **Category:** `CI/CD`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `Low`
- **Priority class:** `P3`
- **Queue rank:** `8`
- **Target horizon:** `later`
- **LOE:** `S`
- **Strategic value:** `3`
- **Architecture fit:** `4`
- **Execution risk:** `1`
- **Dependency burden:** `1`
- **Readiness:** `near`

## Description

Automatically generate release notes from commit history, PR titles, and conventional commits. Categorize changes (features, fixes, breaking changes) and generate formatted release notes.

## Why it matters

Saves time on manual release notes. Ensures comprehensive change documentation. Provides consistent format for releases. Improves communication to users.

## Key requirements

- Conventional commit parsing
- PR title extraction
- Change categorization (feature, fix, breaking change)
- Release note template
- Multiple output formats (markdown, HTML, plain text)
- Author attribution
- Link generation (PR, commit)
- Changelog maintenance

## Affected systems

- Release management
- CI/CD pipeline
- Documentation and communication

## Expected file families

- `release/release_notes_generator.py`
- `config/changelog-config.yaml`
- `.github/workflows/release-notes.yml`

## Dependencies

- RM-CI-002 (Multi-stage build pipeline)

## Risks and issues

### Key risks
- Incomplete or inaccurate categorization
- Misleading titles masking actual changes
- Difficulty capturing manual changes outside normal workflow

### Known issues / blockers
- none; ready to start

## Recommended first milestone

Basic release notes generation from conventional commits.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: Release notes generator functional
- Validation / closeout condition: Release notes auto-generated for new releases
