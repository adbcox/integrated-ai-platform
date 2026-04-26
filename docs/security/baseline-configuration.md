# Security Baseline Configuration

## Platform Security Posture (Mac Mini 192.168.10.113)

### Container Hardening

| Control | Status | Notes |
|---------|--------|-------|
| Non-root containers | Partial | Most run as root; Vault, LiteLLM, Open WebUI run as root due to upstream images |
| Read-only filesystems | No | Not yet enforced — workspace mounts require write access |
| Docker socket restricted | Partial | Homarr uses :ro; Obot uses rw (required for Docker MCP) |
| No privileged containers | Yes | Home Assistant skipped; no `privileged: true` |
| Network segmentation | Yes | `control-center-net` + `docker_plane-net` are separate bridge networks |
| Image vulnerability scanning | Planned | Trivy not installed; run via Docker: `docker run aquasec/trivy image <img>` |

### Docker Bench Security (ARM64 note)

The official `docker/docker-bench-security` image is x86-only and fails on Apple Silicon.
Run manually:

```bash
# Install and run natively (requires brew):
brew install docker-bench-security 2>/dev/null || true

# Or check specific CIS controls manually:
# CIS DI-1: Separate partition for containers
# CIS DI-2: Container-specific OS (N/A for macOS)
# CIS DI-3: Docker daemon hardening — check: docker info | grep -E "Security|Logging"
docker info 2>/dev/null | grep -E "Security Options|Logging Driver"
```

### Secrets Management

| Secret | Current Location | Target |
|--------|-----------------|--------|
| PLANE_API_TOKEN | docker/.env | Vault → `secret/plane/api_token` |
| OBOT_ADMIN_PASSWORD | docker/.env | Vault → `secret/obot/admin_password` |
| LITELLM_MASTER_KEY | control-center-stack/.env | Vault → `secret/litellm/master_key` |
| WEBUI_SECRET_KEY | control-center-stack/.env | Vault → `secret/openwebui/secret_key` |
| VAULT_ROOT_TOKEN | control-center-stack/.env | Secured offline |
| ANTHROPIC_API_KEY | Not set | Vault → `secret/cloud/anthropic` |
| GITHUB_TOKEN | Not set | Vault → `secret/github/token` |

### Vault Secret Migration Procedure

```bash
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=$(grep VAULT_ROOT_TOKEN ~/control-center-stack/stacks/vault/.env | cut -d= -f2-)

# Enable KV secrets engine
vault secrets enable -path=secret kv-v2

# Migrate Plane credentials
vault kv put secret/plane/api_token \
  value="$(grep PLANE_API_TOKEN /Users/admin/repos/integrated-ai-platform/docker/.env | cut -d= -f2-)"

# Migrate LiteLLM master key
vault kv put secret/litellm/master_key \
  value="$(grep LITELLM_MASTER_KEY ~/control-center-stack/stacks/gateways/.env | cut -d= -f2-)"

# Read back to verify
vault kv get secret/plane/api_token
vault kv get secret/litellm/master_key
```

### Vulnerability Remediation SLA

| Severity | Response | Remediation |
|----------|----------|-------------|
| Critical (CVSS 9+) | 4 hours | 24 hours |
| High (CVSS 7-9) | 24 hours | 7 days |
| Medium (CVSS 4-7) | 1 week | 30 days |
| Low | Monthly review | Next cycle |

### Network Exposure Inventory

| Service | Internal Port | Host Binding | Notes |
|---------|--------------|--------------|-------|
| Plane CE | 3001 | 0.0.0.0 | LAN-accessible |
| Obot Gateway | 8090 | 0.0.0.0 | LAN-accessible |
| LiteLLM | 4000 | 0.0.0.0 | LAN-accessible |
| Open WebUI | 3002 | 0.0.0.0 | LAN-accessible |
| Homarr | 7575 | 0.0.0.0 | LAN-accessible |
| Vault | 8200 | 0.0.0.0 | LAN-only in dev mode — restrict for prod |
| PostgreSQL | 5433 | 127.0.0.1 | Localhost only ✓ |
| Ollama | 11434 | 127.0.0.1 | Localhost only ✓ |
| Grafana | 3030 | 0.0.0.0 | LAN-accessible |
| Uptime Kuma | 3033 | 0.0.0.0 | LAN-accessible |

All services are behind OPNsense firewall (192.168.10.1). No services exposed to internet.
