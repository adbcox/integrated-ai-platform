# OpenProject Enrichment Doctrine (D-17-55)

Date: 2026-05-03
Status: Active

## Canonical authority

- `docs/PROJECT_FRAMEWORK.md` §9 is source-of-truth.
- OpenProject is an enriched operational view only.
- Manual OpenProject description edits are preserved by default; canonical overwrite requires `--force`.

## Managed enrichment fields

- `description`: synthesized from framework reference + optional closeout/results excerpt.
- `percentageDone`: derived from WP marker completion ratio in framework reference; fallback from deliverable status.
- Custom fields:
  - `phase`
  - `deliverable_class`
  - `finding_refs`
  - `dependencies`

## Preserved/non-managed fields

- `dueDate`: operator-managed, not framework-managed.
- `customField1` (Plane RM ID): historical mapping, preserve as-is.
- `customField2` (External ID): sync key, preserve as-is.

## Execution model

- Bootstrap fields (admin rails-runner):
  - `scripts/openproject-bootstrap-enrichment-fields.sh`
- Enrichment sync (idempotent, delta-only):
  - `scripts/openproject-enrich-from-framework.py`
- Framework sync integration:
  - `scripts/openproject-sync-from-framework.py` invokes enrichment unless `--skip-enrich`.

## Conflict policy

- Default: if target field already has a non-empty differing value, mark conflict and skip overwrite.
- `--force`: allow canonical overwrite for managed fields.
