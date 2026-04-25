# RM-OPS-015

- **ID:** `RM-OPS-015`
- **Title:** Log aggregation and analysis (ELK/Loki)
- **Category:** `OPS`
- **Type:** `Enhancement`
- **Status:** `Accepted`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `15`
- **Target horizon:** `immediate`
- **LOE:** `M`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `1`
- **Readiness:** `now`

## Description

Implement centralized log aggregation and analysis using ELK Stack or Loki. Collect, store, and analyze logs from all services.

## Why it matters

Log aggregation enables:
- centralized access to logs
- fast troubleshooting and debugging
- performance analysis and trending
- security event detection
- compliance audit trails

## Key requirements

- log collection from all services
- log parsing and enrichment
- storage and retention management
- search and filtering
- alerting and notifications
- visualization and dashboards

## Affected systems

- observability infrastructure
- troubleshooting and debugging
- security monitoring

## Expected file families

- logging/ — log aggregation configuration
- logging/parsers/ — log parsing rules
- logging/dashboards/ — visualization definitions
- config/logging_config.yaml — logging configuration

## Dependencies

- no blocking dependencies; foundational

## Risks and issues

### Key risks
- log volume management and storage costs
- sensitive data in logs
- alerting fatigue from excessive alerts

### Known issues / blockers
- none; ready to start

## CMDB / asset linkage

- Elastic Stack, Loki, Grafana, log aggregation

## Grouping candidates

- none (foundational item)

## Grouped execution notes

- Foundational item for observability.

## Recommended first milestone

Set up log aggregation with search and basic dashboards.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: log aggregation with storage and search
- Validation / closeout condition: logs collected from 10+ services

## Notes

Essential for observability and troubleshooting.
