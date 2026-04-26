# Platform Overview: Integrated AI Platform

**Last Updated:** 2026-04-25  
**Status:** Operational — 65/601 roadmap items complete (10.8%)

---

## What This Is

A local-first AI operating system and control plane running on a Mac Mini M5. It provides autonomous code execution, infrastructure monitoring, media management, and project tracking across a homelab network.

## Hardware

| Node | Role | Spec | IP |
|------|------|------|----|
| Mac Mini M5 | Orchestration (current) | Apple M5 / 48 GB RAM | 192.168.10.145 |
| Mac Studio M3 | Compute / inference (future) | Apple M3 / 96 GB RAM | 192.168.10.202 |
| QNAP NAS | Storage | 23.4 TB | 192.168.10.201 |

## Services — What's Running

| Service | URL | Purpose |
|---------|-----|---------|
| Plane CE | http://localhost:3001 | Project management / roadmap |
| Plane API | http://localhost:8000 | Django REST API |
| Ollama | http://localhost:11434 | Local LLM inference |
| OpenHands | http://localhost:3000 | AI coding agent |
| Grafana | http://localhost:3030 | Metrics dashboards |
| VictoriaMetrics | http://localhost:8428 | Metrics storage |
| Uptime Kuma | http://localhost:3033 | Service uptime monitoring |
| Zabbix Web | http://localhost:10080 | Infrastructure monitoring |
| AI Dashboard | http://localhost:8080 | Platform control panel (**must be started manually**) |

## Local LLM Models (Ollama)

| Model | Size | Use |
|-------|------|-----|
| qwen2.5-coder:32b | 19.9 GB | Review / thorough tasks |
| devstral:latest | 14.3 GB | General coding |
| deepseek-coder-v2 | 8.9 GB | Harder tasks |
| qwen2.5-coder:14b | 9.0 GB | Default balanced |
| qwen2.5-coder:7b | 4.7 GB | Fast / lightweight |

## Core Subsystems

**RAG Pipeline** — Progressive retrieval stages (RAG1→RAG4→RAG6) that select relevant code context before any modification. RAG4 uses entity-aware reranking: 28.6% → 57.1% bounded task coverage.

**Executor Abstraction** — All code changes route through `framework/code_executor.py`: ClaudeCodeExecutor (primary) or AiderExecutor (local Ollama fallback). Current success rate: 54.4% (154/283 runs).

**Autonomous Executor** — `bin/auto_execute_roadmap.py` processes roadmap items end-to-end: parse → decompose → retrieve context → execute → validate → commit.

**Roadmap** — 601 items in `docs/roadmap/ITEMS/`. 65 complete, 459 accepted (not started), 55 in planning, 15 in progress.

## Key Paths

```
~/repos/integrated-ai-platform/   — repo root
  bin/                            — executables and stage probes
  framework/                      — core runtime (16 importable modules)
  docs/roadmap/ITEMS/             — 601 roadmap items (canonical truth)
  artifacts/                      — run outputs, logs, metrics
  docker/                         — compose stacks
  web/dashboard/                  — dashboard server and frontend
  config/                         — per-node and system configuration
```

## Navigation

| Question | Document |
|----------|----------|
| How do I start/stop services? | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| Something is broken | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| How does it work? | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Where to continue development | [HANDOFF_GUIDE.md](HANDOFF_GUIDE.md) |
