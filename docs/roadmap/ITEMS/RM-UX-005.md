# RM-UX-005

- **ID:** `RM-UX-005`
- **Title:** Progress bar for active executor with ETA
- **Category:** `UX`
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

Show a thin progress bar at the top of the page (similar to browser loading indicator) while the executor is running, based on completed/total items with an estimated time remaining label.

## Key requirements

- reads `completed` and `total` from `/api/executor/status`
- ETA calculated from average completion rate over last 10 items
- disappears smoothly when executor stops

## Expected file families

- CSS + JS in `web/dashboard/index.html` Overview tab (≈40 lines added)

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
