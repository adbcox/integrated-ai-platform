# RM-PERF-003

- **ID:** `RM-PERF-003`
- **Title:** Response cache layer for repeated queries
- **Category:** `PERF`
- **Type:** `Enhancement`
- **Status:** `Accepted`
- **Maturity:** `M0`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `3`
- **Target horizon:** `near-term`
- **LOE:** `M`
- **Strategic value:** `3`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `ready`

## Description

Implement a caching layer for stage pipeline responses to avoid recomputing identical queries. Support both in-memory and persistent cache with configurable TTL and eviction policies.

## Why it matters

Query caching eliminates redundant computation:
- repeated queries within sessions use cached results
- identical tasks across different runs share results
- inference costs are reduced
- system responsiveness improves for interactive use

## Key requirements

- query fingerprinting for cache key generation
- in-memory cache with configurable size limits
- persistent cache backend (file or redis)
- TTL and staleness policies
- cache statistics and hit/miss tracking
- cache invalidation strategies

## Affected systems

- stage_rag pipeline (retrieval and ranking)
- stage managers (plan generation)
- inference integration (query results)

## Expected file families

- framework/caching.py — cache implementation
- config/cache_config.yaml — cache policies and tuning
- tests/caching/ — cache functionality tests

## Dependencies

- `RM-PERF-002` — optimization targets should identify caching as priority first

## Risks and issues

### Key risks
- cache invalidation issues (stale results)
- cache key collisions causing wrong results
- memory overhead from cache storage
- complexity in cache maintenance

### Known issues / blockers
- none; ready to start

## CMDB / asset linkage

- caching libraries (redis, diskcache), memcached

## Grouping candidates

- none (depends on `RM-PERF-002`)

## Grouped execution notes

- Blocked by `RM-PERF-002`. Can be executed after optimization targets identified.

## Recommended first milestone

Implement in-memory query cache with TTL and basic statistics.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: in-memory cache with fingerprinting and TTL
- Validation / closeout condition: 20%+ hit rate improvement on test scenarios

## Notes

High ROI optimization candidate.
