# Troubleshooting: Integrated AI Platform

**Last Updated:** 2026-04-25

Quick checks first:

```bash
docker ps --format "{{.Names}}: {{.Status}}" | grep -v "Up"   # stopped containers
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/status  # dashboard
curl -s http://localhost:11434/api/tags | head -5               # ollama
make check                                                       # syntax errors
```

---

## Container Issues

### Container won't start

```bash
# See exact error
docker logs <container-name> --tail 50

# Check port conflicts
lsof -i :<port-number>

# Force recreate
docker compose -f docker/<stack>.yml up -d --force-recreate <service-name>
```

### Container keeps restarting

```bash
docker inspect <container-name> | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['State'])"
docker logs <container-name> --tail 100
```

### Plane containers: one of the worker/beat/api is unhealthy

```bash
# Check which
docker ps --filter "name=plane" --format "{{.Names}}: {{.Status}}"

# Restart just that service
docker restart docker-plane-api-1

# If database related, check db
docker exec docker-plane-db-1 psql -U plane -c "SELECT 1"

# Full plane restart
docker compose -f docker/docker-compose-plane.yml down && docker compose -f docker/docker-compose-plane.yml up -d
```

### Ran out of disk space — containers failing

```bash
df -h /
# Free space
docker system prune -f            # remove stopped containers, dangling images
docker image prune -a -f          # remove all unused images (frees most space)
```

### OpenHands runtime containers accumulating

The 9 `openhands-runtime-*` exited containers are normal — created per session and left behind. Clean up:

```bash
docker ps -a --filter "name=openhands-runtime" --filter "status=exited" -q | xargs docker rm -f
```

---

## Network Issues

### Dashboard server unreachable (port 8080)

The dashboard is NOT a Docker service. It must be started manually:

```bash
cd ~/repos/integrated-ai-platform
python3 web/dashboard/server.py &
curl http://localhost:8080/api/status
```

### Service reachable locally but not from other machines

Check that the container binds to `0.0.0.0` not just `127.0.0.1`:

```bash
docker ps --format "{{.Names}}: {{.Ports}}" | grep <service>
# 0.0.0.0:3030->3000/tcp  ← accessible from LAN
# 127.0.0.1:3030->3000/tcp ← localhost only
```

To fix, edit the ports section in the relevant compose file.

### QNAP NAS unreachable (192.168.10.201)

```bash
ping -c 3 192.168.10.201
curl -s -o /dev/null -w "%{http_code}" http://192.168.10.201:8080
```

If unreachable: the NAS may be powered off, or OPNsense DHCP lease expired. Check OPNsense at http://192.168.10.1.

### Cannot SSH to QNAP

SSH password auth is disabled by default on recent QTS. Use the QNAP web UI → Control Panel → Terminal & SNMP to enable SSH with key auth.

### Seedbox connector failures

The seedbox SFTP is at `193.163.71.22:2088`. Test:

```bash
sftp -P 2088 seedit4me@193.163.71.22
```

If it fails, check `connectors/seedbox.py` and the `SEEDBOX_*` environment variables.

### Arr stack (Sonarr/Radarr/Prowlarr) not responding

From the 2026-04-25 audit, Radarr (7878) and Prowlarr (9696) returned connection refused while only Sonarr (8989) was reachable. Check which ports are actually bound on the QNAP:

```bash
curl -s -o /dev/null -w "%{http_code}" http://192.168.10.201:8989   # Sonarr
curl -s -o /dev/null -w "%{http_code}" http://192.168.10.201:7878   # Radarr
curl -s -o /dev/null -w "%{http_code}" http://192.168.10.201:9696   # Prowlarr
```

---

## MCP Server Issues

### plane-roadmap MCP not responding

```bash
# Check server process
ps aux | grep plane_mcp_server

# Restart
python3 mcp/plane_mcp_server.py &

# Test
curl -s http://localhost:3001/api/v1/workspaces/ -H "Authorization: Bearer $PLANE_API_KEY"
```

### MCP shows stale data

The plane MCP server caches responses. Restart it to invalidate cache:

```bash
pkill -f plane_mcp_server
python3 mcp/plane_mcp_server.py &
```

