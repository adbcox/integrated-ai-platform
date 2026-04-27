# ADR-A-003 — Monitoring stack: Zabbix + TimescaleDB + Grafana + VictoriaMetrics
**Status:** Accepted
**Date:** 2026-04-27
**Source:** Phase 7 observability work and Phase 12 Zabbix deployment

## Context

The platform spans physical hardware (Mac Mini, QNAP NAS, OPNsense firewall) and 55+ Docker containers. A monitoring solution needed to cover: agent-based host metrics, SNMP for network gear, container health, long-term metric retention, and dashboarding. Options evaluated: Prometheus + node-exporter only, Zabbix alone, Datadog (cloud), and the hybrid stack adopted.

## Decision

Run a layered monitoring stack:
- **Zabbix 7.4 + TimescaleDB:** Primary host and network monitor — native agent on Mac Mini, SNMP v2c for OPNsense and QNAP. TimescaleDB provides compressed long-term storage for Zabbix history/trend hypertables.
- **VictoriaMetrics + vmagent:** Container and application metrics scraped from Prometheus exporters (node-exporter, service /metrics endpoints). Chosen over plain Prometheus for lower memory footprint and built-in retention.
- **Grafana:** Unified dashboarding layer — Zabbix plugin (alexanderzobnin-zabbix-app 4.4.5) plus VictoriaMetrics datasource.
- **Uptime Kuma:** External HTTP health check layer for user-facing service availability.

## Consequences

- Named Docker volume (`zabbix-pgdata`) required for Zabbix PostgreSQL — macOS Colima virtiofs maps host UIDs; PostgreSQL uid 70 cannot write to macOS-owned bind-mounts
- Conservative PostgreSQL memory (256 MB shared_buffers) required by 8 GB Colima VM running 30+ containers; increase requires `colima stop && colima start --memory 16`
- TimescaleDB compression policies use integer seconds (not INTERVAL) because Zabbix `clock` column is a Unix timestamp integer
- QNAP "Linux by SNMP" template has many unsupported OIDs (QNAP uses custom MIB); consider switching to "Network Generic Device by SNMP" for broader compatibility
- Zabbix API PSK bug in 7.4: `host.create/update` with `tls_connect=4` + `tls_psk_identity` throws "value must be empty"; workaround is direct DB UPDATE via psql
- macOS ARM64 only has `zabbix_agent` (agentd, agent1) package — `zabbix_agent2` package does not exist for ARM64
