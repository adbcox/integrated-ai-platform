# Research Findings: Architecture Decisions & Recommendations

**Date**: 2026-04-25  
**Scope**: Integrated AI Platform — homelab Mac Mini + Mac Studio stack  
**Method**: Codebase audit + architectural analysis

---

## 1. System Knowledge Integration

### Current State

The platform has CLAUDE.md (Claude Code context) and `config/system_truth.yaml` but no
mechanism to automatically load this context into aider runs or Ollama prompts. The aider
scripts in `bin/` invoke aider without a project-wide `.aider.conf.yml`, meaning each
invocation starts without shared context.

### Ranked Recommendations

| Approach | Complexity | Cost | Verdict |
|---|---|---|---|
| `.aider.conf.yml` | Low | Free | **Do first** — zero friction |
| MCP Instructions | Medium | Free | **Do second** — already have Plane MCP |
| System Prompts via inject | Low | Free | **Do third** — `bin/inject_system_context.py` |
| RAG + VectorDB | High | $$+ops | Skip for now — overkill for this repo size |

### Recommended Implementation

**Step 1 — `.aider.conf.yml`** (30 min, done once):

```yaml
# .aider.conf.yml — lives at repo root, auto-loaded by aider
model: ollama/qwen2.5-coder:14b
editor-model: ollama/qwen2.5-coder:7b
ollama-api-base: http://127.0.0.1:11434
no-auto-commits: true
auto-lint: true
read:
  - CLAUDE.md
  - config/system_truth.yaml
  - config/connectors.yaml
  - docs/progress-contract.md
  - docs/codex51-replacement-gate.md
lint-cmd:
  python: "python3 -m py_compile {file}"
  shell: "bash -n {file}"
```

This alone gives every aider invocation full repo context at zero cost.

**Step 2 — MCP system_knowledge resource** (2 hours):

Extend `mcp/plane_mcp_server.py` with a `get_system_context` tool that returns a structured
snapshot of the platform state: enabled connectors, active domains, current model routing,
recent escalations. Claude Code already has the Plane MCP registered; extending it keeps
everything in one server.

**Step 3 — `bin/inject_system_context.py`** (included below):

Builds a context block from config files and injects it as a comment header into prompts
sent to Ollama. Called from `aider_auto_route.py` before dispatching.

### What NOT to build

- Dedicated VectorDB (Chroma/Weaviate/Pinecone) for this codebase: the repo is ~200 files.
  BM25 in `stage_rag4` already covers retrieval. Add embeddings only when stage_rag4 recall
  drops below 60% on real tasks.
- LangChain/LlamaIndex wrappers: unnecessary abstraction layer over existing `inference_adapter.py`.

---

## 2. Observability Platform

### Current State

`framework/metrics_collector.py` is entirely placeholder:
- `cpu_usage = 0.5` (hardcoded)
- `memory_usage = 2.3` (hardcoded)
- No Prometheus endpoint, no log shipping, no trace collection

`framework/monitoring_system.py` and `framework/metrics_system.py` exist but are not wired
to any real backend. The dashboard (`web/dashboard/server.py`) has circuit breakers and TTL
caching but no structured metrics export.

### Top 3 Options Ranked

#### Option 1: VictoriaMetrics + Grafana (RECOMMENDED)

**Why**: Single binary VM replaces Prometheus + its storage. Consumes ~5x less RAM than
Prometheus for equivalent workloads. Grafana uses the same PromQL queries you'd write for
Prometheus. Best fit for a homelab running on a Mac Mini where RAM matters.

**Pros**: Single binary, instant startup, built-in retention config, PromQL-compatible  
**Cons**: Less community content than Prometheus, no native alertmanager (use VMAlert)

```yaml
# docker/observability-stack.yml (full version below)
services:
  victoriametrics:
    image: victoriametrics/victoria-metrics:v1.99.0
    ports: ["8428:8428"]
    volumes: ["vm-data:/storage"]
    command: -storageDataPath=/storage -retentionPeriod=90d

  grafana:
    image: grafana/grafana:10.4.0
    ports: ["3030:3000"]   # 3000 taken by Homepage
    environment:
      GF_AUTH_ANONYMOUS_ENABLED: "true"
      GF_AUTH_ANONYMOUS_ORG_ROLE: Viewer

  vmagent:
    image: victoriametrics/vmagent:v1.99.0
    # Scrapes the platform's /metrics endpoint + system stats
```

