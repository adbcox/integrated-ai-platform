# Quick Reference — Service Access

**Mac Mini M5 · 192.168.10.145**

## Primary Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| Open WebUI | http://192.168.10.145:3002 | Local account (create on first login) |
| Homarr | http://192.168.10.145:7575 | No auth (LAN only) |
| Home Assistant | http://192.168.10.145:8123 | Local account (create on first login) |
| Plane CE | http://192.168.10.145:3001 | Workspace credentials |
| Grafana | http://192.168.10.145:3030 | admin / admin |
| Uptime Kuma | http://192.168.10.145:3033 | Local account |

## Gateways (API Access)

| Service | URL | Auth |
|---------|-----|------|
| LiteLLM | http://192.168.10.145:4000 | Bearer `$LITELLM_MASTER_KEY` |
| MCPO (OpenAPI) | http://192.168.10.145:8081 | None |
| Vault | http://192.168.10.145:8200 | Root token in `vault/.env` |
| Obot | http://192.168.10.145:8090 | Browser OAuth (setup pending) |
| Ollama | http://192.168.10.145:11434 | None |
| Plane API | http://192.168.10.145:8000 | `x-api-key: $PLANE_API_TOKEN` |

## Ollama Models

| Model | Size | Use Case |
|-------|------|---------|
| qwen2.5-coder:32b | 32B | Best quality code generation |
| qwen2.5-coder:14b | 14B | Balanced speed/quality |
| qwen2.5-coder:7b | 7B | Fast iteration |
| devstral:latest | — | Agentic coding tasks |
| deepseek-coder-v2:latest | — | Complex reasoning |

## Compose Stack Locations

| Stack | Directory | Start Command |
|-------|-----------|---------------|
| Plane CE | `~/repos/integrated-ai-platform/docker/` | `docker compose -f docker-compose-plane.yml up -d` |
| Obot | `~/repos/integrated-ai-platform/docker/` | `docker compose -f obot-stack.yml up -d` |
| Observability | `~/repos/integrated-ai-platform/docker/` | `docker compose -f observability-stack.yml up -d` |
| Gateways | `~/control-center-stack/stacks/gateways/` | `docker compose up -d` |
| AI UI | `~/control-center-stack/stacks/ai-control/` | `docker compose up -d` |
| Vault | `~/control-center-stack/stacks/vault/` | `docker compose up -d` |
| Dashboards | `~/control-center-stack/stacks/dashboards/` | `docker compose up -d` |

## Quick Health Check

```bash
bash ~/phase3-final-validation.sh
```

## Vault Unseal (after restart)

```bash
KEYS=$(grep "Unseal Key" ~/vault-init-keys.txt | head -3 | awk '{print $NF}')
for KEY in $KEYS; do
  docker exec vault-server vault operator unseal -address=http://localhost:8200 "$KEY"
done
```

## Full-Stack Restart Order

```bash
# 1. Database layer
cd ~/repos/integrated-ai-platform/docker
docker compose -f docker-compose-plane.yml up -d plane-db plane-redis

# 2. Application layer
docker compose -f docker-compose-plane.yml up -d
docker compose -f obot-stack.yml up -d

# 3. Gateway layer
cd ~/control-center-stack/stacks/vault  && docker compose up -d
# Unseal vault (see above)
cd ~/control-center-stack/stacks/gateways && docker compose up -d

# 4. UI layer
cd ~/control-center-stack/stacks/ai-control && docker compose up -d
cd ~/control-center-stack/stacks/dashboards && docker compose up -d

# 5. Observability
cd ~/repos/integrated-ai-platform/docker
docker compose -f observability-stack.yml up -d
```
