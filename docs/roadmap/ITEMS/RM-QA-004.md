# RM-QA-004

- **ID:** `RM-QA-004`
- **Title:** API breaking change detection
- **Category:** `QA`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `4`
- **Target horizon:** `soon`
- **LOE:** `M`
- **Strategic value:** `5`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `near`

## Description

Detect API breaking changes in pull requests by comparing API schemas and signatures.

## Why it matters

Prevents accidental breaking changes to public APIs. Enables safe versioning. Requires intentional decisions about API changes. Protects API consumers.

## Key requirements

- OpenAPI/JSON schema generation
- Schema comparison (main vs PR)
- Breaking change detection (removed fields, changed types, etc.)
- Change classification (breaking/non-breaking)
- Version bump requirement
- Migration guide requirement for breaking changes
- Deprecation warnings

## Affected systems

- API development
- CI/CD pipeline
- code quality gates
- API documentation

## Expected file families

- .github/workflows/api-breaking-change-check.yml
- schemas/ — OpenAPI schemas
- scripts/detect-api-changes.py

## Dependencies

- API schema definition (OpenAPI/JSON Schema)
- schema comparison tools

## Risks and issues

### Key risks
- false positives in change detection
- difficulty detecting implicit breaking changes
- schema generation complexity

### Known issues / blockers
- none; ready to start

## Recommended first milestone

Schema comparison and breaking change detection for REST APIs with PR blocking.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: schema extraction and comparison implemented
- Validation / closeout condition: breaking changes detected and PRs blocked appropriately