**Estimated setup**: 4 hours including dashboard provisioning

#### Option 2: Prometheus + Grafana + Loki (Standard)

**Why**: More tutorials, more pre-built dashboards, Loki for log aggregation.

**Pros**: Largest ecosystem, AlertManager included, Loki handles logs natively  
**Cons**: Prometheus alone uses 500MB+ RAM, Loki adds another 300MB. On Mac Mini this
matters. Storage management is more complex (WAL, compaction).

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.51.0
    ports: ["9090:9090"]
  loki:
    image: grafana/loki:2.9.0
    ports: ["3100:3100"]
  grafana:
    image: grafana/grafana:10.4.0
    ports: ["3030:3000"]
```

**Estimated setup**: 6 hours (Loki config is fiddly)

#### Option 3: OpenTelemetry Collector + Uptrace (Modern, Traces too)

**Why**: OpenTelemetry is the future standard. Uptrace is a self-hosted APM that receives
OTel traces, metrics, and logs in one UI.

**Pros**: One SDK covers traces + metrics + logs; great for distributed systems  
**Cons**: Heavier weight; Uptrace requires ClickHouse. Overkill until the platform has
more than one service making cross-service calls.

**Verdict**: Come back to this when stage7_manager runs distributed across Mac Mini/Studio.

### What to Instrument First

In priority order based on audit findings:

1. **`metrics_collector.py`** — replace placeholders with `psutil` calls (30 min)
2. **Aider task outcomes** — emit success/failure/duration to VictoriaMetrics from `aider_benchmark.py`
3. **Stage RAG hit rate** — `stage_rag4_plan_probe.py` already logs to `artifacts/stage_rag4/usage.jsonl`; add a scraper
4. **Circuit breaker state** — `framework/circuit_breaker.py` open/closed state
5. **Dashboard server** — add `/metrics` endpoint to `web/dashboard/server.py`

---

## 3. Missing Integrations Analysis

### Confirmed Gaps (High Value)

**A. Real Ollama integration in inference_adapter.py**  
`LocalHeuristicInferenceAdapter` and `ArtifactReplayInferenceAdapter` are not making real
inference calls. The worker runtime and stage managers use aider as the execution layer
instead. This means the `inference_adapter.py` abstraction is unused in production paths.

*Fix*: Wire `OllamaInferenceAdapter` that hits `http://127.0.0.1:11434/api/chat` directly.
The backend profiles in `framework/backend_profiles.py` suggest this was planned.

**B. metrics_collector.py → real system metrics**  
Replace hardcoded values with `psutil.cpu_percent()`, `psutil.virtual_memory().used`,
`psutil.disk_usage('/')`. Five lines of code.

**C. connectors enabled/disabled mismatch**  
`config/connectors.yaml` marks arr_stack as `enabled: true` but `config/system_truth.yaml`
marks it `enabled: false`. The domains/media.py connector talks to 192.168.10.201 (QNAP)
but the system_truth says media domain is disabled. This is a config split-brain issue.

*Fix*: Decide on a single source of truth (recommend `connectors.yaml`) and have
`system_truth.yaml` derive from it or remove the duplicate flag.

**D. No webhook/event ingestion path**  
Sonarr/Radarr support webhook notifications on download completion. There's no listener.
An event endpoint in `web/dashboard/server.py` could trigger rclone sync or dashboard
refresh automatically instead of polling.

**E. No unified secrets management**  
Credentials live in `docker/.env` (partially populated), env vars at runtime, and
hardcoded defaults in individual scripts. A single `SecretsLoader` that reads `.env` +
env vars with fallback priority would eliminate the duplicate credential definitions.

### Low-Value / Avoid

| Tool | Reason to Skip |
|---|---|
| LangChain | Adds abstraction over `inference_adapter.py` that's already there |
| Pinecone | Cloud-only cost, BM25+stage_rag4 handles this repo's scale |
| n8n | Automation platform that duplicates what `bin/` scripts already do |
| Airflow | DAG scheduler for batch pipelines — the scheduler.py already exists |
| Kafka | Event streaming overkill until >10 services are emitting events |

