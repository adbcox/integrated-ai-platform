# Stack Rationalization — 2026-04-25

## Decision: Single Monitoring Stack

Removed **Zabbix** (4 containers). Keeping **Grafana + VictoriaMetrics + Uptime-Kuma** (5 containers).

### Rationale

| Concern | Zabbix | Grafana+VM+Kuma |
|---------|--------|-----------------|
| AI platform app metrics | No (enterprise SNMP focus) | Yes (PromQL, push-metrics) |
| Network/SNMP devices | Yes | Limited |
| Dashboard provisioning in repo | No | Yes (grafana-provisioning/) |
| RAM footprint (Mac Mini) | High (Java + PG) | Low (VM single binary + Go) |
| Alignment with roadmap tooling | None | Direct (aider bench → VM push) |

For an AI coding platform running on Mac hardware — not a datacenter NOC — the lightweight observability stack wins. Zabbix would add value if OPNsense SNMP integration became a priority; revert then.

## Final Container Roster (13 total)

### Core Orchestration — Plane CE (7)
| Container | Purpose |
|-----------|---------|
| docker-plane-web-1 | Frontend UI (localhost:3001) |
| docker-plane-api-1 | REST API (localhost:8000) |
| docker-plane-beat-1 | Celery beat scheduler |
| docker-plane-worker-1 | Celery task worker |
| docker-plane-db-1 | Postgres for Plane |
| docker-plane-redis-1 | Redis cache/queue |
| docker-plane-minio-1 | Object storage for attachments |

### Observability (5)
| Container | Purpose | Port |
|-----------|---------|------|
| vm | VictoriaMetrics time-series DB | 8428 |
| vmagent | Metrics scraper → VM | 8429 |
| grafana-obs | Dashboards | 3030 |
| uptime-kuma | Service uptime monitor | 3033 |
| node-exporter | Host system metrics | host |

### AI Runtime (1)
| Container | Purpose | Port |
|-----------|---------|------|
| openhands-app | OpenHands AI agent UI | 3000 |

## What Was Removed

| Removed | Count | Reason |
|---------|-------|--------|
| openhands-runtime-* (exited) | 10 | Failed/stale runtime containers, 2 days old |
| docker-plane-migrate-1 | 1 | One-time DB migration (Exited 0, done) |
| docker-plane-minio-setup-1 | 1 | One-time bucket setup (Exited 0, done) |
| sweet_gould (hello-world) | 1 | Test container, unused |
| zabbix-web/server/db/agent | 4 | Replaced by Grafana+VM stack |

**Disk reclaimed: ~23GB** (images + containers + build cache)

## Alignment with Roadmap Goals

The trimmed stack focuses all resources on:
1. **Plane CE** — roadmap source of truth, issue tracking, sprint management
2. **Grafana/VM** — pipeline benchmarks, aider execution metrics, system health
3. **OpenHands** — AI agent execution baseline (compare against local aider)

No infrastructure monitoring overhead distracting from the Codex 5.1 replacement goal.
