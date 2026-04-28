# COMPLETE INFRASTRUCTURE INVENTORY
**Generated:** 2026-04-27 08:45  
**System:** Mac Mini M5 (192.168.10.145) — Autonomous AI Infrastructure  
**Phases:** 1–12 (Phase 12: Zabbix deployed)  
**Uptime:** 4 days, 29 minutes | Load: 7.65 / 7.26 / 7.08

---

## SECTION 1: REPOSITORY & CODEBASE INVENTORY

### Git State

| Field | Value |
|-------|-------|
| Active branch | `main` (ahead of origin by 15 commits) |
| Other branches | `exec-lane`, `reuse-wave-closeout-reconciled` |
| Repository path | `~/repos/integrated-ai-platform` |
| Repository size | 1.3 GB |

**Latest Commits:**
```
3664316 Phase 12: Zabbix 7.4 monitoring stack deployed
994e762 Phase 11: Documentation & Knowledge Transfer + Phase 9/10 code changes
5f40c13 Phase 9: MCP server deployment — 9 servers installed, Claude Desktop configured
bcee2fa Phase 8: Update README to reflect AnythingLLM migration
5d4fd2b Phase 8: Remove all docs migrated to AnythingLLM knowledge base
7e06314 fix: batch update-embeddings to avoid Prisma transaction timeout
e5dbdf2 feat: ingest-docs.py — path-aware metadata and context enrichment
9e7a82a feat: Phase 7 complete — CMDB, CI, knowledge base, ADR structure
66559e8 feat: Phase 6 complete — DNS hostnames, Vault secrets, Prowlarr fix
ae07d2b feat: QNAP media migration complete
```

### File Counts

| Type | Count |
|------|-------|
| Python (.py) | 822 |
| JSON | 1,172 |
| Shell scripts (.sh) | 65 |
| YAML (.yaml/.yml) | 33 |
| Markdown (.md) | 53 |

### Docker Compose Files
```
docker-compose.yml                          (root — browser-operator)
docker/docker-compose-ai-dashboard.yml
docker/docker-compose-dashboards.yml
docker/docker-compose-plane.yml
docker/knowledge-stack.yml
docker/obot-stack.yml
docker/observability-stack.yml
docker/zabbix-stack.yml
docker/zabbix/docker-compose.yml
```

### Governance
- **CODEOWNERS:** `@adbcox` on all protected paths (docs/, docker/, config/, .github/, *.env)
- **GitHub Actions:** `validate-infrastructure.yml` (YAML lint + CMDB validation on PR/push to main)
- `pr-agent.yml.disabled` (disabled)

---

## SECTION 2: CMDB — SERVICE REGISTRY

**File:** `config/service-registry.yaml` — 628 lines, 32 registered services  
**Validation:** All 32 registry containers confirmed running; 5 health checks failed (timeouts — see Section 4); 23 undocumented containers (Obot phat shims + Zabbix stack)

### Services by Category

#### AI (10 services)
| ID | Name | Port | Image |
|----|------|------|-------|
| litellm-gateway | LiteLLM Gateway | 4000 | ghcr.io/berriai/litellm:main-latest |
| open-webui | Open WebUI | 3002 | ghcr.io/open-webui/open-webui:main |
| ollama | Ollama (host process) | 11434 | — (native) |
| obot | Obot | 8090 | obot/obot:latest |
| openhands | OpenHands | 3000 | (custom image) |
| mcpo-proxy | MCPO Proxy | 8081 | nikolaik/python-nodejs:python3.12-nodejs22-slim |
| anythingllm | AnythingLLM | 3004 | mintplexlabs/anythingllm:latest |
| obot-mcp-server | Obot MCP Server | — | ghcr.io/obot-platform/obot-mcp-server:v0.1.1 |
| obot-mcp-shim | Obot MCP Shim | — | ghcr.io/nanobot-ai/nanobot:v0.0.67 |