### Medium-Value Additions Worth Considering

- **Healthchecks.io or Uptime Kuma**: dead-simple uptime monitor for the dashboard,
  Plex, OPNsense, and Plane. Single Docker container, 5 min setup.
- **Ntfy.sh** (self-hosted): push notifications to phone when aider tasks complete or
  circuit breakers trip. `framework/slack_notifier.py` exists; Ntfy is lighter.
- **Rclone monitoring**: the seedbox→QNAP sync has no visibility. A simple cron job that
  runs `rclone check` and logs to the dashboard would close this gap.

---

## 4. OpenClaw Assessment

**What it is**: "OpenClaw" does not correspond to a recognized open-source project in the
AI/ML or DevOps ecosystem as of the knowledge cutoff (Aug 2025). The closest candidates:

- **OpenHands** (formerly OpenDevin): already in your OSS wave (`bin/oss_wave_openhands.sh`)
  — this is the AI coding agent platform you're already evaluating.
- **Claw Machine** / claw-based UI frameworks: unrelated frontend tooling.
- **CLAW (Crawl-Link-Analyze-Write)**: a research automation pattern, not a packaged tool.

**Assessment**: If "OpenClaw" was referenced in a specific context (article, conference, PR),
share the source and this section can be updated. Based on current information, there is no
established project by this name that fits the integrated AI platform use case.

**Closest alternative that DOES fit**: **OpenHands** (already in OSS wave) fills the
"autonomous AI coding agent" niche. Current validation scripts (`bin/oss_wave_openhands_validate.py`)
suggest it's being evaluated but not yet in production. The primary blocker per the OSS wave
script is sandboxing stability for local execution.

---

## 5. Actionable Next Steps

Priority-ordered. Each item is independently executable.

### Week 1 — Zero-friction wins (total: ~8 hours)

| # | Action | File | Effort | Dependency |
|---|---|---|---|---|
| 1 | Create `.aider.conf.yml` at repo root | `.aider.conf.yml` | 30 min | None |
| 2 | Fix `metrics_collector.py` placeholders | `framework/metrics_collector.py` | 1 hr | `pip install psutil` |
| 3 | Add `enabled` reconciliation to connectors | `config/system_truth.yaml` | 30 min | None |
| 4 | Wire `SecretsLoader` from `.env` + env vars | `framework/config_system.py` | 2 hr | None |
| 5 | Add `/metrics` endpoint to dashboard server | `web/dashboard/server.py` | 2 hr | psutil |

### Week 2 — Observability (total: ~10 hours)

| # | Action | File | Effort | Dependency |
|---|---|---|---|---|
| 6 | Deploy VictoriaMetrics + Grafana | `docker/observability-stack.yml` | 4 hr | Docker |
| 7 | Wire aider benchmarks to VM push | `bin/aider_benchmark.py` | 2 hr | Step 6 |
| 8 | stage_rag4 usage.jsonl → metrics scraper | `bin/metric_reporter.py` | 2 hr | Step 6 |
| 9 | Deploy Uptime Kuma for service health | new docker-compose entry | 1 hr | Docker |
| 10 | Wire Ntfy for task completion alerts | `framework/slack_notifier.py` | 1 hr | Self-hosted ntfy |

### Week 3 — Integration completeness (total: ~12 hours)

| # | Action | File | Effort | Dependency |
|---|---|---|---|---|
| 11 | `OllamaInferenceAdapter` real implementation | `framework/inference_adapter.py` | 4 hr | Ollama running |
| 12 | Sonarr/Radarr webhook receiver endpoint | `web/dashboard/server.py` | 3 hr | None |
| 13 | MCP system_context tool (extend Plane MCP) | `mcp/plane_mcp_server.py` | 3 hr | None |
| 14 | Rclone sync status in seedbox connector | `connectors/seedbox.py` | 2 hr | rclone installed |

### Month 2 — Milestone gate (Codex 5.1 replacement)

- Full pipeline execution: stage_rag4 → stage6_manager → real file modification
- Semantic generation at ≥90% primary rate on 24-task benchmark
- Observability proving local models outperform Codex on bounded tasks

---

*Generated by codebase audit. Update this document after each major architecture change.*
