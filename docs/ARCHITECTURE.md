# Integrated AI Platform — Architecture

**Last updated:** 2026-04-29 (Phase 14 D-DOC)
**Supersedes:** `docs/_archive/PLATFORM_OVERVIEW.md` (archived 2026-04-29; moved to `_archive/` 2026-05-03 per D-17-16)
**Service inventory:** NetBox CMDB at `netbox.internal` (authoritative)
**Deployment target:** Mac Mini M4 Pro at 192.168.10.145 (`system_profiler`-verified 2026-05-01; D-17-16 drift fix — earlier "M5" framing was wrong)

---

## Control Plane Overview

The platform runs on a single Mac Mini M5 node (`192.168.10.145`). All services
are Docker-managed (Colima). Caddy terminates TLS for all `*.internal` domains
on the LAN. Vault manages all credentials.

### Physical nodes

| Node | Role | IP |
|---|---|---|
| Mac Mini M5 | Control plane (all services) | 192.168.10.145 |
| QNAP TS-X72 | NAS: Plex, Restic backup target, SNMP | 192.168.10.201 |
| OPNsense | Firewall, DNS, DHCP, WireGuard | 192.168.10.1 |
| Home Assistant | Physical HA hub (Zigbee/Z-Wave) | 192.168.10.141 |

Future nodes (not yet deployed):
- MacBook Pro M5 — Block 3 (Ollama parity + Headscale client + smart routing)
- Linux Threadripper — future block
- Mac Studio M3 — future block

---

## Network Map

```
                      192.168.10.0/24 LAN
  ┌──────────────────────────────────────────────────────────────────┐
  │                                                                  │
  │  Mac Mini M5 (192.168.10.145) — Docker (Colima)                 │
  │  ┌──────────────────────────────────────────────────────────┐    │
  │  │  Caddy :443 (TLS terminator for *.internal)             │    │
  │  │  Vault :8200 / seal-vault :8201 (auto-unseal Transit)   │    │
  │  │  Obot :8090 (MCP gateway)                               │    │
  │  │                                                          │    │
  │  │  AI / LLM        Observability       Platform            │    │
  │  │  ─────────────   ───────────────     ─────────────────   │    │
  │  │  Ollama :11434   Grafana :3030       OpenProject :8086 │    │
  │  │  LiteLLM :4000   VictoriaMetrics     Nextcloud :8085    │    │
  │  │  OpenWebUI :3002   :8428             Vaultwarden :8083  │    │
  │  │  Obot :8090      VMAgent :8429       Homarr :7575       │    │
  │  │  AnythingLLM     Uptime Kuma :3033   NetBox :8080       │    │
  │  │    :3004         Node Exporter :9100 MinIO :9000        │    │
  │  │  OpenHands :3000 Zabbix :10080       Homepage :3005     │    │
  │  │                  cAdvisor :8088      Headscale :8082    │    │
  │  │                                                          │    │
  │  │  MCP Layer        Media              Automation          │    │
  │  │  ─────────────   ───────────────     ─────────────────   │    │
  │  │  filesystem:8091  Sonarr :8989       Home Assist :8123  │    │
  │  │  docker:8092      Radarr :7878       Cast-All :8124     │    │
  │  │  docs:8093        Prowlarr :9696                        │    │
  │  │  plex-mcp:8094    Sportarr :1867                        │    │
  │  └──────────────────────────────────────────────────────────┘    │
  │                                                                  │
  │  ┌──────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
  │  │ QNAP (.201)  │  │ OPNsense (.1)    │  │ HA Hub (.141)     │  │
  │  │ Plex:32400   │  │ Firewall/DNS     │  │ HA UI:8123        │  │
  │  │ Restic target│  │ DHCP/WireGuard   │  │ 100+ IoT devices  │  │
  │  └──────────────┘  └──────────────────┘  └───────────────────┘  │
  └──────────────────────────────────────────────────────────────────┘
```

---

## Service Inventory (NetBox-sourced)

**Authoritative source:** NetBox CMDB (`netbox.internal`).
Query live: `CMDB_SOURCE=netbox python3 scripts/cmdb_source.py`

### AI / LLM (9 services)

