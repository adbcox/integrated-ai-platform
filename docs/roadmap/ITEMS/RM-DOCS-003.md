# RM-DOCS-003

- **ID:** `RM-DOCS-003`
- **Title:** User guides and onboarding documentation
- **Category:** `DOCS`
- **Type:** `Enhancement`
- **Status:** `Accepted`
- **Maturity:** `M0`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `3`
- **Target horizon:** `near-term`
- **LOE:** `M`
- **Strategic value:** `3`
- **Architecture fit:** `4`
- **Execution risk:** `1`
- **Dependency burden:** `0`
- **Readiness:** `ready`

## Description

Create comprehensive user guides covering system setup, basic usage, common workflows, and troubleshooting. Design onboarding documentation for different user personas.

## Why it matters

User guides enable:
- faster time-to-productivity for new users
- reduced support burden for common questions
- clear guidance for different use cases
- better user experience for non-expert users

## Key requirements

- setup and installation guide
- quick-start tutorial for core workflows
- per-domain user guides (coding, home automation, etc.)
- troubleshooting and FAQ
- configuration guide
- persona-specific guides (developers, operators, administrators)

## Affected systems

- user-facing features across all domains
- system configuration and setup
- integration workflows

## Expected file families

- docs/user_guides/ — user documentation
- docs/getting_started.md — quick start guide
- docs/troubleshooting.md — common issues and solutions
- docs/faq.md — frequently asked questions

## Dependencies

- `RM-DOCS-001` — API documentation should exist first for reference

## Risks and issues

### Key risks
- documentation becoming outdated as features evolve
- difficulty anticipating user confusion points
- oversimplification or technical inaccuracy

### Known issues / blockers
- none; ready to start

## CMDB / asset linkage

- documentation systems, user support channels

## Grouping candidates

- none (depends on `RM-DOCS-001`)

## Grouped execution notes

- Can be executed after API documentation started. User guides benefit from reference material.

## Recommended first milestone

Create quick-start guide and 3 domain-specific user guides.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: quick-start and initial user guides
- Validation / closeout condition: 5+ user guides with working examples and troubleshooting

## Notes

High impact on user experience. Benefits from real user feedback during development.
