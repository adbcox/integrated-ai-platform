# Integrated AI Platform — Platform Overview

**Deployment target:** Mac Mini M4 Pro at 192.168.10.145  
**Current phase:** Phase 12 Complete (Zabbix monitoring fully operational)  
**Services running:** 55+ across 6 categories  
**Last updated:** 2026-04-27

---

## Architecture Diagram

```
                        192.168.10.0/24 LAN
  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                 │
  │  ┌─────────────────────────────────────────────────────────┐   │
  │  │  Mac Mini M4 Pro (.145) — Primary Platform Node         │   │
  │  │                                                         │   │
  │  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │   │
  │  │  │  AI / LLM    │  │  Platform    │  │ Observability│  │   │
  │  │  │  Layer       │  │  Layer       │  │  Layer       │  │   │
  │  │  │              │  │              │  │              │  │   │
  │  │  │ Ollama:11434 │  │ Plane:3001   │  │ Zabbix:10080 │  │   │
  │  │  │ LiteLLM:4000 │  │ Vault:8200   │  │ Grafana:3030 │  │   │
  │  │  │ OpenWebUI:3002│  │ IAP-Dash:8080│  │ VictMetr:8428│  │   │
  │  │  │ Obot:8090    │  │ Homarr:7575  │  │ UptimeK:3033 │  │   │
  │  │  │ AnythingLLM: │  │ AnythingLLM: │  │ NodeExp:9100 │  │   │
  │  │  │   3004       │  │   3004       │  │              │  │   │
  │  │  └──────────────┘  └──────────────┘  └─────────────┘  │   │
  │  │                                                         │   │
  │  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │   │
  │  │  │  MCP Servers │  │    Media     │  │  Automation │  │   │
  │  │  │  Layer       │  │    Layer     │  │  Layer      │  │   │
  │  │  │              │  │              │  │             │  │   │
  │  │  │ filesystem:  │  │ Sonarr:8989  │  │ HomeAssist: │  │   │
  │  │  │   8091       │  │ Radarr:7878  │  │   8123      │  │   │
  │  │  │ docker:8092  │  │ Prowlarr:9696│  │             │  │   │
  │  │  │ docs:8093    │  │ Sportarr:1867│  │             │  │   │
  │  │  │ mcpo:8081    │  │              │  │             │  │   │
  │  │  └──────────────┘  └──────────────┘  └─────────────┘  │   │
  │  └─────────────────────────────────────────────────────────┘   │
  │                                                                 │
  │  ┌────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
  │  │ QNAP TS-X72    │  │ OPNsense Firewall │  │ Home Assist.  │  │
  │  │ (.201)         │  │ (.1)             │  │ (.141)        │  │
  │  │                │  │                  │  │               │  │
  │  │ Plex:32400     │  │ Web UI :443      │  │ HA UI :8123   │  │
  │  │ NAS Storage    │  │ DHCP/DNS/VPN     │  │ Zigbee/Z-Wave │  │
  │  │ SNMP :161      │  │ SNMP :161        │  │ 100+ devices  │  │
  │  └────────────────┘  └──────────────────┘  └───────────────┘  │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘
```

---

## MCP Tool Routing (Three-Tier Architecture)

```
Claude Code (CLI)
│
├── Tier 1 — Direct (zero round-trip)
│   ├── filesystem-mcp    — local repo read/write
│   ├── docker            — container management
│   ├── plane-roadmap     — Plane project API
│   ├── postgresql        — Plane DB (port 5433)
│   ├── sequential-thinking
│   ├── memory            — knowledge graph
│   └── sqlite            — platform_analytics.db
│
└── Tier 2 — Via Obot Gateway (:8090)
    ├── GitHub MCP        — PRs, repos, issues
    ├── PostgreSQL MCP    — Plane DB via Obot
    ├── Filesystem MCP    — /workspace (Docker)
    ├── Weather, Fitness, Strava, Home Assistant
    └── Semgrep (SAST)

Claude Desktop
└── Via Obot :8090 (all tools)

Open WebUI
└── Via MCPO Proxy :8081 (OpenAPI bridge for stdio MCPs)
```

---

## Quick Start

```bash
# 1. Check platform health
cd ~/repos/integrated-ai-platform
bash scripts/validate-cmdb.sh

# 2. Start core stacks (if not running)
cd docker
docker-compose -f docker-compose.yml up -d          # Plane + core
docker-compose -f obot-stack.yml up -d              # Obot + MCP remotes
docker-compose -f monitoring-stack.yml up -d        # Grafana + VictoriaMetrics
docker-compose -f zabbix/docker-compose.yml up -d   # Zabbix

# 3. Check all containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | sort

# 4. Unseal Vault (after reboot)
export VAULT_ADDR=http://localhost:8200
vault operator unseal   # run 3x with keys from ~/vault-init-keys.txt

# 5. Verify key endpoints
curl -s http://localhost:8080/health          # IAP Dashboard
curl -s http://localhost:8090/api/healthz     # Obot
curl -s http://localhost:10080               # Zabbix Web
```

---

## Services Reference

