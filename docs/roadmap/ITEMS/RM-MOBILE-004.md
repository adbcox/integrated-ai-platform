# RM-MOBILE-004

- **ID:** `RM-MOBILE-004`
- **Title:** Offline status banner
- **Category:** `MOBILE`
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

Show a yellow banner at the top of the page when the browser goes offline (navigator.onLine = false), indicating that live data may be stale — auto-dismiss when connection restores.

## Key requirements

- `window.addEventListener('offline'/'online')` handler
- banner styled with `--clr-warn` background
- no polling suppressed — graceful degradation

## Expected file families

- JS + CSS in `web/dashboard/index.html` (≈25 lines added)

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
