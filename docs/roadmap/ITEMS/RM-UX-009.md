# RM-UX-009

- **ID:** `RM-UX-009`
- **Title:** Column-level completion percentage ring
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

Show a small SVG donut ring next to each kanban column header indicating what percentage of items in that category are Completed, giving an at-a-glance category health view.

## Key requirements

- inline SVG circle with `stroke-dasharray` calculated from completed/total ratio
- color-coded: green ≥75%, yellow ≥40%, red <40%
- tooltip on hover shows exact counts

## Expected file families

- SVG + JS in `web/dashboard/index.html` kanban headers (≈45 lines added)

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
