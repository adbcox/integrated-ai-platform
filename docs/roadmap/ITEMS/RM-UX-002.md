# RM-UX-002

- **ID:** `RM-UX-002`
- **Title:** Collapsible kanban columns with count badges
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

Allow each kanban column (Backlog/Planned/In Progress/Completed) to collapse to a thin strip showing only the column title and item count, saving horizontal space.

## Key requirements

- click column header to toggle collapsed state
- collapsed state stored in localStorage per column
- badge shows item count when collapsed

## Expected file families

- JS + CSS in `web/dashboard/index.html` kanban section (≈40 lines added)

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
