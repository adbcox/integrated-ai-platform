# RM-MOBILE-001

- **ID:** `RM-MOBILE-001`
- **Title:** Responsive layout breakpoints for dashboard
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

Add CSS media queries so the dashboard is usable on screens ≥375 px wide: sidebar collapses to bottom nav, kanban scrolls horizontally, charts resize to full width.

## Key requirements

- `@media (max-width: 768px)` rules for all major layout components
- horizontal scroll on kanban with snap points
- bottom tab bar replaces sidebar on mobile

## Expected file families

- CSS in `web/dashboard/index.html` `<style>` block (≈60 lines added)

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
