# RM-UX-008

- **ID:** `RM-UX-008`
- **Title:** Quick action floating toolbar
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

Add a floating action bar (bottom-center, above footer) with four buttons: ▶ Start Executor, ⏹ Stop, 📊 Analytics, ⌨ Shortcuts — visible on all tabs.

## Key requirements

- fixed-position bar with CSS backdrop-filter blur
- buttons call existing `execAction()`, `switchTab()` functions
- auto-hides when modal or panel is open

## Expected file families

- HTML + CSS + JS in `web/dashboard/index.html` (≈40 lines added)

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
