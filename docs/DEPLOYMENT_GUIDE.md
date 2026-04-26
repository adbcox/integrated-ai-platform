# Deployment Guide: Integrated AI Platform

**Last Updated:** 2026-04-25  
**Host:** Mac Mini M5 — 192.168.10.113

---

## Starting Services

### All Docker stacks

```bash
cd ~/repos/integrated-ai-platform

# Plane CE (project management)
docker compose -f docker/docker-compose-plane.yml up -d

# Observability (Grafana, VictoriaMetrics, VMAgent, Uptime Kuma, node-exporter)
docker compose -f docker/observability-stack.yml up -d

# Zabbix (infrastructure monitoring)
docker compose -f docker/zabbix-stack.yml up -d
```

### Dashboard server (must be started manually — not in Docker)

```bash
cd ~/repos/integrated-ai-platform
python3 web/dashboard/server.py &
# Runs on http://localhost:8080
```

To keep it running across sessions:

```bash
# In tmux
tmux new-session -d -s dashboard 'cd ~/repos/integrated-ai-platform && python3 web/dashboard/server.py'
```

### Ollama (local inference)

```bash
# Should auto-start via LaunchAgent; if not:
ollama serve &

# Verify
curl http://localhost:11434/api/tags
```

### Autonomous executor

```bash
cd ~/repos/integrated-ai-platform

# Dry-run (no commits)
python3 bin/auto_execute_roadmap.py --target-completions 1 --dry-run

# Real run (commits to git)
python3 bin/auto_execute_roadmap.py --target-completions 5

# In background via tmux
tmux new-session -d -s roadmap 'cd ~/repos/integrated-ai-platform && python3 bin/auto_execute_roadmap.py --resume --target-completions 50'
tmux attach -t roadmap
```

---

## Stopping Services

### Docker stacks

```bash
docker compose -f docker/docker-compose-plane.yml down
docker compose -f docker/observability-stack.yml down
docker compose -f docker/zabbix-stack.yml down
```

### Dashboard server

```bash
pkill -f "web/dashboard/server.py"
```

### Autonomous executor

```bash
tmux kill-session -t roadmap
# Or Ctrl+C if in the foreground
```

---

## Accessing UIs

| Service | URL | Notes |
|---------|-----|-------|
| AI Dashboard | http://localhost:8080 | Must be started manually (see above) |
| Plane (project mgmt) | http://localhost:3001 | Login: see `docker/.env` |
| OpenHands | http://localhost:3000 | AI coding agent |
| Grafana | http://localhost:3030 | Default login: admin/admin |
| Uptime Kuma | http://localhost:3033 | First-run creates admin account |
| Zabbix | http://localhost:10080 | Default: Admin/zabbix |
| VictoriaMetrics | http://localhost:8428 | No auth — metrics query UI |
| Plane MinIO | http://localhost:9001 | Object storage console |
| QNAP NAS | http://192.168.10.201:8080 | Requires QNAP credentials |

---

## Common Operations

### Check all container health

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Restart a single container

```bash
docker restart docker-plane-api-1
docker restart grafana-obs
```

### View container logs

```bash
docker logs -f docker-plane-api-1 --tail 50
docker logs -f grafana-obs --tail 50
```

### Pull latest images and redeploy

```bash
docker compose -f docker/docker-compose-plane.yml pull && docker compose -f docker/docker-compose-plane.yml up -d
```

### Check Ollama model status

```bash
ollama list
curl -s http://localhost:11434/api/tags | python3 -m json.tool
```

### Pull a new Ollama model

```bash
ollama pull qwen2.5-coder:14b
ollama pull devstral:latest
```

### Run platform validation

```bash
cd ~/repos/integrated-ai-platform
make check        # Full syntax check (shell + Python)
make quick        # Fast check on changed files
make test-offline # 7 deterministic offline scenarios
```

### Check roadmap progress

```bash
cd ~/repos/integrated-ai-platform
python3 -c "
from bin.roadmap_parser import parse_roadmap_directory
from pathlib import Path
from collections import defaultdict
items = parse_roadmap_directory(Path('docs/roadmap/ITEMS'))
by_status = defaultdict(int)
for i in items: by_status[i.status] += 1
for s, n in sorted(by_status.items()): print(f'{s}: {n}')
print(f'Total: {len(items)}')
"
```

