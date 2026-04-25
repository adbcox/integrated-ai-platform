# RM-SCALE-009

- **ID:** `RM-SCALE-009`
- **Title:** Back-pressure signal for overloaded Ollama
- **Category:** `SCALE`
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

Poll Ollama `/api/ps` every 10 s; when queue depth > 3, pause new executor dispatches and post a warning to the log until queue clears, preventing timeout cascades.

## Key requirements

- `OllamaBackpressure` class with `is_overloaded()` and `wait_until_clear(timeout)` methods
- configurable queue depth threshold
- integrates with auto_execute_roadmap.py dispatch loop

## Expected file families

- `framework/backpressure.py` — `OllamaBackpressure` class (≈60 lines)

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
