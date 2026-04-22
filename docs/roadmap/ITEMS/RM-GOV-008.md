# RM-GOV-008

- **ID:** `RM-GOV-008`
- **Title:** External application and integration registry with phased adoption and interface guidance
- **Category:** `GOV`
- **Type:** `System`
- **Status:** `Accepted`
- **Maturity:** `M3`
- **Priority:** `High`
- **Priority class:** `P1`
- **Queue rank:** `3`
- **Target horizon:** `next`
- **LOE:** `M`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `2`
- **Dependency burden:** `3`
- **Readiness:** `now`

## Description

Create and maintain a canonical roadmap-facing registry of all external applications, services, protocols, and tooling that the platform will adopt, integrate with, or interface against. The registry must preserve official source links, installation/download paths where relevant, API and integration references, phase placement, and the intended local integration pattern.

## Why it matters

The project has already accumulated a meaningful set of external software decisions and candidate integrations, but they are currently spread across architecture handoffs, roadmap items, research notes, and chat context. Without one dedicated registry, the program risks losing software-adoption decisions, duplicating research, and creating inconsistent implementation assumptions.

## Key requirements

- maintain one canonical external-applications catalog in the repo
- record official source / download links and official API or integration docs where available
- classify each external system as adopt, hybrid, conditional, reference only, or unresolved
- record intended roadmap phase or group for each external system
- document the local wrapper / adapter / ownership model
- include major current external systems such as model/runtime software, roadmap tooling, media systems, home automation systems, athlete-data systems, and AI interaction surfaces
- preserve unresolved items explicitly rather than allowing them to disappear from planning

## Affected systems

- roadmap governance layer
- architecture adoption / build decisions
- media branch planning
- home automation planning
- athlete analytics planning
- developer and AI tooling planning

## Expected file families

- `docs/roadmap/*`
- architecture handoff references
- future deployment/integration notes
- future adapter and wrapper documentation

## Dependencies

- `RM-GOV-001` — integrated roadmap-to-development tracking system
- `RM-GOV-006` — hybrid roadmap operations layer with Plane on top of repo-doc canonical roadmap
- `RM-GOV-007` — Plane deployment, roadmap field mapping, and repo-to-Plane sync implementation

## Risks and issues

### Key risks

- the catalog could become stale if it is not maintained as part of normal roadmap intake and review
- unresolved external products could create false assumptions if they are not clearly labeled and revisited

### Known issues / blockers

- some external-system entries still need stronger per-item traceability into roadmap work
- certain named systems, such as unresolved athlete-data tools, still need final verification

## CMDB / asset linkage

- the registry should later link external systems to owned services, hosts, devices, and inventory/CMDB records where applicable
- app-level entries should remain usable as inputs to capability mapping and impact analysis

## Grouping candidates

- `RM-GOV-001`
- `RM-GOV-006`
- `RM-GOV-007`

## Grouped execution notes

- Shared-touch rationale: this item shares the roadmap registry, naming, impact transparency, adoption discipline, and future sync surfaces with the rest of the governance block.
- Repeated-touch reduction estimate: high if handled together with broader roadmap-governance and software-catalog work.
- Grouping recommendation: `Bundle now` with adjacent roadmap-governance work when feasible.

## Recommended first milestone

Create the initial external applications and integrations catalog with the currently known software set, official links, phase/group placement, and integration posture, then normalize links from future roadmap items back to this registry.

## Status transition notes

- Expected next status: `Planned`
- Transition condition: the catalog structure is accepted and cross-linking/back-reference conventions are defined
- Validation / closeout condition: the registry is maintained through normal intake/change-control practice and materially supports active roadmap work

## Notes

This item creates the long-lived catalog/reference layer for external systems. It does not replace per-item roadmap planning; it supports it.