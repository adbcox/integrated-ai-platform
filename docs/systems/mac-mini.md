# Mac Mini — Orchestration Hub

## Hardware

| Spec | Value |
|------|-------|
| Model | Mac mini (2024, Mac16,11) |
| Model # | G1JV1LL/A |
| Chip | Apple M5 |
| CPU | 12 cores (8 Performance + 4 Efficiency) |
| RAM | 48 GB unified memory |
| OS | macOS 26.3 (Sequoia) build 25D125 |
| Hostname | mac-mini.local |
| IP | 192.168.10.145 |
| Role | **Primary orchestration hub** |

## Purpose

The Mac Mini is the always-on orchestration node. It runs the full platform
stack: Plane CE, observability, the AI dashboard, and all automation services.
GPU-intensive workloads (LoRA training, large Ollama models) are delegated to
the Mac Studio (192.168.10.202, pending arrival).

## Running Services

### Docker Containers

| Container | Port(s) | Purpose |
|-----------|---------|---------|
| docker-plane-web-1 | 3001 | Plane CE frontend |
| docker-plane-api-1 | 8000 | Plane REST API |
| docker-plane-beat-1 | — | Plane Celery beat |
| docker-plane-worker-1 | — | Plane Celery worker |
| docker-plane-db-1 | 5432 (internal) | Plane PostgreSQL |
| docker-plane-redis-1 | 6379 (internal) | Plane Redis |
| docker-plane-minio-1 | 9000, 9001 | Plane MinIO storage |
| grafana-obs | 3030 | Grafana dashboards |
| vm | 8428 | VictoriaMetrics TSDB |
| vmagent | 8429 | Metrics scraper |
| uptime-kuma | 3033 | Service uptime monitor |
| node-exporter | — | Host system metrics |
| openhands-app | 3000 | OpenHands AI agent |
| obot | 8090 | Obot MCP gateway |

### Host Processes

| Process | Port | Purpose |
|---------|------|---------|
| web/dashboard/server.py | 8080 | IAP execution dashboard |
| bin/selfheal.py | — | Self-healing daemon (5min interval) |

## Port Map

```
3000  OpenHands
3001  Plane CE
3030  Grafana
3033  Uptime Kuma
8000  Plane API
8080  IAP Dashboard  (host Python process)
8090  Obot Gateway   (Docker)
8428  VictoriaMetrics
8429  VMAgent
9000  MinIO API
9001  MinIO UI
```

## Resource Budget

At current load (all containers running):

| Component | RAM |
|-----------|-----|
| Plane (7 containers) | ~1,033 MB |
| Observability (5 containers) | ~231 MB |
| OpenHands | ~438 MB |
| Obot | ~200 MB (est.) |
| Dashboard + selfheal (host) | ~150 MB |
| **Total Docker** | **~2,050 MB** |
| **Available headroom** | **~45 GB** |

## MCP Architecture on this Machine

```
Claude Code (claude CLI)
    │
    ├─── plane-roadmap MCP (stdio) → mcp/plane_mcp_server.py → Plane API :8000
    │
    └─── obot-gateway MCP (http) → localhost:8090 → Obot
              │
              ├── filesystem-mcp → /workspace (read-only mount)
              ├── postgresql-mcp → plane-db:5432
              ├── plane-roadmap-mcp → plane-api:8000
              ├── docker-mcp → /var/run/docker.sock
              └── github-mcp → api.github.com (needs GITHUB_TOKEN)
```

## Credentials (stored in docker/.env)

| Variable | Value | Notes |
|----------|-------|-------|
| PLANE_API_TOKEN | plane_api_f6c2c3cc... | Active — used by MCP |
| PLANE_URL | http://localhost:8000 | Internal |
| PLANE_WORKSPACE | iap | |
| PLANE_PROJECT_ID | dbcd4476-... | |
| GITHUB_TOKEN | **NOT SET** | Required for GitHub MCP |
| OBOT_ADMIN_PASSWORD | changeme_before_prod | **Change before production** |

## Key Directories

```
~/repos/integrated-ai-platform/   ← Primary repo (this machine)
  bin/                            ← Executable scripts
  framework/                      ← Core Python runtime
  docker/                         ← Docker Compose files
    obot-stack.yml                ← Obot gateway
    docker-compose-plane.yml      ← Plane CE
    observability-stack.yml       ← Grafana + VM
    zabbix-stack.yml              ← Zabbix (stopped, use if SNMP needed)
  config/obot/                    ← Obot tool & RBAC config
  docs/systems/                   ← This directory
  mcp/plane_mcp_server.py         ← Plane MCP server
artifacts/                        ← Stage RAG + manager run outputs
~/training-env/                   ← Python 3.12 + torch (LoRA training)
```

## Backup Notes

Critical data to back up to QNAP (192.168.10.201):
- `docker-plane-db-1` postgres data (Plane issues + configuration)
- `obot-data` volume (Obot agents + audit logs)
- `docker/.env` (credentials)
- `~/.claude.json` (MCP server registrations)