#### Platform (9 services)
| ID | Name | Port | Image |
|----|------|------|-------|
| vault | HashiCorp Vault | 8200 | hashicorp/vault:latest |
| plane | Plane CE | 3001 | makeplane/plane-frontend:stable |
| plane-api | Plane API | 8000 | makeplane/plane-backend:stable |
| plane-db | Plane PostgreSQL | 5433 | postgres:15-alpine |
| plane-minio | MinIO | 9000 | minio/minio:latest |
| plane-redis | Plane Redis | — | redis:7.2-alpine |
| plane-worker | Plane Worker | — | makeplane/plane-backend:stable |
| plane-beat | Plane Beat Scheduler | — | makeplane/plane-backend:stable |
| homarr | Homarr | 7575 | ghcr.io/ajnart/homarr:latest |
| iap-dashboard | IAP Control Plane | 8080 | (referenced, not seen running) |

#### Observability (5 services)
| ID | Name | Port | Image |
|----|------|------|-------|
| grafana | Grafana | 3030 | grafana/grafana:10.4.2 |
| victoriametrics | VictoriaMetrics | 8428 | victoriametrics/victoria-metrics:v1.99.0 |
| vmagent | VMAgent | 8429 | victoriametrics/vmagent:v1.99.0 |
| uptime-kuma | Uptime Kuma | 3033 | louislam/uptime-kuma:1 |
| node-exporter | Node Exporter | 9100 | prom/node-exporter:v1.7.0 |

#### Media (5 services)
| ID | Name | Port | Image |
|----|------|------|-------|
| sonarr | Sonarr | 8989 | lscr.io/linuxserver/sonarr:latest |
| radarr | Radarr | 7878 | lscr.io/linuxserver/radarr:latest |
| prowlarr | Prowlarr | 9696 | lscr.io/linuxserver/prowlarr:latest |
| sportarr | Sportarr | 1867 | sportarr/sportarr:latest |
| plex | Plex (QNAP .201) | 32400 | — (on QNAP) |

#### Automation (2 services)
| ID | Name | Port |
|----|------|------|
| homeassistant-container | HA (Mac Mini) | 8123 |
| homeassistant-physical | HA (.141) | 8123 |

#### Network (1 service)
| ID | Name | Host |
|----|------|------|
| opnsense | OPNsense Firewall | 192.168.10.1 |

---

## SECTION 3: PHASE 8 — CORE SERVICES DETAIL

### Plane CE

| Attribute | Value |
|-----------|-------|
| Uptime | 2 days (web/beat/worker), 42h (api/db) |
| Web UI | http://localhost:3001 — ✅ HTTP 200 |
| API | http://localhost:8000 — ✅ healthy |
| PostgreSQL | localhost:5433 — ✅ healthy |
| Redis | Internal only — ✅ healthy |
| MinIO | 9000/9001 — ✅ running |
| Image | makeplane/plane-{frontend,backend}:stable |
| Compose | docker/docker-compose-plane.yml |

### AnythingLLM

| Attribute | Value |
|-----------|-------|
| Uptime | 24 minutes (recently restarted) |
| Status | ✅ healthy |
| Port | 3004 → internal 3001 |
| API ping | ✅ `{"online":true}` |
| Image | mintplexlabs/anythingllm:latest |
| Storage volume | `anythingllm-storage` + `docker_anythingllm-storage` |
| Memory | 284 MB |
| Compose | docker/knowledge-stack.yml |

### CMDB (Service Registry)

| Attribute | Value |
|-----------|-------|
| File | config/service-registry.yaml |
| Services | 32 registered |
| Schema | ✅ valid |
| Port conflicts | ✅ none |
| CI validation | ✅ GitHub Actions on every PR |
| Undocumented containers | 23 (Obot phat shims + Zabbix — expected) |
| Health checks passing | 18/23 with health_urls |

---

## SECTION 4: PHASES 9–10 — MCP SERVERS DETAIL

### Obot Gateway

| Attribute | Value |
|-----------|-------|
| Port | 8090 → internal 8080 |
| Status | ✅ healthy, running 9h |
| Image | obot/obot:latest |
| Dev mode | `OBOT_DEV_MODE=true` (no auth — intentional) |
| Audit log | /data/audit.log (volume: obot-data:/data) |
| Memory | 284 MB / 2 GB limit |
| CPU | ~16% |

