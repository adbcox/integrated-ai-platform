# Legacy Roadmap Notice

This file exists to prevent ambiguity inside the legacy `roadmap/` tree.

## Canonical authority

The canonical normalized roadmap system for this repository is:

- `docs/roadmap/`
- `docs/roadmap/ROADMAP_INDEX.md`
- `docs/roadmap/STANDARDS.md`

## How to interpret files under `roadmap/`

Unless a file explicitly says it has been migrated or superseded, treat markdown under `roadmap/` as one of the following:

- historical planning context
- historical execution handoffs
- legacy status or reporting artifacts
- package progression history

These files may still be useful for understanding prior execution history, but they are **not** the canonical backlog database.

## Rules

- Do not add new roadmap items under `roadmap/`.
- Do not maintain duplicate roadmap item definitions in both `roadmap/` and `docs/roadmap/`.
- If a legacy file and a file in `docs/roadmap/` disagree, `docs/roadmap/` wins.
- New issues, PRs, handoffs, and execution packages should reference canonical roadmap IDs from `docs/roadmap/ROADMAP_INDEX.md`.

## Migration posture

Legacy files in this subtree may be:

- left in place as historical records,
- marked as legacy references,
- or migrated selectively into the canonical roadmap system when they still provide active planning value.

Until such migration occurs, this subtree should be read as legacy support material only.
