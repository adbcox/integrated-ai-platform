# RM-MOBILE-003

- **ID:** `RM-MOBILE-003`
- **Title:** Progressive Web App manifest and service worker stub
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

Add `manifest.json` and a minimal `service-worker.js` (cache-first for static assets) so the dashboard can be added to the iOS/Android home screen and load offline.

## Key requirements

- `web/dashboard/manifest.json` with name, icons, theme color, display=standalone
- `web/dashboard/service-worker.js` caching index.html + JS
- `<link rel=manifest>` in index.html head

## Expected file families

- `web/dashboard/manifest.json` (≈20 lines) + `web/dashboard/service-worker.js` (≈40 lines)

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