### MCP Server Inventory (10 via Obot + additional via Claude Code)

#### Remote HTTP (persistent, instant start)
| Server | Container | Port | Status | Memory | Health |
|--------|-----------|------|--------|--------|--------|
| Filesystem | mcp-filesystem-remote | 8091 | ⚠️ unhealthy (false negative — curl absent from healthcheck image) | 556 MB | Serving on port |
| Docker | nohup host process | 8092 | ✅ port up | — | Responding |
| Docs | mcp-docs-remote | 8093 | ✅ healthy | 1.57 GB | Serving on port |

**Note:** mcp-docs-remote is using 1.57 GB — largest single MCP container. Docs server indexes content at runtime.

#### NPX Phat Containers (spawned on demand by Obot)
| Server | Tools | Notes |
|--------|-------|-------|
| PostgreSQL | 1 | Connects to plane DB at localhost:5433 |
| GitHub | 26 | PAT-authenticated |
| Weather | 17 | Open-Meteo, no auth |
| Health & Fitness | 17 | No auth |
| Semgrep | 7 | No auth |
| Strava | 24 | OAuth — token expires ~6h, no auto-refresh |
| Home Assistant | 3 | Token from docker/.env |

**Phat image:** `ghcr.io/obot-platform/mcp-images/phat:v0.20.2`  
**Shim image:** `ghcr.io/nanobot-ai/nanobot:v0.0.67`  
**Active phat instances:** 7 containers + 7 shim containers = 14 running

#### Claude Code Local MCP Servers (running as host processes)
| Server | Process | Notes |
|--------|---------|-------|
| mcp-server-sqlite | Python (uv/uvx) | SQLite tool |
| mcp-server-memory | Node (npx) | Knowledge graph |
| mcp-server-sequential-thinking | Node (npx) | Planning tool |
| mcp-server-postgres | Node (npx) | Plane DB at localhost:5433 |
| mcp-server-filesystem | Node (npx) | Repo directory |
| plane_mcp_server.py | Python | Plane API integration |
| pipeline-monitor/server.py | Python | Pipeline health MCP |
| arr-orchestration/server.py | Python | Sonarr/Radarr/Prowlarr MCP |

**Total Claude Code MCP servers:** 8 local process-based

#### MCPO Proxy (port 8081)
Exposes 14 filesystem MCP tools as OpenAPI REST endpoints. Primarily used for HTTP-accessible tool bridging.

### Claude Desktop MCP Servers (~/mcp-servers/)
`arr-orchestration`, `brave`, `code-research`, `docs`, `health`, `home-assistant`, `pipeline-monitor`, `plex`, `remote`, `semgrep`, `strava`, `weather`

---

## SECTION 5: INFRASTRUCTURE SERVICES

### Monitoring & Observability Stack

| Service | Port | Status | Notes |
|---------|------|--------|-------|
| Grafana | 3030 | ✅ HTTP 200 | 10.4.2, 43MB |
| VictoriaMetrics | 8428 | ✅ healthy | v1.99.0, 36,189 active series, 79 MB |
| VMAgent | 8429 | ✅ running | scraping node-exporter + Docker metrics |
| Uptime Kuma | 3033 | ✅ healthy | 112 MB |
| Node Exporter | 9100 | ✅ running | 13 MB |

### Phase 12: Zabbix 7.4 (newly deployed)

| Container | Image | Status |
|-----------|-------|--------|
| zabbix-postgres | timescale/timescaledb:latest-pg16 | ✅ healthy |
| zabbix-server | zabbix/zabbix-server-pgsql:alpine-7.4-latest | ✅ up 26m |
| zabbix-web | zabbix/zabbix-web-nginx-pgsql:alpine-7.4-latest | ✅ healthy |
| zabbix-agent | zabbix/zabbix-agent:alpine-7.4-latest | ✅ up 26m |

