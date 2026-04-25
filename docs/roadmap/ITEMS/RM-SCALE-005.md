# RM-SCALE-005

- **ID:** `RM-SCALE-005`
- **Title:** Per-worker resource cap enforcer
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

Wrap each worker subprocess in a resource envelope that kills it if it exceeds 4 GB RSS or 90% CPU for >60 s, preventing runaway LLM calls from starving other workers.

## Key requirements

- `ResourceCap` context manager using `resource.setrlimit` and a monitor thread
- configurable limits via constructor
- emits SIGTERM then SIGKILL on breach

## Expected file families

- `framework/resource_cap.py` — `ResourceCap` context manager (≈75 lines)

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
