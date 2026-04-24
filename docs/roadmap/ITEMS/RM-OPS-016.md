# RM-OPS-016

- **ID:** `RM-OPS-016`
- **Title:** Distributed tracing (OpenTelemetry)
- **Category:** `OPS`
- **Type:** `Enhancement`
- **Status:** `Accepted`
- **Maturity:** `M0`
- **Priority:** `Medium`
- **Priority class:** `P2`
- **Queue rank:** `16`
- **Target horizon:** `near-term`
- **LOE:** `M`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `near`

## Description

Implement distributed tracing using OpenTelemetry. Track requests across services to understand latency and dependencies.

## Why it matters

Distributed tracing enables:
- visualization of request paths
- latency analysis and optimization
- service dependency mapping
- bottleneck identification
- improved debugging experience

## Key requirements

- OpenTelemetry SDK integration
- trace collection and storage
- span context propagation
- service dependency visualization
- latency analysis
- alerting on trace patterns

## Affected systems

- observability infrastructure
- performance optimization
- debugging and troubleshooting

## Expected file families

- framework/tracing.py — tracing integration
- config/tracing_config.yaml — tracing configuration
- dashboards/tracing/ — tracing dashboards
- tests/observability/test_tracing.py — tracing tests

## Dependencies

- `RM-OPS-015` — log aggregation (for complementary observability)

## Risks and issues

### Key risks
- trace volume and storage costs
- overhead of instrumentation
- sampling strategy complexity

### Known issues / blockers
- none; ready to start

## CMDB / asset linkage

- OpenTelemetry, Jaeger, Zipkin, tracing systems

## Grouping candidates

- none (depends on `RM-OPS-015`)

## Grouped execution notes

- Blocked by `RM-OPS-015`. Complements log aggregation.

## Recommended first milestone

Implement OpenTelemetry integration with Jaeger backend.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: distributed tracing with span visualization
- Validation / closeout condition: traces collected for 50+ request types

## Notes

Enhances observability for microservices.
