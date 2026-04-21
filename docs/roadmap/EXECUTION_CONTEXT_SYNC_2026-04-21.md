# Execution Context Sync — 2026-04-21

This document records a selective migration sweep of high-value legacy execution-context material from the top-level `roadmap/` tree into the canonical roadmap system at `docs/roadmap/`.

## Canonicality rule

- **Canonical normalized roadmap root:** `docs/roadmap/`
- **Legacy execution/history root:** `roadmap/`
- **Interpretation:** Files under `roadmap/` may still carry useful historical context, but they are not the canonical normalized roadmap database.

## Selective sweep scope

This sweep focused on high-value legacy execution-context under:

- `roadmap/status/`
- `roadmap/planning/`
- `roadmap/handoffs/`

Because the GitHub connector in this session could not reliably enumerate the full subtree, this sweep used a selective best-effort approach:

1. migrate durable status context that was directly verifiable,
2. mark the verified legacy file inline,
3. add subtree-level notices to likely reader entrypoints,
4. record the migration decision here in the canonical roadmap system.

## Migrated durable context

### Legacy source
- `roadmap/status/phase6_progress.md`

### Durable content preserved here
- Active phase recorded there: **Phase 6 — Live-Operating Bridge and External Environment Entry**
- Latest accepted package recorded there: **LOB-W6**
- Latest accepted commit recorded there: **`b43b932`**
- Accepted package chain recorded there:
  - `LOB-W1`
  - `LOB-W2`
  - `LOB-W3`
  - `LOB-INT-1`
  - `LOB-W4`
  - `LOB-W5`
  - `LOB-W6`

### Migration treatment
- The source file remains in place as historical execution-status context.
- The source file is now marked inline as legacy and points back to this canonical sync file.
- This document is the canonical bridge for interpreting that legacy status file.

## Legacy subtree treatment

### `roadmap/status/`
Treat as legacy status history unless individual files are later migrated into `docs/roadmap/` or another canonical docs location.

### `roadmap/planning/`
Treat as legacy planning prompts/artifacts. Planning content there may still be useful operational context, but new normalized roadmap maintenance belongs in `docs/roadmap/`.

### `roadmap/handoffs/`
Treat as legacy handoff/archive material. New durable roadmap-to-execution linkage should reference canonical roadmap IDs from `docs/roadmap/ROADMAP_INDEX.md`.

## Reader rule

When a legacy file under `roadmap/status/`, `roadmap/planning/`, or `roadmap/handoffs/` appears to conflict with the normalized roadmap in `docs/roadmap/`, the canonical `docs/roadmap/` version wins.

## Follow-on migration posture

If additional high-value files from `roadmap/planning/` or `roadmap/handoffs/` are later identified as still operationally important, they should be:

1. marked inline as legacy,
2. summarized or migrated into `docs/roadmap/`, and
3. linked back to canonical roadmap IDs where appropriate.