### Claude Code can't connect to MCP

Check `.claude/settings.json` — MCP server definitions must point to running processes. Verify with:

```bash
cat .claude/settings.json | python3 -m json.tool | grep -A5 "mcp"
```

---

## Database Issues

### Plane database connection errors

```bash
# Test Postgres directly
docker exec docker-plane-db-1 psql -U plane -d plane -c "SELECT version();"

# Check connection from API container
docker exec docker-plane-api-1 python3 -c "import django; django.setup(); from django.db import connection; connection.ensure_connection(); print('OK')" 2>/dev/null || echo "FAIL"

# Restart db + dependent services
docker restart docker-plane-db-1
sleep 5
docker restart docker-plane-api-1 docker-plane-worker-1 docker-plane-beat-1
```

### Plane migrations needed after update

```bash
docker compose -f docker/docker-compose-plane.yml run --rm plane-migrate
```

### Database disk full

```bash
docker exec docker-plane-db-1 psql -U plane -c "SELECT pg_size_pretty(pg_database_size('plane'));"
# If large, check for bloat
docker exec docker-plane-db-1 psql -U plane -c "VACUUM ANALYZE;"
```

---

## Ollama Issues

### Ollama not responding

```bash
curl http://localhost:11434/api/tags
# If fails:
pgrep -la ollama
ollama serve &
```

### Model pull fails / slow

```bash
# Check available disk space first (models are large)
df -h ~/.ollama/

# List what's already pulled
ollama list

# Force re-pull
ollama rm qwen2.5-coder:14b && ollama pull qwen2.5-coder:14b
```

### Ollama returning truncated responses

The `qwen2.5-coder:7b` model truncates whole-file responses on files over ~40 lines under load. Workaround: target new small files (<20 lines) in decomposition, or use the 14b model.

```bash
# Check current model in use
grep "AIDER_WORKER_MODEL\|model" config/model_pairs.yaml
```

### Aider subprocess can't find Ollama

Ensure aider uses the correct `OLLAMA_API_BASE`:

```bash
export OLLAMA_API_BASE=http://127.0.0.1:11434
aider --model ollama/qwen2.5-coder:14b --version
```

### Aider not found in PATH

Aider is installed via uv at `~/.local/bin/aider`:

```bash
which aider || echo "$HOME/.local/bin/aider --version"
# Add to PATH if needed:
export PATH="$HOME/.local/bin:$PATH"
```

---

## Vault Issues

HashiCorp Vault is **not yet deployed** in this platform. Secrets are currently managed via:
- `docker/.env` — Docker service credentials
- Environment variables (`QNAP_USER`, `QNAP_PASS`, `PLANE_API_KEY`, etc.)
- `~/.aider_worker.env` — Aider worker credentials

When Vault is deployed (RM-SEC-* roadmap items), update this section.

---

## Monitoring Issues

### Grafana shows no data

```bash
# Check VictoriaMetrics is running
curl http://localhost:8428/metrics | head -5

# Check VMAgent is scraping
curl http://localhost:8429/metrics | grep "vm_rows_inserted"

# Verify datasource in Grafana
curl -s http://admin:admin@localhost:3030/api/datasources | python3 -m json.tool
```

### Uptime Kuma not detecting outages

Uptime Kuma checks from inside Docker — it can't reach `localhost` on the host. Use actual LAN IP (`192.168.10.145`) or container names in monitors.

### Zabbix not collecting host metrics

```bash
# Check agent is running
docker ps --filter "name=zabbix-agent" --format "{{.Status}}"

# Test agent from server
docker exec zabbix-server zabbix_get -s 192.168.10.145 -p 10050 -k system.uname
```

### VictoriaMetrics high disk usage

```bash
du -sh /var/lib/docker/volumes/ | head -5
# Reduce retention (default is unlimited):
# Edit observability-stack.yml → vm command → add: -retentionPeriod=30d
```

---

## Performance Issues

### Aider execution timeouts (600s kills)

This is the primary failure mode (45.6% failure rate). Root causes:

1. **Model too slow** — switch from 7b to 14b for better throughput
2. **File too large** — decompose into smaller target files (<20 lines for 7b)
3. **Task too complex** — use `make aider-hard` (deepseek-coder-v2) or increase timeout in `bin/auto_execute_roadmap.py`

