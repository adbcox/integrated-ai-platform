# RM-PLUGIN-003

- **ID:** `RM-PLUGIN-003`
- **Title:** Plugin configuration schema and validator
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

Define a JSON Schema for `plugin.json` manifests and validate each plugin's manifest on load, rejecting invalid plugins with a clear error message rather than a stack trace.

## Key requirements

- JSON Schema in `config/plugin_manifest_schema.json` (≈30 lines)
- `validate_manifest(manifest_dict)` using `jsonschema` or inline validation
- detailed error messages naming the invalid field

## Expected file families

- `config/plugin_manifest_schema.json` (≈30 lines) + validation in `framework/plugin_registry.py` (≈20 lines added)

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
