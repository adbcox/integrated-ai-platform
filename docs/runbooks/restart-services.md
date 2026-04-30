# Runbook: Restart Services

**Last updated:** 2026-04-29 (Phase 14 D-DOC rewrite)
**Supersedes:** pre-Phase-13 version that referenced `docker/.env` and Obot-only patterns.

All platform services use Docker Compose. Services that consume secrets
have a Vault Agent sidecar that runs once at startup (`exit_after_auth=true`).
After a restart, the sidecar re-authenticates and re-renders `credentials.env`
before the service container starts.

---

## General restart pattern

For any service managed by a compose file:

```bash
# Navigate to the repo root
cd ~/repos/integrated-ai-platform

# Restart a single service (sidecar runs automatically via depends_on)
docker compose -f docker/<stack>.yml up -d <service-name>

# Verify health
docker inspect <service-name> --format '{{.State.Health.Status}}'
```

If a service has a Vault Agent sidecar (most do), the sidecar must complete
successfully before the service starts. This is enforced by:
```yaml
depends_on:
  vault-agent-<svc>:
    condition: service_completed_successfully
```

Do NOT use `--no-deps` — the sidecar is a dependency, not optional.

---

## Obot gateway

```bash
cd ~/repos/integrated-ai-platform/docker
docker compose -f obot-stack.yml up -d obot

# Verify
curl -sf http://localhost:8090/api/healthz && echo "obot: OK"
```

Obot has a Vault Agent sidecar (`vault-agent-obot`); it exits 0 after
rendering credentials, then obot starts. Full health within ~30 seconds.

---

## MCP servers (remote HTTP, Docker-managed)

```bash
cd ~/repos/integrated-ai-platform/docker

# Filesystem MCP
docker compose -f obot-stack.yml up -d mcp-filesystem-remote
curl -sf http://localhost:8091/healthz && echo "filesystem: OK"

# Docs MCP (note: ~3 min startup — runs apt-get + npm install on start)
docker compose -f obot-stack.yml up -d mcp-docs-remote
until curl -sf http://localhost:8093/healthz 2>/dev/null; do sleep 5; done
echo "docs: OK"

# Plex MCP (in docker/mcp/ — has Vault Agent sidecar)
cd docker/mcp && docker compose up -d plex-mcp
curl -sf http://localhost:8094/healthz && echo "plex-mcp: OK"
```

---

## mcp-docker-remote (macOS host, compose-managed)

mcp-docker-remote runs on the macOS host (Docker socket not accessible
from inside containers). It is managed via a dedicated compose file:

```bash
cd ~/repos/integrated-ai-platform/docker/mcp
docker compose -f docker-compose.mcp-docker-remote.yml up -d mcp-docker-remote
curl -sf http://localhost:8092/healthz && echo "docker-mcp: OK"
```

For persistence across reboots, use the launchd agent:
```bash
launchctl load ~/Library/LaunchAgents/com.iap.mcp.docker.plist
```

---

## Observability stack (vm, vmagent, grafana, uptime-kuma, node-exporter)

```bash
cd ~/repos/integrated-ai-platform/docker
docker compose -f observability-stack.yml up -d

# Spot-check
curl -sf http://localhost:8428/health && echo "VictoriaMetrics: OK"
curl -sf http://localhost:8429/health && echo "vmagent: OK"
curl -sf http://localhost:3030/api/health && echo "Grafana: OK"
```

---

## Plane CE (project management)

```bash
cd ~/repos/integrated-ai-platform/docker
docker compose -f docker-compose-plane.yml up -d

# All sidecars (vault-agent-plane-*) run first; check healthy state
docker compose -f docker-compose-plane.yml ps
```

---

## Vault server

Vault should not be restarted casually — auto-unseal via seal-vault is
required. If a restart is necessary:

```bash
docker compose -f ~/control-center-stack/stacks/vault/docker-compose.yml up -d vault-server
sleep 15
docker exec vault-server vault status | grep -E "Sealed|Initialized"
# Expected: Sealed=false, Initialized=true
```

If sealed after restart, see `docs/runbooks/vault-unseal.md`.

---

## Arr stack (sonarr, radarr, prowlarr, sportarr)

```bash
cd ~/control-center-stack/stacks/arr-stack
docker compose up -d

curl -sf http://localhost:8989/ping && echo "sonarr: OK"
curl -sf http://localhost:7878 && echo "radarr: OK"
curl -sf http://localhost:9696/ping && echo "prowlarr: OK"
```

---

## Restart everything (full platform)

```bash
# In-repo stacks
cd ~/repos/integrated-ai-platform/docker
for f in observability-stack.yml knowledge-stack.yml obot-stack.yml docker-compose-plane.yml; do
  docker compose -f $f up -d
done
docker compose -f mcp/docker-compose.yml up -d
docker compose -f mcp/docker-compose.mcp-docker-remote.yml up -d

# Out-of-repo stacks
for stack in arr-stack dashboards ai-control seal-vault; do
  (cd ~/control-center-stack/stacks/$stack && docker compose up -d)
done

# Verify regression probe
bash ~/repos/integrated-ai-platform/docs/phase-13/h1-regression-probe.sh
```
