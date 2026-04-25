# RM-PERF-010

- **ID:** `RM-PERF-010`
- **Title:** Small-LOE task batcher for executor throughput
- **Category:** `PERF`
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

Group consecutive S-LOE roadmap items into batches of up to 5 and pass them to a single aider invocation, reducing model cold-start overhead per item.

## Key requirements

- `batch_small_items(items, max_batch=5)` groups adjacent S items
- batch prompt template that applies N edits sequentially
- fallback to single-item mode on batch failure

## Expected file families

- `framework/task_batcher.py` — `batch_small_items()` and `format_batch_prompt()` (≈70 lines)

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
