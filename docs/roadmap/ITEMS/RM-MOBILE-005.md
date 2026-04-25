# RM-MOBILE-005

- **ID:** `RM-MOBILE-005`
- **Title:** Mobile-optimized card compact view
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

On screens < 768 px, switch kanban cards from full layout to a compact 2-line view (ID + truncated title + status badge) to fit more cards without horizontal scroll per column.

## Key requirements

- CSS `@media` compact card variant with reduced padding and font size
- title truncated at 40 chars with `text-overflow: ellipsis`
- tap to expand to full card inline

## Expected file families

- CSS + JS in `web/dashboard/index.html` (≈35 lines added)

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
