# Roadmap Authority Model

## Purpose

This document defines where roadmap truth lives and which other roadmap files are derived views.

It exists to prevent split authority and stale status displays.

## Current authority model on `main`

### Canonical visible status source
- `docs/roadmap/ROADMAP_STATUS_SYNC.md`

This is the canonical status rollup for the repository branch currently used as the visible roadmap surface.

### Derived human-readable summary views
- `docs/roadmap/ROADMAP_MASTER.md`
- `docs/roadmap/ROADMAP_INDEX.md`

These files are summary/inventory views. They must agree with `ROADMAP_STATUS_SYNC.md` and must not contradict it.

### Supporting planning views
- `docs/roadmap/EXECUTION_PACK_INDEX.md`
- execution packs under `docs/roadmap/*_EXECUTION_PACK.md`

These files support execution planning. They do not control completion status by themselves.

## Future registry model

If and when a per-item registry is merged and visible on this branch, such as:
- `docs/roadmap/items/RM-*.yaml`

then that per-item registry should become the canonical item-state layer, and `ROADMAP_STATUS_SYNC.md` should be regenerated from it.

Until that registry is visible and consistently maintained on this branch, `ROADMAP_STATUS_SYNC.md` is the canonical visible status source.

## Rules

1. Do not use `ROADMAP_MASTER.md` as direct status truth.
2. Do not use `ROADMAP_INDEX.md` as direct completion truth.
3. Do not mark an item active in a summary view if it is marked completed or archived in `ROADMAP_STATUS_SYNC.md`.
4. When item status changes, update `ROADMAP_STATUS_SYNC.md` and then reconcile summary views.
5. Execution packs make an item execution-ready; they do not by themselves mean the item is completed.

## Repair note

This authority model is the immediate repair for a previously broken roadmap architecture where visible summary docs remained stale after completion/archive work.