**Ports:** 10051 (server), 10080 (web HTTP), 10443 (web HTTPS)  
**DB:** TimescaleDB on pg16 (~185 MB)  
**Network:** zabbix-net (isolated)  
**Documentation:** 7 runbook files in docs/zabbix/

### Ollama (Native Host Process)

| Model | Size |
|-------|------|
| nomic-embed-text:latest | 0.3 GB |
| qwen2.5-coder:7b | 4.7 GB |
| qwen2.5-coder:14b | 9.0 GB |
| deepseek-coder-v2:latest | 8.9 GB |
| devstral:latest | 14.3 GB |
| qwen2.5-coder:32b | 19.9 GB |

**Total model storage:** ~57.1 GB  
**Port:** 11434 — ✅ responding

### HashiCorp Vault

| Attribute | Value |
|-----------|-------|
| Version | 2.0.0 (community) |
| Port | 8200 |
| Status | ✅ initialized, unsealed |
| Storage | File (persistent, not dev mode) |
| Memory | 31 MB |
| CPU | ~6% |

### Media Automation Stack (Arr)

| Service | Port | Status | CPU | Memory |
|---------|------|--------|-----|--------|
| Sonarr | 8989 | ✅ healthy | 4.9% | 131 MB |
| Radarr | 7878 | ✅ healthy | 9.2% | 179 MB |
| Prowlarr | 9696 | ✅ healthy | 4.2% | 156 MB |
| Sportarr | 1867 | ✅ healthy | 5.2% | 213 MB |
| Plex (QNAP .201) | 32400 | ✅ HTTP 200 | — | — |

---

## SECTION 6: EXTERNAL INTEGRATIONS & NETWORK

### Network Topology

| Host | IP | Role | Status |
|------|----|------|--------|
| Mac Mini M5 (this host) | 192.168.10.145 | Primary compute | ✅ |
| OPNsense Router | 192.168.10.1 | Gateway/firewall | ✅ reachable |
| QNAP NAS | 192.168.10.201 | Storage + Plex | ✅ reachable |
| Home Assistant (physical) | 192.168.10.141 | Automation hub | ✅ HTTP 200 |

**DNS resolution:** `mac-mini.internal` ✅ | `qnap.internal` ✅  
**Network interfaces:** en0 (Ethernet primary), en1 (Wi-Fi), en5-en7 (USB), bridge0

### Home Assistant

- **Physical .141:** ✅ HTTP 200 at http://192.168.10.141:8123
- **Container (Mac Mini):** ✅ HTTP 200 at http://localhost:8123 (proxied or mirrored instance)

### OAuth / Token Status

| Integration | Token Present | Status |
|-------------|--------------|--------|
| Strava OAuth | ❌ Not found at ~/.config/strava | ⚠️ Configured in docker/.env only |
| GitHub PAT | ✅ In docker/.env (Obot) | ✅ Operational |
| Home Assistant token | ✅ In docker/.env | ✅ Operational |
| SSH keys | id_ed25519 (Apr 16), id_rsa (Apr 26) | ✅ |

---

## SECTION 7: DOCKER INFRASTRUCTURE

### Summary

| Metric | Value |
|--------|-------|
| Total containers | 51 |
| Running | 50 |
| Created (not started) | 1 (mcp-docker-remote) |
| Total images | 34 (41.19 GB) |
| Named volumes | 30+ |
| Anonymous volumes | 57 |
| Total volume storage | 5.52 GB |
| Reclaimable images | 40.91 GB (3 unused images) |

### Docker Networks

| Network | Driver | Purpose |
|---------|--------|---------|
| bridge | bridge | Default |
| obot-net | bridge | Obot + phat containers |
| docker_plane-net | bridge | Plane stack |
| observability | bridge | Grafana + VM + exporters |
| knowledge | bridge | AnythingLLM |
| zabbix-net | bridge | Zabbix stack |
| dashboard-net | bridge | Homarr + dashboards |
| control-center-net | bridge | LiteLLM + Open-WebUI |

### Named Docker Volumes

