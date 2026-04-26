# Integrated AI Platform

Local-first AI operating system and control plane running on Mac Mini M5 (192.168.10.113).

## Core Documentation

| Document | Purpose |
|----------|---------|
| [docs/PLATFORM_OVERVIEW.md](docs/PLATFORM_OVERVIEW.md) | Hardware, services, what's running |
| [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | Start/stop services, access UIs, operations |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Diagnose and fix problems |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the system works |
| [docs/HANDOFF_GUIDE.md](docs/HANDOFF_GUIDE.md) | Resume development, check progress |

## Quick Start

```bash
# 1. Start Docker stacks
docker compose -f docker/docker-compose-plane.yml up -d
docker compose -f docker/observability-stack.yml up -d
docker compose -f docker/zabbix-stack.yml up -d

# 2. Start dashboard (not in Docker)
python3 web/dashboard/server.py &

# 3. Verify Ollama (local inference)
curl http://localhost:11434/api/tags

# 4. Run validation
make check && make test-offline
```

## Key Services

| Service | URL |
|---------|-----|
| AI Dashboard | http://localhost:8080 |
| Plane (roadmap) | http://localhost:3001 |
| Grafana | http://localhost:3030 |
| Ollama | http://localhost:11434 |

## Roadmap

601 items in `docs/roadmap/ITEMS/`. 65 complete (10.8%).

```bash
python3 bin/auto_execute_roadmap.py --target-completions 5
```
