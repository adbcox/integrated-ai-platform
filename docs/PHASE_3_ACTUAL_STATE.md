# Phase 3 Actual Deployment State

**Last Updated:** 2026-04-26  
**Validated by:** phase3-final-validation.sh (23/23 checks pass)

## Fully Operational Services

### Layer 3 — UI Services

| Service | Port | Status | Notes |
|---------|------|--------|-------|
| Open WebUI | :3002 | ✅ healthy | Port adjusted — OpenHands uses :3000 |
| Homarr | :7575 | ✅ healthy | Service dashboard |
| Home Assistant | :8123 | ✅ healthy | Home automation + dashboards |

### Layer 2 — Gateways

| Service | Port | Status | Notes |
|---------|------|--------|-------|
| LiteLLM | :4000 | ✅ healthy | 8 models: 5 Ollama + Claude + GPT-4o |
| MCPO | :8081 | ✅ healthy | Port adjusted — IAP dashboard uses :8080 |
| Vault | :8200 | ✅ healthy | Persistent file storage, 5-of-3 Shamir keys |
| Obot | :8090 | ✅ healthy | Browser OAuth setup still required |

### Layer 1 — Infrastructure

| Service | Port | Status | Notes |
|---------|------|--------|-------|
| Ollama | :11434 | ✅ running | 5 models loaded |
| Plane CE | :3001 | ✅ healthy | Project management |
| Plane API | :8000 | ✅ healthy | REST API |
| Plane DB | :5433 | ✅ healthy | Localhost-only |
| Grafana | :3030 | ✅ running | |
| VictoriaMetrics | :8428 | ✅ healthy | |
| Uptime Kuma | :3033 | ✅ healthy | |

### MCP Servers (7 active)

| Server | Command | Status |
|--------|---------|--------|
| plane-roadmap | python3 mcp/plane_mcp_server.py | ✅ active |
| filesystem-mcp | npx @modelcontextprotocol/server-filesystem | ✅ active |
| postgresql-mcp | npx @modelcontextprotocol/server-postgres | ✅ active |
| docker-mcp | uvx mcp-server-docker | ✅ active |
| sequential-thinking | npx @modelcontextprotocol/server-sequential-thinking | ✅ active |
| memory | npx @modelcontextprotocol/server-memory | ✅ active |
| sqlite | uvx mcp-server-sqlite | ✅ active |

## Port Adjustments vs Original Plan

| Service | Planned | Actual | Reason |
|---------|---------|--------|--------|
| Open WebUI | :3000 | :3002 | OpenHands was already on :3000 |
| MCPO | :8080 | :8081 | IAP dashboard serves on :8080 |

These are the **correct production ports**. All documentation now reflects :3002 and :8081.

## Vault Migration Notes

Vault was migrated from dev mode (ephemeral, in-memory) to server mode (persistent file storage) on 2026-04-26.

- **Storage**: file backend at `/vault/data` (named Docker volume `vault_vault-data`)
- **Init**: 5 key shares, 3-of-5 threshold (Shamir secret sharing)
- **Keys**: saved to `~/vault-init-keys.txt` — **back up to QNAP or password manager immediately**
- **Root token**: `REDACTED_VAULT_ROOT_TOKEN` — stored in `~/control-center-stack/stacks/vault/.env`
- **After restart**: must unseal with 3 keys before Vault serves requests
- **macOS note**: `disable_mlock = true` in vault-config.hcl (mlock not available in Colima containers)

Unseal procedure after restart:
```bash
cd ~/control-center-stack/stacks/vault
KEY1=$(sed -n '1p' ~/vault-init-keys.txt | awk '{print $NF}')
KEY2=$(sed -n '2p' ~/vault-init-keys.txt | awk '{print $NF}')
KEY3=$(sed -n '3p' ~/vault-init-keys.txt | awk '{print $NF}')
for KEY in "$KEY1" "$KEY2" "$KEY3"; do
  docker exec vault-server vault operator unseal -address=http://localhost:8200 "$KEY"
done
```

## Services NOT on Mac Mini (By Design)

| Service | Why not here |
|---------|-------------|
| ComfyUI :8188 | GPU-intensive; planned for Threadripper + RTX 4080 |
| Sonarr/Radarr/Prowlarr | Live on seedbox/NAS, not Mac Mini |
| Home Assistant (host networking) | macOS/Colima doesn't support `network_mode: host`; bridge+port-mapping used instead |

## Pending Manual Steps

| Action | Where | Priority |
|--------|-------|----------|
| Back up vault-init-keys.txt | QNAP or password manager | **CRITICAL** |
| Obot browser setup | http://192.168.10.145:8090 | High |
| GITHUB_TOKEN | docker/.env | Medium |
| BRAVE_API_KEY | docker/.env | Medium |
| Open WebUI → LiteLLM test | http://192.168.10.145:3002 | Medium |
| Home Assistant dashboard config | http://192.168.10.145:8123 | Low |
| Homarr service widgets | http://192.168.10.145:7575 | Low |
| Uptime Kuma monitors | http://192.168.10.145:3033 | Low |

## Quick Health Check

```bash
bash ~/phase3-final-validation.sh
```

Individual spot checks:
```bash
for port in 3002 4000 7575 8081 8090 8123 8200; do
  curl -s -o /dev/null -w ":%{http_code} http://localhost:$port\n" http://localhost:$port
done
```
