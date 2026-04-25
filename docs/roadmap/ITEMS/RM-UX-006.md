# RM-UX-006

- **ID:** `RM-UX-006`
- **Title:** Keyboard navigation for kanban cards
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

Allow users to navigate kanban cards with arrow keys (up/down within column, left/right between columns) and press Enter to expand a card's detail view.

## Key requirements

- `tabindex=0` on each card with `keydown` handler
- focus ring visible in both themes
- Enter opens inline detail pane with full item text

## Expected file families

- JS in `web/dashboard/index.html` Roadmap tab (≈55 lines added)

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
