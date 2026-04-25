# RM-UX-003

- **ID:** `RM-UX-003`
- **Title:** Full-text search bar for roadmap kanban
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

Add a search/filter input above the kanban board that filters visible cards in real time by matching against item ID, title, and category (case-insensitive substring match).

## Key requirements

- `<input id='kanban-search'>` with debounced (200 ms) `input` handler
- cards with no match get `display:none`
- match count shown below input

## Expected file families

- HTML + JS in `web/dashboard/index.html` Roadmap tab (≈35 lines added)

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
