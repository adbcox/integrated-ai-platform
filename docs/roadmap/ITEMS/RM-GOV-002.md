# RM-GOV-002

- **ID:** `RM-GOV-002`
- **Title:** Recurring full-system integrity review for naming consistency, duplicates, mismatches, and synchronization hygiene
- **Category:** `GOV`
- **Type:** `System`
- **Status:** `Completed`
- **Maturity:** `M3`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `1`
- **Target horizon:** `next`
- **LOE:** `L`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `near`

## Description

Implement a recurring full-system integrity review capability that audits naming consistency, duplicate concepts, mismatches, and synchronization issues across roadmap, code, docs, and CMDB-adjacent surfaces.

## Why it matters

This is a core anti-drift system. It makes future autonomous work safer by reducing ambiguity and helping the platform maintain one coherent system identity over time.

## Key requirements

- detect naming inconsistencies
- identify duplicates and overlaps
- compare roadmap, code, docs, and system surfaces for drift
- produce prioritized integrity findings

## Affected systems

- roadmap governance layer
- architecture docs
- code/document naming surfaces
- future CMDB-lite and asset identity surfaces

## Expected file families

- `docs/roadmap/*`
- `docs/architecture/*`
- future integrity/audit tooling

## Dependencies

- `RM-GOV-001`
- naming standards and authority surfaces

## Risks and issues

### Key risks
- noisy findings if rules are too vague

### Known issues / blockers
- requires stable canonical naming inputs to be most effective

## CMDB / asset linkage

- should compare canonical system and asset identities against future CMDB-linked surfaces

## Grouping candidates

- `RM-GOV-001`

## Grouped execution notes

- Shared-touch rationale: identity, naming, governance, and anti-drift surfaces overlap strongly.
- Repeated-touch reduction estimate: high.
- Grouping recommendation: `Bundle now`

## Recommended first milestone

Create a first integrity review pass covering naming consistency, duplicate detection, and roadmap/doc alignment.

## Status transition notes

- Expected next status: `Planned`
- Transition condition: rule set and first review surface are defined
- Validation / closeout condition: recurring integrity review outputs are produced and used
