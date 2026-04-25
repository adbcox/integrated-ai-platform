# RM-PLUGIN-001

- **ID:** `RM-PLUGIN-001`
- **Title:** Plugin registry and loader
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

Implement a plugin registry that scans `plugins/` directory for Python packages with a `plugin.json` manifest, loads them on startup, and exposes a `PluginRegistry.get(name)` lookup.

## Key requirements

- `PluginRegistry` class scanning `plugins/*/plugin.json`
- manifest fields: name, version, entry_point, hooks
- `load_all()` imports entry_point module and calls `register(registry)`

## Expected file families

- `framework/plugin_registry.py` — `PluginRegistry` class (≈75 lines)

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
