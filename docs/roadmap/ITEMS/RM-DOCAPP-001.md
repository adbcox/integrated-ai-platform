# RM-DOCAPP-001

- **ID:** `RM-DOCAPP-001`
- **Title:** Excel-to-web-app migration system
- **Category:** `DOCAPP`
- **Type:** `Program`
- **Status:** `In progress`
- **Maturity:** `M2`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `9`
- **Target horizon:** `later`
- **LOE:** `XL`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `4`
- **Dependency burden:** `3`
- **Readiness:** `later`

## Description
Convert Excel-based systems into web applications while preserving workbook logic, formulas, business rules, and migration-aware interpretation of macros and VBA behavior where feasible.

## Why it matters
Provides a high-value bridge from spreadsheet-driven business logic into governed application delivery.

## Key requirements
- workbook structure understanding
- formula/rule migration
- macro/VBA interpretation where applicable
- deployable web-app output path

## Affected systems
- document/app conversion branch
- future website/app generation surfaces

## Expected file families
- future conversion pipelines and rule-mapping docs

## Dependencies
- `RM-DOCAPP-002`
- core app delivery/post-generation surfaces

## Risks and issues
### Key risks
- underestimating spreadsheet complexity and VBA semantics
### Known issues / blockers
- bounded first migration target still needs explicit selection

## CMDB / asset linkage
- may later link to source-document inventory and generated application ownership surfaces

## Grouping candidates
- `RM-DOCAPP-002`

## Grouped execution notes
- Shared-touch rationale: document-to-app and generated delivery surfaces overlap.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Select one bounded spreadsheet use case and define the conversion contract from workbook logic into web-app behavior.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: bounded source-workbook class and conversion assumptions are defined
- Validation / closeout condition: one bounded spreadsheet-to-app slice works with preserved rule behavior
