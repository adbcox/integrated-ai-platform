# RM-PLUGIN-005

- **ID:** `RM-PLUGIN-005`
- **Title:** Plugin sandboxing with allowed-import whitelist
- **Category:** `PLUGIN`
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

Wrap plugin module loading in a restricted import hook that blocks access to `os.system`, `subprocess`, and network calls unless the plugin declares the `trusted: true` flag in its manifest.

## Key requirements

- `RestrictedImporter` using `sys.meta_path` hook
- blocklist: `subprocess`, `socket`, `urllib` when `trusted=false`
- `trusted: true` plugins bypass restriction with an audit log entry

## Expected file families

- `framework/plugin_sandbox.py` — `RestrictedImporter` class (≈80 lines)

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
