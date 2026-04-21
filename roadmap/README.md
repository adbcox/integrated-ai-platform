# Roadmap

This directory is a legacy planning and execution documentation root for the integrated-ai-platform project.

## Status

This top-level `roadmap/` tree is no longer the canonical roadmap source.

- **Canonical roadmap root:** `docs/roadmap/`
- **Use `docs/roadmap/` for all new roadmap updates and normalized backlog maintenance.**
- Existing materials here should be treated as historical planning storage unless and until they are migrated.

## Legacy subtree rule

Unless a file explicitly states otherwise, markdown under `roadmap/` should be treated as **legacy planning or historical execution context**, not as the canonical normalized roadmap database.

- Do **not** add new roadmap items under `roadmap/`.
- Do **not** treat files in this tree as the authoritative backlog unless they have been explicitly migrated into `docs/roadmap/`.
- When a legacy file conflicts with `docs/roadmap/`, the `docs/roadmap/` version wins.
- New roadmap-to-execution linkage should reference canonical roadmap IDs from `docs/roadmap/ROADMAP_INDEX.md`.

## Historical structure

- `roadmap_master.md` — historical primary roadmap and package progression summary
- `status/` — current phase and progress snapshots
- `planning/` — short planning-window prompts and planning artifacts
- `handoffs/` — execution-ready handoffs and large text artifacts
- `reports/` — execution reports, validation summaries, and milestone reports

## Operating rule

Chat remains a control surface for short planning prompts.
Canonical roadmap maintenance now belongs in `docs/roadmap/` so the repo has a single normalized roadmap authority.
