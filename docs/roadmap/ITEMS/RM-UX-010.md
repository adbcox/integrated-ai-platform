# RM-UX-010

- **ID:** `RM-UX-010`
- **Title:** Export roadmap to CSV one-click download
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

Add an Export CSV button to the Controls tab that generates and downloads a CSV file with columns: ID, Title, Category, Status, LOE, Readiness, Execution risk — one row per item.

## Key requirements

- client-side CSV generation from the roadmap JSON already loaded
- uses `Blob` + `URL.createObjectURL` download trick
- filename includes today's date

## Expected file families

- JS in `web/dashboard/index.html` Controls tab (≈30 lines added)

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
