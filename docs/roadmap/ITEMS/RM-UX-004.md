# RM-UX-004

- **ID:** `RM-UX-004`
- **Title:** Toast notification system for async operation feedback
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

Show slide-in toast messages (success/warning/error) at the bottom-right corner when executor starts/stops, training starts, or model deploys — auto-dismiss after 4 s.

## Key requirements

- `showToast(msg, type='success'|'warn'|'error')` JS function
- CSS transitions for slide-in/slide-out
- max 3 toasts visible at once (oldest dismissed first)

## Expected file families

- CSS + JS in `web/dashboard/index.html` (≈50 lines added)

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
