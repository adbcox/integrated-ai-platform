# Project Management Tool Decision Matrix — 2026-04-25

## Current State: Plane CE

| Fact | Status |
|------|--------|
| Containers running | 7 (web, api, beat, worker, db, redis, minio) |
| RAM usage | ~1,033 MB total |
| Actually used in code | YES — 41 references, 8 files |
| Bidirectional sync with markdown | YES — sync_roadmap_to_plane.py / sync_plane_to_markdown.py |
| MCP server integration | YES — plane-roadmap MCP server active |
| Live issues in Plane | 603 (synced from 601 markdown ITEMS) |
| Last API interaction | Today (live query returned 603 issues) |
| **VERDICT** | **In active use. Integrated. Working.** |

---

## Requirements for This AI Orchestration Platform

| # | Requirement | Weight |
|---|-------------|--------|
| 1 | API-driven (for automation from scripts/MCP) | Critical |
| 2 | Stores task status, priority, state changes | Critical |
| 3 | Self-hosted, open-source | Critical |
| 4 | Bidirectional sync with markdown files | High |
| 5 | Roadmap item tracking with metadata | High |
| 6 | Fast enough for 600+ item queries | High |
| 7 | Low resource usage (Mac Mini, 8GB) | Medium |
| 8 | Integration with Ollama/LLMs | Nice-to-have |
| 9 | Sprint/cycle management | Nice-to-have |

---

## Tool Comparison

### Option A: Keep Plane CE ✅ RECOMMENDED

**Pros:**
- Already installed, configured, and synced (7 containers, 603 live issues)
- Modern, fast REST API — all automation scripts already written
- MCP server (`mcp__plane-roadmap__*`) works today
- Bidirectional markdown ↔ Plane sync fully implemented
- Lightweight compared to alternatives (~1GB RAM total)
- Active upstream development (makeplane/plane)
- Status cycles, priorities, labels, cycles all configured
- Zero migration cost

**Cons:**
- 7 containers vs 0 for pure markdown
- API rate limits hit during bulk operations (seen today: 1166 scrape failures)
- Plane CE occasionally lags behind Plane Cloud features

**Effort to keep:** ZERO (already running)
**Risk:** LOW

---

### Option B: OpenProject

**Pros:**
- Most comprehensive: Gantt, time tracking, Scrum, Kanban, Wiki, Forums
- Closest to Jira in feature depth
- Strong API

**Cons:**
- Much heavier: Ruby on Rails + Postgres + Nginx + Memcached (~2-3GB RAM)
- Migration: 603 issues would need re-import scripts (days of work)
- No existing integration in codebase
- Overkill for a single-developer AI platform

**Effort to switch:** HIGH (2-5 days migration + rewrite all scripts)
**Risk:** HIGH (breaks all existing automation)

---

### Option C: GitLab CE

**Pros:**
- Git + CI/CD + Issues + Milestones in one tool
- Already use Git; issues can track roadmap items
- Powerful built-in CI pipelines for make check / test runs

**Cons:**
- Extremely heavy: 4-6GB RAM minimum
- Issues not designed for structured metadata (no LoE, strategic value fields)
- Would lose all Plane-specific metadata without custom labels hack
- Different paradigm — issues tied to git events, not AI task orchestration
- No Python library or MCP equivalent written yet

**Effort to switch:** MEDIUM-HIGH (3-4 days migration + rewrite)
**Risk:** HIGH (paradigm mismatch)

---

### Option D: Taiga.io

**Pros:**
- Agile-focused (sprints, user stories, epics)
- Clean modern UI
- Good REST API

**Cons:**
- Sprints/user story paradigm doesn't match AI task orchestration
- No existing integration in codebase
- Self-hosted setup complexity similar to Plane
- Less active development than Plane

**Effort to switch:** HIGH
**Risk:** MEDIUM

---

### Option E: Redmine

**Pros:**
- Battle-tested, stable (20+ years)
- Very customizable with plugins

**Cons:**
- Old Ruby on Rails UI — not modern
- No structured metadata support without plugins
- Heavier than Plane
- API is CRUD-only, not designed for automation workflows

**Effort to switch:** HIGH
**Risk:** MEDIUM

---

### Option F: Pure Markdown (Remove Plane)

**Pros:**
- Zero container overhead
- Git-native — every status change is a commit
- No rate limits
- Zero maintenance

**Cons:**
- No web UI for status visualization
- Manual tracking only
- Lose MCP server integration (the plane-roadmap tools)
- Lose Plane's filtering, kanban board, cycle management
- The roadmap dashboard at localhost:3001 becomes unusable
- Would need to rewrite `bin/sync_roadmap_to_plane.py` as a local file processor

**Effort to switch:** LOW (just stop containers)
**Risk:** LOW operationally, but loses significant capability

---

## Decision Matrix Scoring

| Criterion (weight) | Plane CE | OpenProject | GitLab | Pure Markdown |
|--------------------|----------|-------------|--------|---------------|
| API-driven (10) | 10 | 8 | 7 | 0 |
| Task status/state (10) | 10 | 10 | 7 | 5 |
| Self-hosted OSS (10) | 10 | 10 | 10 | 10 |
| Markdown sync (8) | 9 | 3 | 3 | 10 |
| Metadata richness (8) | 9 | 8 | 5 | 9 |
| 600+ item speed (6) | 8 | 7 | 8 | 10 |
| RAM on Mac Mini (6) | 8 | 4 | 2 | 10 |
| Migration cost (10) | 10 | 2 | 3 | 7 |
| **Weighted Total** | **524** | **346** | **294** | **404** |

---

## Recommendation

**KEEP PLANE CE.**

The investigation shows it is not "just installed" — it is integrated:
- Scripts call the API today
- MCP server queries it live  
- Markdown ↔ Plane sync is bidirectional and tested
- 603 real issues tracked with priorities and states

The only scenario to reconsider: if Mac Mini RAM becomes the binding constraint (currently 1GB / 7.7GB used by Plane — not a problem).

The rate-limit issue is addressable: add exponential backoff in `plane_connector.py` and avoid bulk-paginating all 603 issues in rapid succession (the root cause of today's 429s).

---

## Action Items from This Decision

1. **Stay on Plane** — no migration needed
2. **Fix rate limiting** — add `Retry-After` header handling in `framework/plane_connector.py`
3. **Trim the backlog** — 601 ITEMS is AI-inflated; review and cancel ~200 low-value items
4. **Start Ollama** — `docker run -d -p 11434:11434 ollama/ollama` enables task_decomposer live calls
5. **Focus execution** — use `config/roadmap_execution_order.yaml` to pick next actionable item
