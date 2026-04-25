# RM-SCALE-006

- **ID:** `RM-SCALE-006`
- **Title:** Overflow queue for failed executor tasks
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

Store items that failed ≥2 times in a separate `artifacts/overflow_queue.jsonl` for human review, preventing retry storms while preserving failure context.

## Key requirements

- `OverflowQueue` with `push(item_id, reason, attempts)` and `list()` methods
- JSONL format with timestamp and full error message
- dashboard endpoint GET /api/overflow to display it

## Expected file families

- `framework/overflow_queue.py` — `OverflowQueue` class (≈55 lines)

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