| Service | Port | Notes |
|---|---|---|
| Ollama | 11434 | Local model runtime (qwen2.5-coder:32b orchestrator, 14b/7b workers) |
| LiteLLM Gateway | 4000 | Local-only routes; cloud LLM routes removed Phase 13.5 |
| OpenWebUI | 3002 | Chat interface over Ollama |
| Obot | 8090 | MCP gateway; Vault Agent sidecar |
| AnythingLLM | 3004 | RAG + knowledge base |
| OpenHands | 3000 | Autonomous coding agent |
| MCPO Proxy | 8081 | OpenAI-compatible MCP proxy |
| Obot MCP Server | — | Obot-managed lifecycle |
| Obot MCP Shim | — | Obot-managed lifecycle |

### MCP Servers (4 compose-managed + Obot-managed)

| Server | Port | Credentials | cap_drop |
|---|---|---|---|
| mcp-filesystem-remote | 8091 | None | ALL |
| mcp-docker-remote | 8092 | None | ALL (compose-managed) |
| mcp-docs-remote | 8093 | None | ALL (+ SETUID/SETGID/CHOWN/DAC_OVERRIDE for startup apt-get) |
| plex-mcp | 8094 | Vault Agent sidecar | ALL |
| sms1obot-mcp-server | 8080 | Obot-managed | Not hardened (D#30) |
| sms1obot-mcp-server-shim | 8099 | Obot-managed | Not hardened (D#30) |

See `docs/architecture-facts/mcp-servers.md` for full MCP topology.

### Observability (6 services)

| Service | Port | Notes |
|---|---|---|
| Grafana | 3030 | Dashboards; Vault Agent sidecar |
| VictoriaMetrics | 8428 | Time-series DB (Prometheus-compatible) |
| VMAgent | 8429 | Scrape collector → VM |
| Uptime Kuma | 3033 | Uptime monitoring |
| Node Exporter | 9100 | Host metrics |
| cAdvisor | 8088 | Container metrics (privileged; documented exception) |
| Zabbix Server | 10051 | Network/SNMP monitoring |
| Zabbix Web UI | 10080 | Zabbix frontend |
| Topology API | 8300 | NetBox-backed service topology |

### Platform (14 services)

| Service | Port | Notes |
|---|---|---|
| HashiCorp Vault | 8200 | Credential store; server mode; file backend |
| Vault Auto-Unseal (Transit) | 8201 | seal-vault container |
| OpenProject | 8086 | Project management (replaced Plane CE 2026-05-01, D-17-04) |
| OpenProject PostgreSQL | (internal) | OpenProject DB (internal to compose network) |
| Nextcloud | 8085 | Calendar/files |
| Vaultwarden | 8083 | Password manager |
| Homarr | 7575 | Alternate dashboard |
| MinIO | 9000 | S3-compatible object storage (QNAP target) |
| Homepage | 3005 | Control center portal |
| Caddy | 443 | TLS reverse proxy |
| Headscale | 8082 | WireGuard VPN controller |
| NetBox CMDB | 8080 | Service registry (authoritative) |

### Media (5 services)

| Service | Port | Host |
|---|---|---|
| Sonarr | 8989 | mac-mini |
| Radarr | 7878 | mac-mini |
| Prowlarr | 9696 | mac-mini |
| Sportarr | 1867 | mac-mini |
| Plex Media Server | 32400 | QNAP |

---

## Secrets Architecture

All credentials live in Vault (`http://vault-server:8200`). No plaintext
credentials in `environment:` blocks, `.env` files, or compose configs.
The `detect-secrets` pre-commit hook enforces this on tracked files.

```
Vault KV  →  Vault Agent sidecar (one-shot, exit_after_auth=true)
          →  /vault/secrets/credentials.env (bind-mount volume)
          →  service entrypoint: set -a && . credentials.env && set +a && exec <binary>
```

- Each credential-bearing service has a per-service AppRole at `auth/approle/role/<service>`
- AppRole credentials at `~/.vault-approle/<service>/` (role-id + secret-id, chmod 600)
- Rendered secrets at `~/.vault-agent-secrets/<service>/` (chmod 600)
- Auto-unseal via Transit seal (seal-vault container at :8201)
- Root token: 30-day TTL orphan token, rotated before expiry
- Audit log: `/vault/logs/audit.log`, 30-day local retention, nightly archive to QNAP

For service provisioning: `docs/runbooks/add-new-service.md`
For credential rotation: `docs/runbooks/rotate-credentials.md`
For Vault restore: `docs/runbooks/vault-restore-from-backup.md`

---

## LLM Access Doctrine

```
claude-local  →  local Ollama (free, no quota; default for routine work)
claude-pro    →  Anthropic Pro subscription (quota-limited; high-judgment tasks only)
```

Platform services **must never depend on Anthropic API access.** `secret/anthropic/api`
is deleted from Vault (Phase 13.5). All platform LLM capability uses local Ollama
via LiteLLM or directly.

Claude Code uses the subagent pattern (`~/.claude/agents/`):
- `decomposer` (qwen2.5-coder:32b): problem decomposition
- `implementer` (qwen2.5-coder:14b): single-spec execution
- `reviewer` (qwen2.5-coder:7b): implementation validation

---

## Container Hardening Doctrine

All containers:
- `cap_drop: [ALL]` with minimal per-class `cap_add`
- `security_opt: [no-new-privileges:true]`

Per-class capability requirements:

| Workload class | Required cap_add | Example |
|---|---|---|
| Stateless HTTP (no user drop) | None | mcp-filesystem-remote |
| setpriv UID/GID drop | SETUID, SETGID | uptime-kuma |
| linuxserver/* (s6-overlay) | CHOWN, SETUID, SETGID, FOWNER, DAC_OVERRIDE | sonarr, radarr |
| Unix socket dir creation | DAC_OVERRIDE | headscale |
| apt-get at startup (drops to _apt) | SETUID, SETGID, CHOWN, DAC_OVERRIDE | mcp-docs-remote |
| cAdvisor container metrics | privileged (documented exception) | cadvisor |

Known hardening gaps (Phase 14 D-DOC tracking):
- `sms1obot-mcp-server*` — Obot-managed; not compose-hardened (D#30)
- `mcp-docs-remote` — broad cap_add required for startup apt-get; pre-built image recommended (D#29)

---

## Backup Policy

- Nightly Restic backup via `scripts/backup.sh` (backup AppRole)
- Vault data: `/vault/data` → Restic repo on QNAP
- Retention: 30-day local, QNAP NAS secondary
- Restore procedure: `docs/runbooks/vault-restore-from-backup.md`
- Quarterly restore test required

---

## Compose File Map

| Stack | File | Services |
|---|---|---|
| Observability | `docker/observability-stack.yml` | vm, vmagent, grafana, uptime-kuma, node-exporter, cadvisor |
| Knowledge | `docker/knowledge-stack.yml` | anythingllm |
| Obot + MCP | `docker/obot-stack.yml` | obot, mcp-filesystem-remote, mcp-docs-remote |
| OpenProject | `docker/openproject/docker-compose.yml` | openproject, openproject-db, openproject-cache (Plane CE retired 2026-05-01, D-17-04) |
| NetBox CMDB | `docker/netbox/docker-compose.yml` | netbox, netbox-worker, netbox-housekeeping, netbox-db, netbox-redis |
| MCP (plex) | `docker/mcp/docker-compose.yml` | plex-mcp, vault-agent-plex-mcp |
| MCP Docker | `docker/mcp/docker-compose.mcp-docker-remote.yml` | mcp-docker-remote |
| Headscale | `docker/headscale/docker-compose.yml` | headscale |
| Arr stack | `~/control-center-stack/stacks/arr-stack/docker-compose.yml` | sonarr, radarr, prowlarr, sportarr |
| Dashboards | `~/control-center-stack/stacks/dashboards/docker-compose.yml` | (empty — Home Assistant retired 2026-05-03 per D-17-34; canonical HA at 192.168.10.141) |
| AI Control | `~/control-center-stack/stacks/ai-control/docker-compose.yml` | homarr |
| Vault | `~/control-center-stack/stacks/vault/docker-compose.yml` | vault-server |
| Seal Vault | `~/control-center-stack/stacks/seal-vault/docker-compose.yml` | seal-vault |

---

## Runbooks Index

| Topic | Runbook |
|---|---|
| Add new service | `docs/runbooks/add-new-service.md` |
| Add new MCP server | `docs/runbooks/add-new-mcp-server.md` |
| Add new host | `docs/runbooks/add-new-host.md` |
| Restart services | `docs/runbooks/restart-services.md` |
| Rotate credentials | `docs/runbooks/rotate-credentials.md` |
| Vault unseal | `docs/runbooks/vault-unseal.md` |
| Vault Shamir recovery | `docs/runbooks/vault-recovery-from-shamir.md` |
| Vault restore from backup | `docs/runbooks/vault-restore-from-backup.md` |
| Vault token rotation | `docs/runbooks/vault-token-rotation.md` |
| Drift detection | `docs/runbooks/drift-detection-procedure.md` |
| Regression probe failure | `docs/runbooks/regression-probe-failure.md` |
| Incident response | `docs/runbooks/incident-response.md` |
| Operating model | `docs/runbooks/operating-model.md` |
