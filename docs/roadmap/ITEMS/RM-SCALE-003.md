# RM-SCALE-003

- **ID:** `RM-SCALE-003`
- **Title:** Task deduplication guard for concurrent workers
- **Category:** `SCALE`
- **Type:** `Enhancement`
- **Status:** `Accepted`
- **Maturity:** `M0`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `1`
- **Target horizon:** `immediate`
- **LOE:** `S`
- **Strategic value:** `3`
- **Architecture fit:** `4`
- **Execution risk:** `1`
- **Dependency burden:** `0`
- **Readiness:** `immediate`

## Description

Maintain a file-backed set of in-progress item IDs so that parallel workers never attempt the same roadmap item simultaneously even across process restarts.

## Key requirements

- `DedupGuard` with `acquire(item_id)` / `release(item_id)` / `is_locked(item_id)`
- backed by a JSON file under `/tmp/dedup_guard.json`
- TTL of 30 min to auto-release stale locks

## Expected file families

- `framework/dedup_guard.py` — `DedupGuard` class (≈60 lines)

## Dependencies

- no external blocking dependencies

## Risks and issues

### Key risks
- none; low-complexity task

### Known issues / blockers
- none; ready to start

## Status transition notes

- Expected next status: `In progress`
- Transition condition: file created and verified
- Validation / closeout condition: module importable, unit tests pass

## Notes

Small, self-contained task — ideal for autonomous executor.
