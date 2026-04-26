# Integrated AI Platform — Master Guide

## 1. Quick Start

### Access URLs

| Service | URL | Notes |
|---|---|---|
| Dashboard | http://localhost:8080 | Main control panel (15 tabs + NOC) |
| Plane CE | http://localhost:3001 | Project management / roadmap (603 items) |
| Ollama API | http://localhost:11434 | Local LLM inference |
| **Zabbix NOC** | **http://localhost:10080** | **Enterprise network monitoring** |
| VictoriaMetrics | http://localhost:8428 | Time-series metrics DB |
| Grafana | http://localhost:3030 | Metrics visualisation |
| Uptime Kuma | http://localhost:3033 | Service uptime monitoring |

### Start Services

```bash
cd /Users/admin/repos/integrated-ai-platform

# Start Plane CE (project management)
docker compose -f docker/docker-compose-plane.yml up -d

# Start observability stack (VictoriaMetrics, Grafana, Uptime Kuma)
docker compose -f docker/observability-stack.yml up -d

# Start Zabbix NOC stack
docker compose -f docker/zabbix-stack.yml up -d

# Start dashboard
python3 web/dashboard/server.py &

# Verify Ollama is running
curl -s http://localhost:11434/api/tags | python3 -m json.tool
```

### Validate Environment

```bash
make check && make test-offline   # Syntax validation + 7 offline scenarios
```

---

## 2. Architecture Overview

The platform combines a local-first AI execution engine (Ollama + RAG pipeline) with a Plane CE project management backend and a web dashboard that ties everything together. Mac Mini (`admin@mac-mini.local`) hosts the dashboard and services; Mac Studio handles compute-intensive workloads.

```
  Browser
     |
  Dashboard (localhost:8080)
  web/dashboard/server.py
     |
     +--- Plane CE (localhost:3001) ---- Roadmap items (RM-* format)
     |    docker/docker-compose-plane.yml
     |
     +--- Ollama (localhost:11434) ----- Local code generation
     |    Default model: qwen2.5-coder:14b
     |
     +--- RAG Pipeline (stage_rag1-6) -- Code retrieval + planning
     |
     +--- Execution Managers ----------- Code modification
          stage3-7_manager.py
          framework/code_executor.py
```

---

## 3. Monitoring Stack

Two complementary monitoring layers — use each for what it's best at.

### Time-Series & Application Metrics

| Service | Port | Purpose | Compose file |
|---|---|---|---|
| VictoriaMetrics | 8428 | Lightweight Prometheus-compatible TSDB | `observability-stack.yml` |
| vmagent | 8429 | Metrics scraping agent | `observability-stack.yml` |
| Grafana | 3030 | Dashboards and alerting | `observability-stack.yml` |
| Uptime Kuma | 3033 | Service/URL uptime monitoring | `observability-stack.yml` |

### Network & Infrastructure Monitoring (Zabbix)

| Service | Port | Purpose | Compose file |
|---|---|---|---|
| Zabbix Web UI | 10080 | NOC dashboards, alerting, host overview | `zabbix-stack.yml` |
| Zabbix Server | 10051 | Data collection engine | `zabbix-stack.yml` |
| Zabbix Agent 2 | 10050 | Mac Mini host monitoring | `zabbix-stack.yml` |
| PostgreSQL (Zabbix) | — (internal) | Zabbix database | `zabbix-stack.yml` |

**Default Zabbix login:** `Admin` / `zabbix` — change on first login.

### Monitoring Division of Responsibility

| Use Case | Tool |
|---|---|
| App performance metrics, custom time-series | VictoriaMetrics + Grafana |
| Service uptime / HTTP health | Uptime Kuma |
| Network devices (SNMP) | Zabbix |
| NOC dashboard (host overview, problems) | Zabbix |
| Mac Mini system metrics | Zabbix Agent 2 |

### Adding Network Devices to Zabbix

1. Open http://localhost:10080 → **Configuration → Hosts → Create host**
2. Set **Host name** and **IP** (e.g. `OPNsense` / `192.168.10.1`)
3. Under **Templates** add the appropriate template:
   - OPNsense: `Template Net Network Generic Device SNMP`
   - QNAP NAS: `Template NAS QNAP SNMP`
   - Generic switch: `Template Net Generic Device SNMP`
   - macOS: `Template OS macOS`
4. Set **SNMP community** under **Macros** if needed (`{$SNMP_COMMUNITY}` = `public`)

### Widget Installation (initMAX)

