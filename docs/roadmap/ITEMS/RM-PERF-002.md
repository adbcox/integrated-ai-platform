# RM-PERF-002

- **ID:** `RM-PERF-002`
- **Title:** Optimization targets and prioritization framework
- **Category:** `PERF`
- **Type:** `Enhancement`
- **Status:** `Accepted`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `2`
- **Target horizon:** `immediate`
- **LOE:** `M`
- **Strategic value:** `4`
- **Architecture fit:** `3`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `ready`

## Description

Use profiling data to identify and prioritize optimization targets. Build a framework for evaluating optimization options, estimating impact, and tracking results.

## Why it matters

Optimization is high-impact but easy to misdirect. A prioritization framework enables:
- ROI-based optimization decisions
- resource allocation transparency
- progress tracking across optimization initiatives
- prevention of premature optimization on low-impact targets

## Key requirements

- identification of top bottlenecks from profiling data
- impact estimation framework
- effort estimation for optimization candidates
- ROI scoring (impact/effort)
- tracking of attempted and completed optimizations

## Affected systems

- stage pipeline performance
- inference integration latency
- artifact generation speed
- memory efficiency

## Expected file families

- docs/optimization_targets.md — identified bottlenecks and prioritization
- config/optimization_roadmap.yaml — optimization tracking
- tests/optimization/ — optimization regression tests

## Dependencies

- `RM-PERF-001` — profiling data required for targeting

## Risks and issues

### Key risks
- optimization attempts introducing regressions or bugs
- over-optimizing low-impact targets
- micro-optimizations with diminishing returns

### Known issues / blockers
- none; ready to start after `RM-PERF-001`

## CMDB / asset linkage

- performance profiling, optimization tracking systems

## Grouping candidates

- none (depends on `RM-PERF-001`)

## Grouped execution notes

- Blocked by `RM-PERF-001`. Can be executed after profiling data available.

## Recommended first milestone

Identify top 3 bottlenecks and develop optimization proposals for each.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: prioritized optimization target list with impact/effort estimates
- Validation / closeout condition: 5+ optimization targets implemented with measured impact

## Notes

Blocked by `RM-PERF-001`. Enables strategic optimization investments.