| Volume | Used By |
|--------|---------|
| anythingllm-storage | AnythingLLM knowledge base |
| docker_anythingllm-storage | AnythingLLM (alt mount) |
| docker_grafana-data | Grafana dashboards/config |
| docker_plane-db-data | Plane PostgreSQL data |
| docker_plane-logs | Plane application logs |
| docker_plane-minio-data | Plane file storage |
| docker_plane-redis-data | Plane session/cache |
| docker_uptime-data | Uptime Kuma history |
| docker_vm-data | VictoriaMetrics TSDB |
| docker_vmagent-data | VMAgent state |
| gateways_litellm-data | LiteLLM config/keys |
| ai-control_open-webui-data | Open-WebUI user data |
| ai-control_homarr-{config,data,icons} | Homarr |
| arr-stack_{sonarr,radarr,prowlarr,sportarr}-config | Arr configs |
| dashboards_homeassistant-config | HA container config |

### Docker Resource Usage (Top Consumers)

| Container | CPU % | Memory |
|-----------|-------|--------|
| open-webui | 35.7% | 392 MB (starting) |
| litellm-gateway | 31.4% | 42 MB (starting) |
| obot | 15.9% | 284 MB |
| docker-plane-api-1 | 7.7% | 110 MB |
| uptime-kuma | 6.8% | 112 MB |
| vault-server | 6.3% | 31 MB |
| vm (VictoriaMetrics) | 6.3% | 79 MB |
| docker-plane-worker-1 | 6.6% | 442 MB |
| zabbix-postgres | 5.7% | 185 MB |
| sportarr | 5.2% | 213 MB |
| mcp-docs-remote | 0.3% | 1.57 GB |
| mcp-filesystem-remote | 0.0% | 556 MB |

---

## SECTION 8: DOCUMENTATION INVENTORY

### docs/ — 23 markdown files across 8 directories

| File | Lines | Description |
|------|-------|-------------|
| docs/README.md | 74 | Status dashboard + quick links |
| docs/architecture/mcp-server-architecture.md | 116 | Network topology, server inventory |
| docs/performance/baseline-metrics.md | 80 | Response times, resource usage |
| docs/phase-9-completion.md | 96 | Phase 9 completion report |
| docs/phase-10-validation-report.md | 131 | Phase 10 validation |
| docs/phases/phase-1-10-summary.md | 102 | Full timeline phases 1-10 |
| docs/phases/phase-11-complete.md | 38 | Phase 11 (docs) complete |
| docs/runbooks/restart-services.md | 74 | Restart procedures |
| docs/runbooks/add-new-mcp-server.md | 131 | MCP onboarding guide |
| docs/runbooks/rotate-credentials.md | 86 | Credential rotation |
| docs/troubleshooting/common-issues.md | 184 | 8 documented issues |
| docs/adr/ADR-A-001.md | 19 | ADR template / first decision |
| docs/adr/ADR-A-006.md | 22 | ADR-A-006 |
| docs/adr/ADR-A-007.md | 32 | ADR-A-007 |
| docs/adr/ADR-A-008.md | 21 | ADR-A-008 |
| docs/adr/README.md | 43 | ADR index |
| docs/zabbix/initial-setup.md | 34 | Zabbix setup guide |
| docs/zabbix/phase-12-complete.md | 55 | Phase 12 completion |
| docs/zabbix/grafana-integration.md | 40 | Grafana→Zabbix integration |
| docs/zabbix/mac-mini-agent-setup.md | 48 | Agent configuration |
| docs/zabbix/opnsense-snmp-setup.md | 41 | OPNsense SNMP |
| docs/zabbix/qnap-snmp-setup.md | 33 | QNAP SNMP |
| docs/zabbix/security-checklist.md | 36 | Zabbix security |

**Note:** ADRs A-002 through A-005 are missing — gap in decision record history from pre-ADR era.

---

## SECTION 9: SYSTEM PERFORMANCE & RESOURCES

### Host System (Mac Mini M5)