```bash
CONTAINER=$(docker ps --filter name=zabbix-web --format "{{.ID}}")
docker exec -u root $CONTAINER sh -c "
  cd /usr/share/zabbix/modules/
  # Download and install widgets here — see Phase 2 in mission docs
"
```

Then: **Administration → General → Modules → Scan directory → Enable each widget**

---

## 4. Dashboard Tabs Reference

| Tab | Purpose |
|---|---|
| Home | Homepage portal / system overview |
| Overview | System health summary across all services |
| Roadmap | Browse and manage RM-* roadmap items |
| Analytics | Dependencies, priorities, burndown, velocity |
| Logs | Live execution and service logs |
| Media | Media pipeline status (Plex, Sonarr, etc.) |
| Infra | Infrastructure / homelab service status |
| Tools | Utility actions and one-off operations |
| Controls | Service start/stop controls |
| Security | Audit events and circuit breakers |
| Insights | AI recommendations and learning signals |
| Metrics | System performance metrics |
| Dev | AI engine status and code generation |
| Network | Network topology, device status, ISP metrics |
| Architecture | System data-flow diagram, aider worker controls |
| NOC | Zabbix embedded view + quick links to Problems, Hosts, Dashboards |

---

## 5. API Reference

### GET Endpoints

| Endpoint | Description |
|---|---|
| `/api/status` | Overall system status |
| `/api/health` | Health check |
| `/api/plane/stats` | Plane issue counts (total, done, in_progress, backlog) |
| `/api/plane/status` | Plane connectivity health |
| `/api/analytics/dependencies` | Roadmap dependency graph |
| `/api/analytics/priorities` | Ranked priority items |
| `/api/analytics/progress` | Burndown + velocity |
| `/api/analytics/effort` | Effort estimates |
| `/api/training/status` | Fine-tuning status |
| `/api/dev/status` | AI engine (Ollama) availability |
| `/api/executor/status` | Code executor availability |
| `/api/roadmap/search` | Search roadmap items |
| `/api/roadmap/item/<id>` | Fetch single roadmap item by ID |
| `/api/infra/status` | Infrastructure health |
| `/api/media/status` | Media pipeline status |
| `/api/metrics` | Platform performance metrics |
| `/api/recommendations` | AI-generated recommendations |
| `/api/circuit-breakers` | Circuit breaker states |
| `/api/selfheal/status` | Self-healing system status |

### POST Endpoints

| Endpoint | Description | Key Body Fields |
|---|---|---|
| `/api/development/generate` | AI code generation | `engine`, `prompt`, `create_tests`, `add_docs` |
| `/api/roadmap/ai-generate` | Translate description → structured roadmap item | `description` |
| `/api/roadmap/create-in-plane` | Create item in Plane + markdown backup | `title`, `description`, `priority` |
| `/api/roadmap/create` | Create markdown item only | `title`, `description` |
| `/api/roadmap/move` | Update item status | `item_id`, `status` |
| `/api/plane/sync-to` | Push markdown → Plane | — |
| `/api/plane/sync-from` | Pull Plane → markdown | — |
| `/api/train` | Start fine-tuning run | `model`, `dataset` |
| `/api/training/stop` | Stop active training | — |
| `/api/chat/message` | Send chat message to AI | `message`, `context` |
| `/api/selfheal/run` | Trigger self-healing | — |
| `/api/circuit-breakers/reset` | Reset circuit breakers | `service` |

---

## 6. Roadmap Management Workflow

Roadmap items live in `docs/roadmap/ITEMS/*.md` in `RM-*` format and are mirrored in Plane CE.

### View Roadmap

- Dashboard → Roadmap tab (browse, filter, search)
- Plane CE at http://localhost:3001 (canonical source of truth)
- `docs/roadmap/ITEMS/` (markdown backups, ~600 items)

### Sync Roadmap

```bash
# Pull latest from Plane → local markdown (do this first each session)
python3 bin/sync_plane_to_markdown.py

# Push local markdown → Plane (after local edits)
python3 bin/sync_roadmap_to_plane.py
```

### Create a New Roadmap Item

**From CLI (natural language):**
```bash
python3 bin/ai_requirement_translator.py --create --markdown "Your requirement description"
```

**From Dashboard:** Dev tab → AI Generate → enter description → Submit

