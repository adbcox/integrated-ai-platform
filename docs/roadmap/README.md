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
- **Execution derivative:** GitHub issues, PRs, and implementation packages
- **Reference key:** every execution artifact should reference one or more roadmap IDs such as `RM-GOV-001`

## Directory contents

- `ROADMAP_INDEX.md` — master roadmap index
- `STANDARDS.md` — IDs, categories, statuses, metrics, naming, and impact rules
- `FEATURE_BLOCK_GROUPING.md` — grouped-package planning logic for shared-touch work
- `CMDB_LINKAGE.md` — mapping expectations between roadmap items and systems/assets
- `TEMPLATES/ROADMAP_ITEM_TEMPLATE.md` — template for new roadmap items

## Workflow

1. Add or amend roadmap items here first.
2. Assign stable ID, category, type, and normalized metrics.
3. Record affected systems, expected file families, and dependencies.
4. Evaluate whether the item should be executed alone or as part of a grouped feature block.
5. Open GitHub issues or execution docs only after the roadmap item is clear enough to drive work.

## Rule

Issues are not the canonical roadmap database.
They are downstream execution artifacts derived from the roadmap docs.