| Metric | Value |
|--------|-------|
| Total RAM | 48 GB |
| RAM used | ~47 GB (macOS memory compression active) |
| RAM free | ~117 MB (compressed — normal macOS behavior) |
| CPU (snapshot) | 37.5% user, 14.8% sys, 47.6% idle |
| System load (1m/5m/15m) | 7.65 / 7.26 / 7.08 |
| Disk total | 926 GB |
| Disk used | 210 GB (24%) |
| Disk free | 695 GB |

### Ollama Model Storage: ~57 GB on disk

---

## SECTION 10: SECURITY STATUS

### macOS Firewall
✅ **Enabled** (`State = 1`) via `socketfilterfw`

### SSH Keys
- `~/.ssh/id_ed25519.pub` (100B, created Apr 16)
- `~/.ssh/id_rsa.pub` (742B, created Apr 26)

### Vault Security
- ✅ Initialized, unsealed
- ✅ `no-new-privileges: true`, `CapDrop: [ALL]`
- ✅ Persistent file storage (not dev mode)
- 5-of-3 Shamir unseal keys at `~/vault-init-keys.txt`

### Container Hardening
- `vault-server`: `[no-new-privileges:true]` + `CapDrop:[ALL]` ✅
- Per Phase 7 completion: `cap_drop` and `no-new-privileges` applied across hardened containers

### Known Exposure Surface (externally accessible ports on LAN)
20+ ports bound to `0.0.0.0` with no TLS or authentication layer for most services. All services currently LAN-only. No reverse proxy with TLS has been deployed (Traefik planned in Phase 12+).

---

## SECTION 11: SUMMARY DASHBOARD

### Container Health Summary
| Category | Total | Healthy | Starting | Warning |
|----------|-------|---------|----------|---------|
| AI services | 9 | 7 | 2 (open-webui, litellm) | 0 |
| Platform | 9 | 9 | 0 | 0 |
| Observability | 5 | 5 | 0 | 0 |
| Zabbix | 4 | 4 | 0 | 0 |
| Media/Arr | 5 | 5 | 0 | 0 |
| MCP remotes | 3 | 1 | 0 | 2 (filesystem false-neg, docker-remote not started) |
| Obot phat (NPX) | 14 | 14 | 0 | 0 |
| **TOTAL** | **51** | **45** | **2** | **2** |

### CMDB Health Checks (live validation at time of audit)
- 18/23 health URLs passing ✅
- 5 failing: `plane-api` (timeout at /), `plane-minio` (timeout), `ollama` (host process, check method), `litellm` (starting), `open-webui` (starting)

### Key Metrics
| Metric | Value |
|--------|-------|
| Total CMDB services | 32 |
| Docker containers running | 50 / 51 |
| MCP servers (Obot) | 10, 138 tools |
| MCP servers (Claude Code local) | 8 process-based |
| Ollama models | 6 (57 GB) |
| VictoriaMetrics active series | 36,189 |
| Docker total storage | 41 GB images + 5.5 GB volumes |
| Repository size | 1.3 GB (822 .py, 1172 .json, 65 .sh) |
| Documentation files | 23 markdown files |
| System uptime | 4 days |

### Gap Analysis (Critical Items)

| Priority | Gap | Impact |
|----------|-----|--------|
| P0 | `docs/PLATFORM_OVERVIEW.md` missing (CLAUDE.md references it) | New sessions start with broken context |
| P0 | `mcp-filesystem-remote` healthcheck uses `curl` (not in image) | False unhealthy; will alert in Zabbix |
| P1 | Strava OAuth token auto-refresh not implemented | Auth fails every ~6h |
| P1 | ADRs A-002 to A-005 missing | Gap in decision record history |
| P1 | Service registry missing: Zabbix (4 containers), mcp remote servers (2), openhands | 23 undocumented containers in CMDB |
| P2 | No TLS/reverse proxy | 20+ ports LAN-exposed without HTTPS |
| P2 | mcp-docs-remote using 1.57 GB RAM | Largest container — may need memory limit |
| P3 | main branch 15 commits ahead of origin (not pushed) | Unpublished work |
