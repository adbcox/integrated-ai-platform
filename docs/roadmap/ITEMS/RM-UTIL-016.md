# RM-UTIL-016

- **ID:** `RM-UTIL-016`
- **Title:** Color terminal output helpers
- **Category:** `UTIL`
- **Type:** `Feature`
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

ANSI color wrappers: red(), green(), yellow(), blue(), bold() that auto-disable when not a TTY.

## Deliverable

framework/util/colors.py — color helper functions with NO_COLOR env var support (40 lines)

## Dependencies

- no external blocking dependencies

## Risks and issues

### Key risks
- none; low-complexity isolated task

### Known issues / blockers
- none; ready to start

## Status transition notes

- Expected next status: `In progress`
- Transition condition: file created and verified
- Validation / closeout condition: module importable or script runs without error

## Notes

Self-contained S-LOE task — suitable for autonomous executor without human input.
