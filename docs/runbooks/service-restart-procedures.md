# Service Restart Procedures

## Quick Reference

| Service | Stack | Restart Command | Health Check |
|---------|-------|-----------------|--------------|
| Plane CE | `docker/docker-compose-plane.yml` | `docker compose up -d` | curl :8000 |
| Obot | `docker/obot-stack.yml` | `docker compose up -d` | curl :8090/api/healthz |
| LiteLLM | `control-center-stack/stacks/gateways/` | `docker compose restart litellm` | curl :4000/health |
| MCPO | `control-center-stack/stacks/gateways/` | `docker compose restart mcpo` | curl :8081/openapi.json |
| Open WebUI | `control-center-stack/stacks/ai-control/` | `docker compose restart open-webui` | curl :3002/health |
| Homarr | `control-center-stack/stacks/ai-control/` | `docker compose restart homarr` | curl :7575 |
| Vault | `control-center-stack/stacks/vault/` | `docker compose restart vault` | curl :8200/v1/sys/health |
| Grafana | `docker/observability-stack.yml` | `docker compose restart grafana-obs` | curl :3030 |
| Uptime Kuma | `docker/observability-stack.yml` | `docker compose restart uptime-kuma` | curl :3033 |

## Restart Order (for full-stack restart)

Always restart in dependency order to avoid cascading failures:

```bash
cd /Users/admin/repos/integrated-ai-platform/docker

# 1. Database layer
docker compose -f docker-compose-plane.yml up -d plane-db plane-redis
sleep 10

# 2. Application layer
docker compose -f docker-compose-plane.yml up -d
sleep 10

# 3. Gateway layer
docker compose -f obot-stack.yml up -d

# 4. Observability layer
docker compose -f observability-stack.yml up -d

# 5. Control center
cd ~/control-center-stack/stacks/vault && docker compose up -d
cd ~/control-center-stack/stacks/gateways && docker compose up -d
cd ~/control-center-stack/stacks/ai-control && docker compose up -d
```

## Service-Specific Procedures

### LiteLLM Gateway (port 4000)

```bash
cd ~/control-center-stack/stacks/gateways
docker compose restart litellm
sleep 10

# Verify with auth
LITELLM_KEY=$(grep LITELLM_MASTER_KEY .env | cut -d= -f2-)
curl -s http://localhost:4000/v1/models -H "Authorization: Bearer $LITELLM_KEY" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d[\"data\"])} models loaded')"
# Expected: 8 models loaded
```

### Open WebUI (port 3002)

```bash
cd ~/control-center-stack/stacks/ai-control
docker compose restart open-webui
until curl -sf http://localhost:3002/health > /dev/null 2>&1; do sleep 3; done
echo "Open WebUI ready"
```

### Obot Gateway (port 8090)

```bash
cd /Users/admin/repos/integrated-ai-platform/docker
docker compose -f obot-stack.yml restart
until curl -sf http://localhost:8090/api/healthz > /dev/null 2>&1; do sleep 5; done
echo "Obot ready"
```

### Vault (port 8200)

Note: Dev mode Vault does NOT persist across restarts (all secrets lost on container restart).
In dev mode, secrets need to be re-written after each restart.

```bash
cd ~/control-center-stack/stacks/vault
docker compose restart vault
sleep 5
# Re-initialize secrets after restart (dev mode only)
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=$(grep VAULT_ROOT_TOKEN .env | cut -d= -f2-)
vault secrets enable -path=secret kv-v2 2>/dev/null || true
# Re-run: docs/security/baseline-configuration.md vault migration commands
```

**To prevent data loss, migrate Vault to persistent storage mode:**
See `docs/security/baseline-configuration.md` → Vault Secret Migration.

### Dashboard Server (port 8080)

The IAP dashboard runs as a host process, not Docker:

```bash
# Find the process
ps aux | grep "server.py" | grep -v grep

# Kill and restart
pkill -f "web/dashboard/server.py"
nohup python3 /Users/admin/repos/integrated-ai-platform/web/dashboard/server.py \
  > /tmp/dashboard.log 2>&1 &
sleep 3
curl -sf http://localhost:8080/ && echo "Dashboard restarted"
```
