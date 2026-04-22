# RM-GOV-007

- **ID:** `RM-GOV-007`
- **Title:** Plane deployment, roadmap field mapping, and repo-to-Plane sync implementation
- **Category:** `GOV`
- **Type:** `System`
- **Status:** `Accepted`
- **Priority:** `High`
- **LOE:** `M`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `3`
- **Dependency burden:** `4`
- **Readiness:** `near`

## Description

Implement the first operational rollout of the hybrid roadmap model by deploying Plane in a self-hosted configuration, defining the field/property mapping between canonical roadmap docs and Plane work items, and establishing the initial synchronization pattern between repo roadmap artifacts and the Plane operational layer.

## Why it matters

`RM-GOV-006` defines the operating model decision. This item implements the actual operational substrate required to make that decision usable. Without deployment, field mapping, and sync design, the hybrid roadmap model remains conceptual and does not improve day-to-day execution flow.

## Key requirements

- deploy Plane in a self-hosted configuration suitable for the integrated AI platform environment
- define canonical field mapping from roadmap docs into Plane entities and properties
- preserve stable `RM-...` IDs across repo docs, Plane items, GitHub issues, and PR references
- define a sync model in which repo docs remain canonical and Plane mirrors active execution-ready work
- support grouped execution blocks in Plane for shared-touch packages
- preserve naming, impact, dependency, and grouping metadata well enough for governance use
- define initial conventions for linking GitHub issues and PRs back to roadmap IDs and Plane entries

## Affected systems

- roadmap governance layer
- repo documentation structure under `docs/roadmap/`
- Plane deployment and configuration layer
- GitHub execution flow
- future CMDB linkage layer
- future roadmap automation/sync layer

## Expected file families

- `docs/roadmap/*`
- deployment/config files for Plane
- sync/integration tooling
- issue / PR templates and conventions
- future governance automation surfaces

## Dependencies

- `RM-GOV-001` — integrated roadmap-to-development tracking system
- `RM-GOV-003` — feature-block package planner
- `RM-GOV-006` — hybrid roadmap operations layer with Plane on top of repo-doc canonical roadmap

## CMDB / asset linkage

- deployment should be compatible with future CMDB-aware mapping of systems, assets, and services referenced by roadmap items
- sync design must preserve the ability to represent affected systems and linked assets without flattening them into unstructured text

## Grouping candidates

- `RM-GOV-001`
- `RM-GOV-003`
- `RM-GOV-006`

## Grouped execution notes

- Shared-touch rationale: this item shares the same roadmap schema, naming, impact, execution-state, grouping, and governance automation surfaces as the rest of the active governance block.
- Repeated-touch reduction estimate: high if bundled with broader roadmap-governance implementation rather than handled as an isolated deployment-only task.
- Grouping recommendation: `Bundle now` or `Split into shared substrate + separate feature layers` depending on whether sync tooling is implemented together with the governance core.

## Recommended first milestone

Stand up a minimal self-hosted Plane instance, define the roadmap property schema in Plane, map 10 to 20 active roadmap items into the operational layer, and document the canonical sync conventions between repo docs, Plane, GitHub issues, and PR references.

## Notes

This item is the implementation companion to `RM-GOV-006`. `RM-GOV-006` establishes the model choice; this item performs the deployment, mapping, and sync work needed to operationalize it.