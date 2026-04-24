- **ID:** `RM-MON-001`
- **Title:** System health dashboard
- **Category:** `Monitoring`
- **Type:** `System`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P1`
- **Queue rank:** `1`
- **Target horizon:** `soon`
- **LOE:** `L`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `2`
- **Dependency burden:** `1`
- **Readiness:** `near`

## Description

Build a central health dashboard that displays real-time status of all system components: executor availability, item completion rate, failure frequency, resource usage, and operational health indicators.

## Why it matters

Provides operators with at-a-glance visibility into system state. Enables quick detection of failures, resource bottlenecks, or execution anomalies. Supports operational decision-making and troubleshooting.

## Key requirements

- Real-time status updates (refresh interval <30s)
- Component health indicators (executor, database, API, storage)
- Completion rate and velocity metrics
- Failure rate tracking with severity classification
- Resource utilization graphs (CPU, memory, disk)
- System uptime and reliability metrics
- Alert threshold configuration
- Web UI or terminal dashboard interface
- Historical trend visualization

## Affected systems

- Monitoring and observability
- Execution engine
- Operational control plane
- Analytics and reporting

## Expected file families

- `monitoring/dashboard.py`
- `monitoring/health_check.py`
- `config/dashboard-config.yaml`
- `static/dashboard/index.html`

## Dependencies

- RM-MON-002 (Real-time metrics)
- RM-MON-003 (Alert system)

## Risks and issues

### Key risks
- Complexity of aggregating metrics from distributed components
- Dashboard latency under high volume
- Difficulty maintaining accurate health state across async operations

### Known issues / blockers
- none; ready to start

## Recommended first milestone

Real-time executor health display with completion rate and current item status.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: Dashboard functional with basic metrics
- Validation / closeout condition: Displays executor status, completion metrics, and failure alerts
