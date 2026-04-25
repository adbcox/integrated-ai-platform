# RM-UX-007

- **ID:** `RM-UX-007`
- **Title:** Roadmap item detail side panel
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

Clicking any kanban card opens a right-side slide-in panel showing the full item markdown (ID, title, description, requirements, deliverable, dependencies) without leaving the board.

## Key requirements

- `<aside id='item-panel'>` with CSS transform slide animation
- fetches item data from `/api/roadmap/item/<id>` (new endpoint)
- close via Escape key or × button

## Expected file families

- HTML + CSS + JS + server handler in dashboard files (≈80 lines added)

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
