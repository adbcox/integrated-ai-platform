# RM-SCALE-004

- **ID:** `RM-SCALE-004`
- **Title:** Structured log aggregator for multiple executor logs
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

Merge events from all `/tmp/executor_*.log` files into a single chronological JSONL stream at `artifacts/executor_events.jsonl`, with deduplication by (item_id, timestamp).

## Key requirements

- `aggregate_logs(glob_pattern, output_path)` function
- parses ✅/❌ lines into structured dicts with timestamp, item, result
- idempotent: safe to call repeatedly

## Expected file families

- `framework/log_aggregator.py` — `aggregate_logs()` (≈65 lines)

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
