# RM-SCALE-008

- **ID:** `RM-SCALE-008`
- **Title:** Worker health endpoint for multi-executor monitoring
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

Add GET `/api/workers/health` that returns per-worker PID, current item, elapsed time, memory usage, and last heartbeat for all active executor processes.

## Key requirements

- reads `/tmp/executor_*.log` and pgrep to build worker list
- returns JSON array of worker status dicts
- integrated into dashboard Controls tab

## Expected file families

- handler added to `web/dashboard/server.py` `_worker_health()` (≈50 lines)

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
