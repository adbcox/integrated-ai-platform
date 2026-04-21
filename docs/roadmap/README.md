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
- **Execution derivative:** GitHub issues, PRs, and implementation packages
- **Reference key:** every execution artifact should reference one or more roadmap IDs such as `RM-GOV-001`

## Canonicality note

This `docs/roadmap/` directory supersedes the older top-level `roadmap/` documentation root.

- Use `docs/roadmap/` for all new roadmap updates.
- Treat the top-level `roadmap/` tree as legacy planning storage unless and until it is fully migrated.
- Do not create new canonical roadmap items in multiple places.

## Directory contents

- `ROADMAP_MASTER.md` — single first-read master roadmap document and priority authority
- `ROADMAP_INDEX.md` — master normalized roadmap index
- `STANDARDS.md` — IDs, categories, statuses, metrics, naming, and impact rules
- `FEATURE_BLOCK_GROUPING.md` — grouped-package planning logic for shared-touch work
- `CMDB_LINKAGE.md` — mapping expectations between roadmap items and systems/assets
- `ROADMAP_CHAT_SYNC_2026-04-21.md` — detailed normalization of roadmap items captured in chat and synced into the canonical roadmap system
- `EXECUTION_CONTEXT_SYNC_2026-04-21.md` — selective migration of durable execution-context from legacy roadmap status material
- `TEMPLATES/ROADMAP_ITEM_TEMPLATE.md` — template for new roadmap items

## Workflow

1. Read `ROADMAP_MASTER.md` first for strategic priority and canonical interpretation.
2. Add or amend roadmap items in `ROADMAP_INDEX.md`.
3. Assign stable ID, category, type, and normalized metrics.
4. Record affected systems, expected file families, and dependencies.
5. Evaluate whether the item should be executed alone or as part of a grouped feature block.
6. Open GitHub issues or execution docs only after the roadmap item is clear enough to drive work.

## Rule

Issues are not the canonical roadmap database.
They are downstream execution artifacts derived from the roadmap docs.
