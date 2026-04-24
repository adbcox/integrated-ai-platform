- **ID:** `RM-MON-008`
- **Title:** Custom metric collectors
- **Category:** `Monitoring`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `8`
- **Target horizon:** `soon`
- **LOE:** `M`
- **Strategic value:** `3`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `1`
- **Readiness:** `near`

## Description

Build extensible framework for custom metric collectors. Enable domain-specific metrics (item completion rate, subtask success rate, model usage, etc.) without core changes.

## Why it matters

Allows operators to track application-specific metrics relevant to their domain. Provides flexibility for future monitoring needs without core modifications.

## Key requirements

- Plugin architecture for custom collectors
- Metric registration and discovery
- Collector lifecycle management (start, stop, pause)
- Metric aggregation and storage
- Built-in collectors for key metrics (completion rate, success rate, model usage)
- Collector configuration (sampling rate, filters)
- Performance efficient (low overhead)

## Affected systems

- Monitoring and metrics
- Extensibility framework
- Analytics

## Expected file families

- `monitoring/collector_framework.py`
- `monitoring/builtin_collectors.py`

## Dependencies

- RM-MON-002 (Metrics visualization)

## Risks and issues

### Key risks
- Poorly written custom collectors can impact system performance
- Complexity of collector plugin architecture

### Known issues / blockers
- none; ready to start

## Recommended first milestone

Basic collector plugin framework with item completion rate collector.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: Collector framework accepting custom collectors
- Validation / closeout condition: Custom collectors running and metrics collected
