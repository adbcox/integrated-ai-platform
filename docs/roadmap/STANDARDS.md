# Roadmap Standards

## 1. ID format

Every roadmap item must have a stable ID:

`RM-[CATEGORY]-[###]`

Examples:

- `RM-GOV-001`
- `RM-UI-003`
- `RM-MEDIA-002`

Rules:

- IDs are permanent once assigned.
- IDs are never reused.
- A title may change, but the ID remains stable.
- Execution packages, issues, PRs, and docs should reference roadmap IDs.

## 2. Standard categories

Use one of the following categories:

- `GOV` — governance, roadmap system, naming, integrity, CMDB linkage
- `CORE` — core platform/runtime/productization capabilities
- `DEV` — developer assistant, coding automation, Xcode, firmware dev
- `UI` — main UI, control center, dashboards, tablet and ambient surfaces
- `AUTO` — agents, autonomy, workflow automation
- `OPS` — monitoring, self-healing, operational health, reporting
- `INV` — inventory, assets, capability mapping
- `MEDIA` — Plex, Sonarr, Radarr, media endpoints, acquisition flows
- `HOME` — Home Assistant and household environment automations
- `LANG` — translation and multilingual communication
- `HW` — hardware/electronics design and embedded device features
- `SHOP` — woodworking, workshop, fabrication support
- `AUTO-MECH` — automotive repair, maintenance, restoration
- `DOCAPP` — document-to-app and spreadsheet-to-web-app conversion
- `INTEL` — external OSS watchtower, ecosystem intelligence

## 3. Standard types

Each roadmap item must declare one of:

- `Program`
- `System`
- `Feature`
- `Enhancement`

Guidance:

- **Program** — broad multi-phase initiative
- **System** — substantial subsystem or platform service
- **Feature** — bounded capability or app surface
- **Enhancement** — improvement to an existing system or feature

## 4. Standard statuses

Use only the normalized status set:

- `Proposed`
- `Accepted`
- `Decomposing`
- `Planned`
- `Execution-ready`
- `In progress`
- `Validating`
- `Completed`
- `Deferred`
- `Frozen`
- `Rejected`

## 5. Standard priority scale

Use:

- `Critical`
- `High`
- `Medium`
- `Low`

## 6. Standard LOE scale

Use:

- `XS`
- `S`
- `M`
- `L`
- `XL`
- `XXL`

## 7. Standard scoring fields

Each item should carry at least:

- `Strategic value` — 1 to 5
- `Architecture fit` — 1 to 5
- `Execution risk` — 1 to 5
- `Dependency burden` — 1 to 5
- `Readiness` — `now`, `near`, `later`, or `blocked`

Optional but recommended:

- `Operational value`
- `User value`
- `Reuse potential`
- `Validation burden`
- `Drift risk`
- `Maintenance burden`
- `Security/privacy sensitivity`

## 8. Naming enforcement rules

All roadmap and execution artifacts should use canonical names.

Required naming fields:

- `canonical_name`
- `category`
- `type`
- `status`
- `priority`

Naming expectations:

- titles should be explicit and scope-accurate
- avoid duplicate concepts under slightly different names
- preserve consistent subsystem names across roadmap, code, docs, CMDB, and dashboards
- when a canonical subsystem name exists, use it exactly

## 9. Impact transparency requirements

Before work moves into execution, each item should identify:

- affected systems
- affected subsystems
- affected CMDB items or asset classes
- expected file families
- expected new-file vs existing-file touch posture
- forbidden or read-only areas
- key dependencies
- likely blast radius

This is mandatory for reducing unintended issues.

## 10. Grouping rule

Roadmap items should not only be evaluated individually.
They should also be evaluated for grouped execution when they share:

- files
- file families
- subsystems
- dashboards/UI surfaces
- inventory or CMDB schemas
- integration layers

Grouped execution should be preferred when it reduces repeated touches and lowers total LOE without creating unacceptable risk.

## 11. Canonical item schema

Each roadmap item should contain:

- `ID`
- `Title`
- `Category`
- `Type`
- `Status`
- `Priority`
- `LOE`
- `Strategic value`
- `Architecture fit`
- `Execution risk`
- `Dependency burden`
- `Readiness`
- `Description`
- `Why it matters`
- `Dependencies`
- `Affected systems`
- `Expected file families`
- `CMDB links`
- `Feature-block grouping candidates`
- `Recommended first milestone`

## 12. Canonical execution rule

Roadmap docs are the canonical source.
GitHub issues, execution prompts, package docs, and PRs are downstream execution artifacts and must reference the roadmap IDs they implement.

## 13. Mandatory intake synchronization rule

Every future roadmap intake must update the canonical roadmap docs in the same intake cycle.

### Required file updates

- **Always update:** `docs/roadmap/ROADMAP_INDEX.md`
- **Also update when priority, pull order, or strategic ranking changes:** `docs/roadmap/ROADMAP_MASTER.md`

### Intake completion rule

A roadmap intake is not complete unless:

1. the new or changed item is reflected in `ROADMAP_INDEX.md`, and
2. `ROADMAP_MASTER.md` is updated whenever the intake changes strategic priority interpretation, pull-first ordering, or the most important roadmap cluster.

### Prohibited intake pattern

Do not leave roadmap items only in:

- chat history
- legacy files under `roadmap/`
- issues without normalized roadmap entry
- ad hoc docs that are not linked back to the canonical roadmap system
