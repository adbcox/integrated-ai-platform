# RM-OPS-010

- **ID:** `RM-OPS-010`
- **Title:** Lawful tenant and worker screening workflow using public-record and approved verification sources
- **Category:** `OPS`
- **Type:** `System`
- **Status:** `In progress`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P3`
- **Queue rank:** `15`
- **Target horizon:** `later`
- **LOE:** `L`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `4`
- **Dependency burden:** `4`
- **Readiness:** `later`

## Description

Build a governed screening workflow for apartment-rental applicants and future workers using lawful, reviewable, and source-aware verification steps rather than opaque or exploitative screening websites.

The goal is not to create an unbounded background-investigation tool. The goal is to create a structured workflow that can help collect, normalize, and present screening-relevant information from approved sources with clear compliance boundaries, operator review, and defensible evidence handling.

## Why it matters

This addresses a real operational pain point:
- repeated payment to screening vendors
- low trust in many websites and intermediaries
- weak control over what data is collected and how it is used
- poor transparency about evidence quality and decision support

A governed internal workflow would improve consistency, transparency, and integration with the rest of the platform’s intake, recordkeeping, and decision-support posture.

## Key requirements

- support distinct screening workflows for:
  - rental applicants
  - prospective workers / contractors
- use approved, reviewable, and source-aware verification steps
- preserve operator review and final decision responsibility
- show what sources were used, what was found, and confidence/limitations of findings
- support evidence packaging and retention rules where appropriate
- support configurable workflow steps rather than a single hard-coded process

### Compliance and lawful-use boundaries
- do not treat this as unrestricted personal-data aggregation
- require explicit lawful-use posture and jurisdiction-sensitive compliance review before activation
- require configurable consent / disclosure steps where applicable
- require clear boundaries between public-record lookup, identity verification, employment screening, rental screening, and adverse-action-sensitive workflows
- preserve auditability of what data was used and why
- allow only approved data-source categories and approved workflow variants

## Affected systems

- operator workflow / intake surfaces
- connector/control-plane layer
- evidence/audit surfaces
- future document and decision-support surfaces

## Expected file families

- future screening workflow docs/configs
- future source approval and compliance policy files
- future evidence packaging and retention files
- future intake/review UI surfaces

## Dependencies

- `RM-GOV-009` — external application connectivity and integration control plane
- `RM-OPS-005` — telemetry, tracing, and audit evidence pipeline
- `RM-GOV-001` — roadmap/execution governance and evidence alignment
- future message/document/intake surfaces where applicant or worker information is received

## Risks and issues

### Key risks
- compliance risk if workflow boundaries are weak or used in the wrong context
- false confidence from low-quality or mismatched records
- privacy risk if the feature drifts into over-collection or unclear retention

### Known issues / blockers
- this item should not move into execution until lawful-use boundaries, source policy, and workflow separation are explicitly defined
- exact source categories and retention/audit rules need careful up-front design

## CMDB / asset linkage

- limited direct CMDB linkage; primarily a business/operations workflow surface

## Grouping candidates

- `RM-GOV-009`
- `RM-OPS-005`
- future document/intake and assistant workflow items

## Grouped execution notes

- Shared-touch rationale: connector governance, evidence/audit handling, and operator workflow surfaces overlap strongly.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle only after connector, evidence, and compliance-control substrate is mature`

## Recommended first milestone

Define one bounded screening workflow variant with:
- explicit lawful-use posture
- approved source categories
- consent/disclosure checkpoints where applicable
- operator review output
- evidence packaging rules

Do not begin with broad automation across multiple screening contexts.

## Status transition notes

- Expected next status: `Planned`
- Transition condition: one bounded workflow variant, source policy, audit posture, and compliance boundaries are explicitly defined
- Validation / closeout condition: one governed screening workflow works end to end with visible source provenance, operator review, and defensible evidence handling

## Notes

This item should remain a lawful, reviewable business workflow capability. It must not become a generic background-investigation or unrestricted people-search feature.