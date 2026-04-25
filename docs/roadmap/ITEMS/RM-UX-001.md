# RM-UX-001

- **ID:** `RM-UX-001`
- **Title:** Dark/light mode toggle with system preference detection
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

Add a sun/moon toggle button to the dashboard header that switches between dark (#0D1117) and light (#F6F8FA) themes, persisted to localStorage and defaulting to system prefers-color-scheme.

## Key requirements

- CSS custom property swap via `data-theme` attribute on `<html>`
- toggle button in header with animated icon
- localStorage persistence across page loads

## Expected file families

- CSS variables in `web/dashboard/index.html` `<style>` block (≈30 lines added)

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