**From API:**
```bash
curl -X POST http://localhost:8080/api/roadmap/create-in-plane \
  -H "Content-Type: application/json" \
  -d '{"title": "My Feature", "description": "Details...", "priority": "medium"}'

# Update status
curl -X POST http://localhost:8080/api/roadmap/move \
  -H "Content-Type: application/json" \
  -d '{"item_id": "RM-APIGW-001", "status": "In progress"}'
```

---

## 7. AI Development

### Code Generation

**From Dashboard:** Dev tab → enter prompt → Generate

**From API:**
```bash
curl -X POST http://localhost:8080/api/development/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Add error handling to foo()", "engine": "ollama", "create_tests": true}'
```

### RAG Pipeline (Code Retrieval + Planning)

```bash
# Check what files stage_rag4 selects for a query
python3 bin/stage_rag4_plan_probe.py --top 6 --max-targets 4 improve ExecutorFactory
make micro-lane-stage6        # Dry-run stage 6 orchestration planning
python3 bin/stage3_manager.py # Direct file-edit execution (stage 3)
```

### Aider (Local Model Code Editing)

```bash
make aider-fast    # qwen2.5-coder:14b — default, rapid iteration
make aider-hard    # deepseek-coder-v2 — harder tasks
make aider-smart   # 32B model — complex tasks

# Micro-edit with guardrails (clean working tree required)
make aider-micro-safe \
  AIDER_MICRO_MESSAGE="bin/foo.py::bar_function add guard clause" \
  AIDER_MICRO_FILES="bin/foo.py"
```

---

## 8. Plane CE Workflow

Plane CE at http://localhost:3001 is the authoritative source for roadmap state.

### MCP Server (AI Agent Access)

The MCP server gives AI agents structured access to Plane:

```bash
# Start MCP server
python3 mcp/plane_mcp_server.py
```

Available MCP tools: `list_issues`, `update_status`, `create_issue`, `get_issue`

### Docker Stack

```bash
# Start Plane
docker compose -f docker/docker-compose-plane.yml up -d

# Stop Plane
docker compose -f docker/docker-compose-plane.yml down

# Check logs
docker compose -f docker/docker-compose-plane.yml logs --tail=50
```

---

## 9. Key Scripts Cheatsheet

| Script | What it does |
|---|---|
| `web/dashboard/server.py` | Dashboard API server (port 8080) |
| `bin/sync_plane_to_markdown.py` | Pull Plane → local markdown files |
| `bin/sync_roadmap_to_plane.py` | Push local markdown → Plane (initial load) |
| `bin/ai_requirement_translator.py` | NL description → structured roadmap item |
| `mcp/plane_mcp_server.py` | MCP server for AI agent roadmap access |
| `bin/stage_rag4_plan_probe.py` | Test RAG retrieval for a query |
| `bin/stage3_manager.py` | Direct file-edit execution manager |
| `bin/stage7_manager.py` | Full autonomy execution manager |
| `bin/deploy_to_mac_mini.sh` | Deploy dashboard/services to Mac Mini |
| `bin/deploy_to_mac_studio.sh` | Deploy compute workloads to Mac Studio |
| `bin/cache_manager.py` | Manage response cache |

| `make check && make test-offline` | Full validation suite |
| `make workflow-mode-show` | Show current workflow mode |
| `make codex51-benchmark` | Run Codex 5.1 replacement benchmark |
| `make aider-bench-report` | Show recent aider performance |

---

## 10. Troubleshooting

**Dashboard not loading (http://localhost:8080)**
```bash
# Check if server is running
lsof -i :8080
# Restart
python3 web/dashboard/server.py &
```

**Plane CE unreachable (http://localhost:3001)**
```bash
docker compose -f docker/docker-compose-plane.yml ps
docker compose -f docker/docker-compose-plane.yml up -d
# Plane can take 30–60 seconds to fully start
```

**Ollama not responding / code generation fails**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags
# Restart Ollama if needed (macOS)
brew services restart ollama
# Pull default model if missing
ollama pull qwen2.5-coder:14b
```

**Roadmap sync fails (Plane API errors)**
- 429 rate limit: re-run after a few seconds
- Session auth expired: log in at http://localhost:3001 and retry
- See `docs/PLANE_SETUP.md` for API token configuration

**`make check` fails with syntax errors**
```bash
python3 -m py_compile path/to/file.py   # Check Python file
bash -n shell/script.sh                  # Check shell script
make quick                               # Quick targeted check
```

**ML/training deps not found (torch, transformers)**
- Lives in `~/training-env` venv only — activate: `source ~/training-env/bin/activate`
- See `docs/TRAINING.md` for full training architecture
