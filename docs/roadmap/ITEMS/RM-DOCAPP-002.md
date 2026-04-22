# RM-DOCAPP-002

- **ID:** `RM-DOCAPP-002`
- **Title:** AI-assisted website generation, SEO, and analytics delivery stack
- **Category:** `DOCAPP`
- **Type:** `Program`
- **Status:** `Accepted`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P3`
- **Queue rank:** `10`
- **Target horizon:** `later`
- **LOE:** `XL`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `3`
- **Readiness:** `later`

## Description
Add a website-delivery capability that uses adopted OSS tools to generate editable, deployable websites with SEO and analytics support rather than building a custom web-design platform from scratch.

## Why it matters
Creates a practical delivery stack for website generation while following the platform’s adopt-first posture for commodity tooling.

## Key requirements
- OSS-backed website generation workspace
- post-generation SEO workflow
- analytics instrumentation path
- reusable vertical template packs

## Affected systems
- document/app conversion branch
- generated website delivery surfaces

## Expected file families
- future generation/adoption configs, templates, and delivery docs

## Dependencies
- external docs for selected web-generation stack
- `RM-CORE-002`

## Risks and issues
### Key risks
- overbuilding a bespoke site-builder instead of using adopted tools
### Known issues / blockers
- exact adopted stack and deployment model still need definition

## CMDB / asset linkage
- may later link generated sites/apps to owned project/service inventory

## Grouping candidates
- `RM-DOCAPP-001`

## Grouped execution notes
- Shared-touch rationale: website delivery and document-to-app conversion share generation and deployability surfaces.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone
Define the adopted website-generation stack and produce one bounded editable/deployable site slice with SEO and analytics hooks.

## Status transition notes
- Expected next status: `Decomposing`
- Transition condition: adopted stack and first vertical slice are defined
- Validation / closeout condition: one generated/deployable website slice exists with bounded post-generation workflow
