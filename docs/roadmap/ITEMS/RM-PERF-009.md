# RM-PERF-009

- **ID:** `RM-PERF-009`
- **Title:** Memory-mapped log tail reader
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

Use `mmap` to read only the last N bytes of large executor log files instead of seeking through the whole file, keeping `/api/executor/status` fast even on 100 MB logs.

## Key requirements

- `tail_bytes(path, n=16384)` using mmap
- fallback to seek-based read on unsupported FS
- integrated into server.py _parse_log()

## Expected file families

- `framework/log_tail.py` — `tail_bytes(path, n) -> str` (≈45 lines)

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
