# RM-PERF-005

- **ID:** `RM-PERF-005`
- **Title:** Cache key normalizer for BM25 retrieval
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

Normalize query strings before BM25 lookup to improve cache hit rate across near-duplicate queries (lower-case, strip punctuation, collapse whitespace).

## Key requirements

- deterministic normalizer callable
- cache hit rate logged
- unit tests covering edge cases

## Expected file families

- `framework/cache_normalizer.py` — `normalize_query(q: str) -> str` (≈40 lines)

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
