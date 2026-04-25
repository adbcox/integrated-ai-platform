# RM-PERF-007

- **ID:** `RM-PERF-007`
- **Title:** Streaming response chunker for Ollama inference
- **Category:** `PERF`
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

Read Ollama `/api/generate` NDJSON stream line-by-line instead of buffering the full response, reducing first-token latency and peak memory use.

## Key requirements

- generator that yields token strings as they arrive
- fallback to buffered read when streaming not supported
- integrated into inference_adapter.py

## Expected file families

- `framework/streaming_adapter.py` — `stream_generate(prompt, model) -> Iterator[str]` (≈60 lines)

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
