# Concrete Next Steps — 2026-04-25

Based on direct investigation of code, git history, containers, and live Plane data.
No speculation — every item below is grounded in evidence from today's audit.

---

## Immediate (Today / Next Session)

### 1. Add rate-limit retry to PlaneAPI (`framework/plane_connector.py`)
**Why:** Hit 429 three times today — vmagent recorded 1166 failed scrapes because the bulk sync hit Plane's rate limit and stuck in a bad state. The fix is one function: wrap all HTTP calls with exponential backoff on 429 + `Retry-After` header respect.
**File:** `framework/plane_connector.py`
**Size:** ~30 lines

### 2. Start Ollama container
**Why:** `domains/task_decomposer.py` has complete Ollama integration (`_call_ollama()` makes real HTTP calls) but no container is running. One command activates real AI task decomposition.
```bash
docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
docker exec ollama ollama pull qwen2.5-coder:14b
```
**Unblocks:** RM-833 (local translation), domains/task_decomposer.py, domains/code_generator.py

### 3. Backlog triage — cancel low-value bulk items
**Why:** 601 ITEMS includes AI-generated filler. A single commit added 300 items. Cancelling ~150 low-priority items (P3/P4 TESTING, DOCS, A11Y categories) reduces noise without losing anything strategic.
**How:** `python3 bin/sync_roadmap_to_plane.py --status "Backlog" --category TESTING` → review and batch-cancel via Plane web UI
**Frees:** Mental clarity, MCP search quality

---

## This Week

### 4. Wire `record_aider_task()` into aider execution path
**Why:** `framework/platform_metrics.py` was built today (RM-1181) but no code calls `record_aider_task()` yet. Wiring it into the aider execution wrapper gives live Grafana dashboards of task success/failure rates.
**File:** `bin/aider_worker.py` — add 3 lines around each task execution
**Result:** `aider_tasks_total` metric flows into VictoriaMetrics → Grafana

### 5. Execute RM-876: Self-healing code (automatic bug fixing)
**Why:** Ranked high priority Backlog. Strategic value 5/5. Architecture fit 4/5. Execution risk 3/5 (acceptable). The `framework/auto_fixer.py` exists — this item formalizes it into a proper self-healing loop.
**Files:** `framework/auto_fixer.py`, `bin/selfheal.py` (already started — it's running as a daemon)
**Check current state:** `cat framework/auto_fixer.py | head -50`

### 6. Execute RM-963: Database connection pooling (URGENT Backlog)
**Why:** Marked **urgent** priority. The Plane postgres container runs without connection pooling, which causes slow queries under load. Adding pgBouncer or SQLAlchemy pool settings is bounded and low-risk.
**Estimate:** 2-3 hours

### 7. Add Ollama scrape target to vmagent
**Why:** Once Ollama is running (Step 2), add it as a scrape target in `docker/vmagent-config/scrape.yml` to track inference latency and queue depth.
```yaml
- job_name: ollama
  static_configs:
    - targets: ['host.docker.internal:11434']
  metrics_path: /metrics
```

---

## Decision Points (Already Answered)

### Keep Plane? **YES**
Evidence: 41 code references, 8 integration files, bidirectional sync, MCP server active, 603 live issues. Not "just installed" — it is the project management backbone. Zero reason to migrate.

### Monitoring stack (Grafana + VictoriaMetrics + Uptime-Kuma)? **KEEP**
Evidence:
- 455 roadmap ITEMS reference monitoring/metrics (30 dedicated RM-MONITOR items)
- Total RAM: ~230MB for all 5 containers — negligible
- Just wired the Prometheus endpoint today (RM-1181 complete)
- vmagent now successfully scraping platform metrics
- Removing it would break the dashboard's `/metrics` → VictoriaMetrics pipeline we just built

### Ollama? **INTEGRATE IMMEDIATELY** (see Step 2)
Evidence: Complete code exists, zero container overhead is the only blocker. One `docker run` command.

### LoRA Training Pipeline? **PARK UNTIL MAC STUDIO**
Evidence: Requires GPU VRAM for 14GB model. Mac Mini can't run it. Pipeline code is complete and tested. Revisit when Mac Studio is the active compute host.

---

## Priority Matrix (What Moves the Codex 5.1 Needle)

| Item | Impact on Codex 5.1 Gate | Effort | Do Next? |
|------|--------------------------|--------|----------|
| Start Ollama | HIGH — activates real LLM task decomposition | 10 min | ✅ Yes |
| Plane rate-limit fix | MEDIUM — prevents toolchain disruption | 30 min | ✅ Yes |
| Wire aider metrics | HIGH — makes execution visible | 1 hour | ✅ Yes |
| RM-876 Self-healing | HIGH — core capability | 2-4 hours | ✅ Yes |
| Backlog triage | MEDIUM — reduces noise | 1 hour | ✅ Yes |
| RM-963 DB pooling | LOW for Codex 5.1, MEDIUM for stability | 2-3 hours | Next sprint |
| LoRA training | HIGH — final differentiation | Days (needs Mac Studio) | ❌ Park |
| Switch PM tool | ZERO — already working | Days | ❌ Never |
