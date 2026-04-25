# RM-SCALE-002

- **ID:** `RM-SCALE-002`
- **Title:** Executor heartbeat monitor
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

Write a lightweight watchdog that pings `/api/executor/status` every 30 s and restarts the executor process if it stops updating its log for >5 min.

## Key requirements

- `HeartbeatMonitor` class with configurable thresholds
- restart via `subprocess.Popen` with exponential back-off
- log heartbeat events to `/tmp/heartbeat.log`

## Expected file families

- `framework/heartbeat.py` — `HeartbeatMonitor` (≈70 lines)

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
