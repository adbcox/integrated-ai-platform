# Audit & Compliance

## Logging Architecture

| Service | Log Type | Location | Retention |
|---------|----------|----------|-----------|
| Obot Gateway | JSONL audit | `docker exec obot cat /data/audit.log` | 90 days |
| LiteLLM | Request logs | `docker logs litellm-gateway` | Container lifecycle |
| Vault | Audit log | Disabled by default in dev — enable for prod | 90 days |
| Plane CE | Django logs | `docker logs docker-plane-api-1` | Container lifecycle |
| VictoriaMetrics | Metrics TSDB | `docker/vmagent-config/` | 30 days default |

## Enabling Vault Audit Logging

```bash
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=$(grep VAULT_ROOT_TOKEN ~/control-center-stack/stacks/vault/.env | cut -d= -f2-)

# Enable file audit log
vault audit enable file file_path=/vault/logs/audit.log

# Verify
vault audit list
```

## Weekly Security Checks

```bash
#!/usr/bin/env bash
# docs/security/weekly-check.sh

echo "=== Weekly Security Check $(date) ==="

# 1. Check for container restarts (sign of crashes/exploits)
echo "Container restarts:"
docker ps -a --format "{{.Names}}: {{.Status}}" | grep -v "Up" | head -10

# 2. Check disk usage (bloat can indicate log injection)
echo "Disk usage:"
df -h / | tail -1

# 3. Check for new processes (unexpected spawns)
docker stats --no-stream --format "{{.Name}}: CPU={{.CPUPerc}} MEM={{.MemUsage}}" | head -15

# 4. Scan high-risk images (run quarterly)
# docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
#   aquasec/trivy image $(docker images -q | head -5)

# 5. Check Vault health
curl -sf http://localhost:8200/v1/sys/health | python3 -m json.tool | grep -E "sealed|initialized"
```

## Access Review Schedule

| Activity | Frequency | Responsible |
|----------|-----------|-------------|
| MCP server permission audit | Monthly | Admin |
| Docker image updates | Monthly | Admin |
| Secret rotation (API keys) | Quarterly | Admin |
| Vault access policy review | Quarterly | Admin |
| Full security audit | Annually | Admin |

## CIS Docker Benchmark — Key Controls

| Control | Description | Status |
|---------|-------------|--------|
| 2.1 | Restrict container communication | ✅ Network segmentation |
| 2.2 | Logging level set to INFO | ✅ VAULT_LOG_LEVEL=info |
| 4.1 | Containers run as non-root | ⚠️ Partial — most upstream images run as root |
| 4.5 | Container filesystems read-only | ⚠️ Not enforced |
| 5.1 | AppArmor/SELinux profiles | ⚠️ N/A on macOS |
| 5.12 | Limit memory usage | ⚠️ Not set (48GB available headroom) |
| 5.25 | Containers use content trust | ⚠️ Not enabled |

Priority hardening: 4.1 (non-root) and 5.12 (memory limits) for production readiness.
