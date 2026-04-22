# Integrated AI Platform Roadmap

This directory is the canonical roadmap system for the repository.

## Purpose

The roadmap is the authoritative planning and governance layer for the platform. It exists to:

- standardize roadmap item IDs and categories
- normalize scoring and evaluation metrics
- make impact scope explicit before execution
- support grouping of related items into shared execution packages
- improve linkage between roadmap, development, and CMDB-style system inventory

## Operating model

- **Canonical source of truth:** repo docs in `docs/roadmap/`
- **Single master roadmap document:** `docs/roadmap/ROADMAP_MASTER.md`
- **Implementation enrichment guide:** `docs/roadmap/HIGH_PRIORITY_IMPLEMENTATION_GUIDE.md`
- **Execution pack index:** `docs/roadmap/EXECUTION_PACK_INDEX.md`
- **Execution derivative:** GitHub issues, PRs, and implementation packages
- **Reference key:** every execution artifact should reference one or more roadmap IDs such as `RM-GOV-001`

## Canonicality note

This `docs/roadmap/` directory supersedes the older top-level `roadmap/` documentation root.

- Use `docs/roadmap/` for all new roadmap updates.
- Treat the top-level `roadmap/` tree as legacy planning storage unless and until it is fully migrated.
- Do not create new canonical roadmap items in multiple places.

## Read-first order

1. `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`
2. `docs/roadmap/ROADMAP_AUTHORITY.md`
3. `docs/roadmap/ROADMAP_STATUS_SYNC.md`
4. `docs/roadmap/ROADMAP_MASTER.md`
5. `docs/roadmap/ROADMAP_INDEX.md`
6. `docs/roadmap/STANDARDS.md`
7. `docs/roadmap/ARCHITECTURE_ALIGNMENT.md`
8. `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`

## Directory contents

### Core roadmap set

- `ROADMAP_MASTER.md` — single first-read master roadmap document and priority authority
- `ROADMAP_INDEX.md` — master normalized roadmap index
- `HIGH_PRIORITY_IMPLEMENTATION_GUIDE.md` — implementation-oriented enrichment guide for critical and high-value roadmap items
- `EXECUTION_PACK_INDEX.md` — canonical index of dedicated execution packs
- `STANDARDS.md` — IDs, categories, statuses, metrics, naming, readiness, and impact rules
- `ARCHITECTURE_ALIGNMENT.md` — architecture-to-roadmap alignment rules
- `FEATURE_BLOCK_GROUPING.md` — grouped-package planning logic for shared-touch work
- `CMDB_LINKAGE.md` — mapping expectations between roadmap items and systems/assets
- `EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md` — canonical external systems catalog
- `EXTERNAL_SYSTEM_TO_ROADMAP_CROSSWALK.md` — dependency crosswalk from external systems to roadmap work

### PM / governance operating docs

- `DOCUMENT_MAP.md` — concise map of the roadmap document set
- `SOURCE_OF_TRUTH_MATRIX.md` — which document controls which class of planning truth
- `OPERATING_MODEL.md` — how the roadmap should be operated day to day
- `CHANGE_CONTROL.md` — how roadmap changes must be recorded
- `INTAKE_AND_NORMALIZATION_PROCESS.md` — how new items enter the canonical roadmap
- `EXECUTION_READINESS_CHECKLIST.md` — checklist before an item is treated as execution-ready
- `STATUS_TRANSITION_RULES.md` — normalized roadmap status movement rules
- `ITEM_MATURITY_MODEL.md` — maturity model independent of status
- `BACKLOG_HYGIENE_CHECKLIST.md` — recurring backlog quality checks
- `DEPENDENCY_MANAGEMENT.md` — dependency and blocker handling guidance
- `RISK_AND_ISSUE_MANAGEMENT.md` — risk, issue, and escalation guidance
- `REVIEW_CADENCE.md` — planning review and sync cadence
- `WORKING_CONVENTIONS.md` — naming, reference, issue/PR, and traceability conventions
- `DOCUMENT_RETENTION_AND_DEPRECATION_POLICY.md` — how roadmap docs are retained, superseded, or deprecated

### Supporting and historical materials

- `ROADMAP_CHAT_SYNC_2026-04-21.md` — detailed normalization of roadmap items captured in chat and synced into the canonical roadmap system
- `EXECUTION_CONTEXT_SYNC_2026-04-21.md` — selective migration of durable execution-context from legacy roadmap status material
- `TEMPLATES/ROADMAP_ITEM_TEMPLATE.md` — template for new roadmap items
- `ITEMS/` — per-item detail files where used

## Workflow

1. Read the architecture master first for platform direction.
2. Read roadmap authority and status docs for current state truth.
3. Use `ROADMAP_MASTER.md` for strategic interpretation.
4. Use `ROADMAP_INDEX.md` for backlog inventory.
5. Use `STANDARDS.md` and the PM operating docs for intake, readiness, dependency, lifecycle, maturity, and review discipline.
6. Use grouped-execution, CMDB linkage, and external-system docs as needed.
7. Open GitHub issues or execution docs only after the roadmap item is clear enough to drive work.

## Rule

Issues are not the canonical roadmap database.
They are downstream execution artifacts derived from the roadmap docs.