### Sync roadmap to Plane

```bash
python3 bin/sync_roadmap_to_plane.py
```

---

## Security Operations

### Rotate Plane secret key

1. Edit `docker/.env` — update `SECRET_KEY`
2. `docker compose -f docker/docker-compose-plane.yml down && docker compose -f docker/docker-compose-plane.yml up -d`

### View open ports

```bash
ss -tlnp | grep LISTEN
# Or
lsof -iTCP -sTCP:LISTEN -P -n
```

### Check which containers have external bindings

```bash
docker ps --format "{{.Names}}: {{.Ports}}" | grep -v "^$"
```

### Rotate Zabbix admin password

Access http://localhost:10080 → Administration → Users → Admin → Change password.

### Check for exposed credentials in env files

```bash
grep -r "PASSWORD\|SECRET\|KEY\|TOKEN" docker/.env docker/.env.* 2>/dev/null | grep -v ".example\|.bak"
```

---

## Monitoring

### Key dashboards

| Dashboard | URL | Shows |
|-----------|-----|-------|
| Grafana overview | http://localhost:3030 | System metrics, aider performance |
| Uptime Kuma | http://localhost:3033 | Service uptime history |
| Zabbix | http://localhost:10080 | Infrastructure alerts |
| VictoriaMetrics | http://localhost:8428/vmui | Raw metric queries |

### Check live metrics

```bash
# Node metrics (CPU, RAM, disk)
curl -s http://localhost:8428/api/v1/query?query=node_cpu_seconds_total | python3 -m json.tool | head -20

# ISP connectivity log (actively written by background monitor)
tail -20 artifacts/isp_monitor.jsonl | python3 -m json.tool

# Self-heal log
tail -20 artifacts/selfheal.jsonl | python3 -m json.tool
```

### Execution metrics

```bash
# Recent run outcomes
tail -5 artifacts/execution_metrics.jsonl | python3 -m json.tool

# Recent failures
tail -10 artifacts/execution_failures.jsonl | python3 -m json.tool

# Aider benchmark summary
make aider-bench-report
```

---

## Troubleshooting Quick Checks

```bash
# Is dashboard server running?
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/status

# Is Plane up?
curl -s -o /dev/null -w "%{http_code}" http://localhost:3001

# Is Ollama reachable?
curl -s http://localhost:11434/api/tags | python3 -m json.tool | head -5

# Any stopped containers?
docker ps -a --filter "status=exited" --filter "status=created" --format "{{.Names}}: {{.Status}}"

# Disk space
df -h / /System/Volumes/Data 2>/dev/null || df -h /

# Recent git activity
git log --oneline | head -10
```

Full troubleshooting: see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## File Locations

| What | Path |
|------|------|
| Repo root | `~/repos/integrated-ai-platform/` |
| Docker compose files | `docker/docker-compose-plane.yml`, `docker/observability-stack.yml`, `docker/zabbix-stack.yml` |
| Docker env (credentials) | `docker/.env` |
| Dashboard server | `web/dashboard/server.py` |
| Ollama models | `~/.ollama/models/` |
| Execution log | `execution.log` |
| Execution artifacts | `artifacts/` (executions/, stage_rag4/, failures) |
| Roadmap items | `docs/roadmap/ITEMS/` (601 `.md` files) |
| Config per-node | `config/mac_mini/`, `config/mac_studio/`, `config/qnap/` |
| Aider worker env | `~/.aider_worker.env` |
| MCP server | `mcp/plane_mcp_server.py` |
| Self-heal script | `bin/selfheal.py` |
| ISP monitor output | `artifacts/isp_monitor.jsonl` |

---

## Mac Studio Deployment (When Ready)

The Mac Studio M3 (192.168.10.202) bootstrap script is at `config/mac_studio/bootstrap.sh`. Run it once after first login:

```bash
scp config/mac_studio/bootstrap.sh admin@192.168.10.202:~/
ssh admin@192.168.10.202 'bash ~/bootstrap.sh'
```

This installs Homebrew, Ollama, aider, clones the repo, and configures the LaunchAgent for Ollama.
