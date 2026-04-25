# RM-PLUGIN-002

- **ID:** `RM-PLUGIN-002`
- **Title:** Event hook system for executor lifecycle events
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

Add a synchronous event bus to the executor that fires named hooks (`on_item_start`, `on_item_complete`, `on_item_fail`, `on_executor_stop`) allowing plugins to react without modifying core code.

## Key requirements

- `EventBus` with `subscribe(event, callback)` and `emit(event, **kwargs)`
- thread-safe callback dispatch with exception isolation per handler
- integrated into auto_execute_roadmap.py at key lifecycle points

## Expected file families

- `framework/event_bus.py` — `EventBus` class (≈60 lines)

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