```bash
# Check recent timeouts
grep "timeout\|SIGTERM\|exit -15" execution.log | tail -10
```

### Dashboard server slow / unresponsive

The dashboard server calls multiple backends synchronously. If QNAP is unreachable, requests hang. Check:

```bash
ping -c 1 -W 2 192.168.10.201 || echo "QNAP unreachable — dashboard media tabs will be slow"
```

Workaround: disable QNAP-dependent tabs or add `--skip-qnap` flag (if implemented).

### Plane API slow response

```bash
# Check if worker queue is backed up
docker exec docker-plane-redis-1 redis-cli llen celery

# Check celery worker
docker logs docker-plane-worker-1 --tail 20
```

### Mac Mini memory pressure

```bash
# Check memory usage
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}" | sort -k2 -rh | head -10
# Top consumers as of 2026-04-25 audit:
#   openhands-app:      437 MiB
#   docker-plane-worker: 418 MiB
#   docker-plane-api:   303 MiB
```

Consider stopping OpenHands when not in active use to free ~437 MiB.

---

## Security Issues

### Exposed plain-text secrets in env files

```bash
# Find any accidentally committed secrets
git log --all --full-history -- "*.env" | head -10
git show HEAD:docker/.env 2>/dev/null | grep -v "^#\|^$"
```

If secrets were committed, rotate them immediately and remove from git history with `git filter-branch` or `bfg`.

### Unexpected open port

```bash
lsof -iTCP -sTCP:LISTEN -P -n | grep -v "127.0.0.1"
```

If an unexpected port is open, identify the process and kill it or add a firewall rule in OPNsense.

### Container running as root

```bash
docker inspect <container-name> | python3 -c "import sys,json; d=json.load(sys.stdin); print('User:', d[0]['Config']['User'] or 'root')"
```

### Config file conflict (arr_stack enabled)

`config/system_truth.yaml` sets `arr_stack: enabled: false` but `config/connectors.yaml` sets `enabled: true`. The connector code reads `connectors.yaml`. Resolve by making them consistent:

```bash
grep -n "arr_stack" config/system_truth.yaml config/connectors.yaml
```

---

## Recovery Procedures

### Full platform restart

```bash
cd ~/repos/integrated-ai-platform

# Stop everything
docker compose -f docker/docker-compose-plane.yml down
docker compose -f docker/observability-stack.yml down
docker compose -f docker/zabbix-stack.yml down
pkill -f "web/dashboard/server.py" 2>/dev/null

# Wait for clean shutdown
sleep 5

# Start everything
docker compose -f docker/docker-compose-plane.yml up -d
docker compose -f docker/observability-stack.yml up -d
docker compose -f docker/zabbix-stack.yml up -d
python3 web/dashboard/server.py &

echo "Done. Check: docker ps"
```

### Restore Plane from backup

Plane data is in Docker volumes (`docker-plane-db-1`, `docker-plane-minio-1`). To restore:

```bash
# Stop Plane
docker compose -f docker/docker-compose-plane.yml down

# Restore Postgres volume from dump
docker run --rm -v docker_plane-db-data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/plane-db-backup.tar.gz -C /data

# Restart
docker compose -f docker/docker-compose-plane.yml up -d
```

### Rollback a bad code change

```bash
git log --oneline | head -10   # find the bad commit
git revert <commit-hash>        # create a revert commit
make check                      # verify syntax
```

### Executor left a half-applied change

If `auto_execute_roadmap.py` crashed mid-run:

```bash
git status                      # see what's modified
git diff                        # review changes
git checkout -- .               # discard all uncommitted changes (safe after review)
```

### Roadmap item stuck in "In Progress"

```bash
# List in-progress items
python3 -c "
from bin.roadmap_parser import parse_roadmap_directory
from pathlib import Path
items = parse_roadmap_directory(Path('docs/roadmap/ITEMS'))
for i in items:
    if i.status == 'In Progress':
        print(i.id, i.title)
"

# Manually reset to Accepted
# Edit docs/roadmap/ITEMS/RM-XXX-YYY.md → change Status: to Accepted
```