### AI Layer

| Service | Host | Port | Status | Purpose |
|---------|------|------|--------|---------|
| Ollama | mac-mini | 11434 | Running | Local LLM runtime — 6 models (~57 GB) |
| LiteLLM Gateway | mac-mini | 4000 | Running | Unified OpenAI-compatible API over Ollama + Anthropic |
| Open WebUI | mac-mini | 3002 | Running | Multi-model chat UI with RAG |
| Obot | mac-mini | 8090 | Running | AI agent orchestrator + MCP gateway |
| AnythingLLM | mac-mini | 3004 | Running | Semantic search over platform docs |
| OpenHands | mac-mini | 3000 | Stopped | AI software engineering agent (on-demand) |
| MCPO Proxy | mac-mini | 8081 | Running | MCP stdio → OpenAPI bridge for Open WebUI |

**Local models (Ollama):**

| Model | Size | Use Case |
|-------|------|----------|
| qwen2.5-coder:32b | ~20 GB | Primary code generation, aider |
| qwen2.5-coder:7b | ~5 GB | Fast code gen, decomposition |
| llama3.3:70b | ~40 GB | General reasoning, long context |
| deepseek-r1:32b | ~20 GB | Chain-of-thought, planning |
| nomic-embed-text | ~0.3 GB | RAG embeddings (768-dim) |
| mxbai-embed-large | ~0.7 GB | Secondary embeddings, reranking |

### Platform Layer

| Service | Host | Port | Status | Purpose |
|---------|------|------|--------|---------|
| IAP Dashboard | mac-mini | 8080 | Running | Control plane UI — roadmap, execution, service graph |
| HashiCorp Vault | mac-mini | 8200 | Running | Secrets management (Shamir 5-of-3 unseal) |
| Plane CE | mac-mini | 3001 | Running | Project management — 601 roadmap items, MCP-integrated |
| Plane API | mac-mini | 8000 | Running | Plane REST backend |
| Plane PostgreSQL | mac-mini | 5433 | Running | Plane project database |
| MinIO | mac-mini | 9000 | Running | S3-compatible object storage for Plane attachments |
| Homarr | mac-mini | 7575 | Running | Service discovery dashboard |

### Observability Layer

| Service | Host | Port | Status | Purpose |
|---------|------|------|--------|---------|
| Zabbix Web | mac-mini | 10080 | Running | Monitoring frontend — hosts, triggers, dashboards |
| Zabbix Server | mac-mini | 10051 | Running | Active poller — agent + SNMP collection |
| Grafana | mac-mini | 3030 | Running | Metric dashboards (VictoriaMetrics + Zabbix datasources) |
| VictoriaMetrics | mac-mini | 8428 | Running | Long-term metric storage (90-day, PromQL) |
| VMAgent | mac-mini | 8429 | Running | Metric scraper for all /metrics endpoints |
| Uptime Kuma | mac-mini | 3033 | Running | HTTP uptime monitoring — 12 service monitors |
| Node Exporter | mac-mini | 9100 | Running | Host CPU/mem/disk/net metrics |

**Monitored Hosts (Zabbix):**

| Host | IP | Method | Template |
|------|----|--------|----------|
| Mac Mini M4 Pro | 192.168.10.145:10050 | Native agentd | Linux by Zabbix agent |
| OPNsense Firewall | 192.168.10.1:161 | SNMP v2c | OPNsense by SNMP |
| QNAP TS-X72 | 192.168.10.201:161 | SNMP v2c | Linux by SNMP |

### MCP Server Layer

| Service | Host | Port | Transport | Purpose |
|---------|------|------|-----------|---------|
| filesystem-mcp (direct) | mac-mini | — | stdio | Claude Code direct — full repo read/write |
| mcp-filesystem-remote | mac-mini | 8091 | HTTP | Obot-facing filesystem (read-only /workspace) |
| mcp-docker-remote | mac-mini | 8092 | HTTP | Docker MCP on host (Colima socket, launchd-managed) |
| mcp-docs-remote | mac-mini | 8093 | HTTP | @arabold/docs-mcp-server via supergateway |
| plane-roadmap (direct) | mac-mini | — | stdio | Claude Code direct — Plane API tool |
| postgresql (direct) | mac-mini | 5433 | TCP | Claude Code direct — Plane DB queries |
| docker (direct) | mac-mini | — | socket | Claude Code direct — container management |
| memory (direct) | mac-mini | — | stdio | Claude Code direct — knowledge graph |
| sqlite (direct) | mac-mini | — | file | Claude Code direct — platform_analytics.db |
| sequential-thinking (direct) | mac-mini | — | stdio | Claude Code direct — reasoning scaffold |

### Media Layer

| Service | Host | Port | Status | Purpose |
|---------|------|------|--------|---------|
| Sonarr | mac-mini | 8989 | Running | TV automation — 185 shows tracked |
| Radarr | mac-mini | 7878 | Running | Movie automation — 425 movies tracked |
| Prowlarr | mac-mini | 9696 | Running | Indexer manager — 5 indexers |
| Sportarr | mac-mini | 1867 | Running | Sports TV automation |
| Plex | qnap | 32400 | Running | Media streaming (QNAP-hosted library) |

