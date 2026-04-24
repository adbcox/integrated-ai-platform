# RM-GOV-006

- **ID:** `RM-GOV-006`
- **Title:** Hybrid roadmap operations layer with Plane on top of repo-doc canonical roadmap
- **Category:** `GOV`
- **Type:** `Enhancement`
- **Status:** `Completed`
- **Maturity:** `M3`
- **Priority:** `High`
- **Priority class:** `P1`
- **Queue rank:** `1`
- **Target horizon:** `next`
- **LOE:** `M`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `2`
- **Dependency burden:** `3`
- **Readiness:** `now`

## Description

Implement a hybrid roadmap operating model in which the repository documentation under `docs/roadmap/` remains the canonical source of truth, while a self-hosted Plane deployment becomes the active planning, execution, and visualization layer for roadmap items that are ready to move into operational work.

## Why it matters

The current roadmap model is strong at governance definition but weak as an operational layer for day-to-day planning, grouped execution handling, and active implementation tracking. A hybrid model preserves the repo-centered canonical structure while reducing friction in backlog handling, execution flow, and active roadmap visualization.

## Key requirements

- repo roadmap docs remain canonical
- Plane is used as the operational planning and execution layer
- roadmap items retain stable `RM-...` IDs
- Plane mirrors or syncs active roadmap items rather than replacing the repo docs
- grouped execution blocks must be representable in the operational layer
- roadmap metadata must remain structured enough to preserve naming, impact, dependency, and grouping context
- GitHub issues and PRs remain downstream execution artifacts tied back to roadmap IDs

## Affected systems

- roadmap governance layer
- repo documentation structure under `docs/roadmap/`
- GitHub execution flow
- future CMDB linkage layer
- future grouped execution / package planning workflow
- future automation layer that syncs roadmap data into an operational tool

## Expected file families

- `docs/roadmap/*`
- future roadmap sync tooling
- future issue / PR templates
- future automation / integration files for Plane connectivity

## Dependencies

- `RM-GOV-001` — integrated roadmap-to-development tracking system
- `RM-GOV-002` — recurring full-system integrity review
- `RM-GOV-003` — feature-block package planner

## Risks and issues

### Key risks

- Plane could become treated as a new planning authority instead of an operational overlay
- metadata drift could occur if repo docs and operational-layer fields diverge

### Known issues / blockers

- final property mapping and sync conventions still need to be documented and tested
- pull planning still needs a small pilot scope before this model is treated as fully operational

## CMDB / asset linkage

- roadmap item identity should remain linkable to systems, services, assets, and future CMDB records
- the operational layer must not break future CMDB-aware planning and grouped execution analysis

## Grouping candidates

- `RM-GOV-001`
- `RM-GOV-002`
- `RM-GOV-003`

## Grouped execution notes

- Shared-touch rationale: this item shares the roadmap registry, metrics, naming, impact-scope, execution-state, and grouped-planning surfaces already defined in the governance block.
- Repeated-touch reduction estimate: high if implemented together with roadmap governance and grouping work.
- Grouping recommendation: `Bundle now` with other governance-layer roadmap work when feasible.

## Recommended first milestone

Stand up Plane in a self-hosted configuration, define a matching custom-property model for roadmap metadata, and sync a small set of active roadmap items into Plane while preserving repo docs as the canonical source of truth.

## Status transition notes

- Expected next status: `Planned`
- Transition condition: hybrid operating model confirmed, pilot scope identified, and governance placement agreed
- Validation / closeout condition: operational model is documented, piloted, and reflected in canonical roadmap/governance surfaces

## Notes

This item does not authorize replacing the repo-doc roadmap as canonical. It specifically implements the hybrid model in which repo docs remain authoritative and Plane acts as the operational planning/execution layer.