### Automation Layer

| Service | Host | Port | Status | Purpose |
|---------|------|------|--------|---------|
| Home Assistant (container) | mac-mini | 8123 | Running | HA container with Sonarr/Radarr REST sensors |
| Home Assistant (device) | 192.168.10.141 | 8123 | Running | Physical HA — 100+ Zigbee/Z-Wave devices |

---

## Full Port Reference

| Port | Service | Host |
|------|---------|------|
| 443 | OPNsense Web UI / Caddy TLS | opnsense / mac-mini |
| 1867 | Sportarr | mac-mini |
| 3000 | OpenHands | mac-mini |
| 3001 | Plane CE | mac-mini |
| 3002 | Open WebUI | mac-mini |
| 3004 | AnythingLLM | mac-mini |
| 3030 | Grafana | mac-mini |
| 3033 | Uptime Kuma | mac-mini |
| 4000 | LiteLLM Gateway | mac-mini |
| 5433 | Plane PostgreSQL | mac-mini |
| 7575 | Homarr | mac-mini |
| 7878 | Radarr | mac-mini |
| 8000 | Plane API | mac-mini |
| 8080 | IAP Dashboard | mac-mini |
| 8081 | MCPO Proxy | mac-mini |
| 8090 | Obot Gateway | mac-mini |
| 8091 | MCP Filesystem (remote HTTP) | mac-mini |
| 8092 | MCP Docker (remote HTTP, host) | mac-mini |
| 8093 | MCP Docs (remote HTTP) | mac-mini |
| 8123 | Home Assistant | mac-mini |
| 8200 | HashiCorp Vault | mac-mini |
| 8428 | VictoriaMetrics | mac-mini |
| 8429 | VMAgent | mac-mini |
| 8989 | Sonarr | mac-mini |
| 9000 | MinIO | mac-mini |
| 9100 | Node Exporter | mac-mini |
| 9696 | Prowlarr | mac-mini |
| 10050 | Zabbix Agent (native, macOS) | mac-mini |
| 10051 | Zabbix Server | mac-mini |
| 10080 | Zabbix Web UI | mac-mini |
| 11434 | Ollama | mac-mini |
| 32400 | Plex | qnap |

---

## Key File Locations

| Path | Purpose |
|------|---------|
| `docker/docker-compose.yml` | Core platform stack (Plane, Vault, IAP Dashboard) |
| `docker/obot-stack.yml` | Obot gateway + MCP remote servers |
| `docker/monitoring-stack.yml` | Grafana + VictoriaMetrics + Uptime Kuma |
| `docker/zabbix/docker-compose.yml` | Zabbix 7.4 + TimescaleDB |
| `config/service-registry.yaml` | CMDB — all 56 services with ports, health URLs, security baseline |
| `docs/adr/` | Architecture Decision Records (A-001 through A-008) |
| `docs/roadmap/ITEMS/` | 601 roadmap items (canonical truth) |
| `scripts/validate-cmdb.sh` | CMDB integrity checker (6 checks) |
| `~/vault-init-keys.txt` | Vault unseal keys (NOT in repo — gitignored) |
| `/usr/local/etc/zabbix/zabbix_agentd.conf` | Mac Mini Zabbix native agent config |
| `/Library/LaunchDaemons/com.zabbix.zabbix_agentd.plist` | Zabbix agent launchd service |

---

## Known Issues and Constraints

- **Vault unseal required after reboot:** 3 of 5 Shamir keys from `~/vault-init-keys.txt`
- **Colima VM memory:** 8 GB; Zabbix PostgreSQL uses conservative 256 MB `shared_buffers`. Adding memory: `colima stop && colima start --memory 16`
- **Zabbix API PSK bug (7.4):** `host.update` with `tls_connect=4` throws "value must be empty" — use direct psql UPDATE as workaround
- **QNAP SNMP template:** "Linux by SNMP" has many unsupported OIDs; consider switching to "Network Generic Device by SNMP"
- **LiteLLM Gateway / OpenHands / Open WebUI:** Currently stopped — start on demand with `docker start litellm-gateway open-webui openhands`
- **mcp-docker-remote:** Runs on host via launchd (`com.iap.mcp.docker`), not in Docker — Colima socket is not mountable from containers
- **Obot shim containers:** Use dynamic names (ms1xxxxx pattern) — registered in service registry with `container: null`

---

## Operations Runbooks

| Task | Reference |
|------|-----------|
| Deploy / restart services | `docs/DEPLOYMENT_GUIDE.md` |
| Diagnose service failures | `docs/TROUBLESHOOTING.md` |
| Architecture decisions | `docs/adr/` |
| Add a new roadmap item | `docs/roadmap/ITEMS/` |
| Sync Plane with repo | `python3 bin/sync_roadmap_to_plane.py` |
| Validate CMDB | `bash scripts/validate-cmdb.sh` |
| Rotate a secret | Vault UI at http://192.168.10.145:8200 |
