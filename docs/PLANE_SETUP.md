# Plane Setup Guide

> **100% Open Source** — Plane CE + PostgreSQL + Redis + MinIO. Zero AWS/cloud dependencies.
> All images: `makeplane/plane-*:stable`, `postgres:15-alpine`, `redis:7.2-alpine`, `minio/minio:latest`

Plane is the open-source project management UI for this repository's roadmap.
**Plane CE is the single source of truth** for roadmap status. Markdown files
serve as the git-trackable backup; they are written by the sync scripts, not
edited by hand.

## Data Flow Architecture

```
                    ┌─────────────────┐
                    │   PLANE CE      │  ← SINGLE SOURCE OF TRUTH
                    │ localhost:3001  │     600 issues, Kanban/Gantt/Cycles
                    └────────┬────────┘
                             │
         ┌───────────────────┼──────────────────┐
         ↓                   ↓                  ↓
   Dashboard             MCP Server         Analytics
   (iframe embed)        (AI access)        (read-only queries)
   /api/plane/stats      plane_mcp_server   dependency_analyzer
   /api/plane/status     update_status()    priority_engine
                                            progress_analytics
         │
         ↓ (one-way backup only)
   docs/roadmap/ITEMS/*.md
   bin/sync_plane_to_markdown.py
   git commit (version history)
```

**Day-to-day workflow:**
1. Edit issues in Plane UI at http://localhost:3001
2. AI agents update statuses via MCP (`update_status` tool)
3. Run `python3 bin/sync_plane_to_markdown.py` to write git-trackable backup
4. Do NOT edit markdown files directly — they are overwritten on sync

**Why Plane is primary:**
- Built-in Kanban, List, Calendar, Gantt, Cycles, Modules views
- Better visualization than any custom-built board
- MCP server gives AI agents direct structured access
- Dashboard embeds Plane via iframe — no duplicate UI

## Architecture (legacy bi-directional view)

```
docs/roadmap/ITEMS/*.md  ←─────────────────────────────┐
          ↑  (canonical)                                 │
          │  bin/sync_plane_to_markdown.py               │
          │  (pull changes, git commit)                  │
          ↓                                              │
    Plane Issues          ←── AI agents via MCP ─── Claude Code / Claude.ai
    localhost:3001             mcp/plane_mcp_server.py
          ↑
          │  bin/sync_roadmap_to_plane.py
          │  (push all 600 items on setup)
          │
   Dashboard (/roadmap tab)
   "Push to Plane" / "Pull from Plane" buttons
```

## Phase 1: Deploy Plane

### Ports

| Service | URL | Notes |
|---------|-----|-------|
| Plane Web UI | http://localhost:3001 | nginx serving pre-built React app |
| Plane API | http://localhost:8000 | Django/Gunicorn, `{"status":"OK"}` |
| MinIO S3 API | http://localhost:9000 | Self-hosted object storage |
| MinIO Console | http://localhost:9001 | Web UI for file storage admin |

### Start Plane

```bash
cd /Users/admin/repos/integrated-ai-platform

# Plane is already running. To start fresh:
docker compose -f docker/docker-compose-plane.yml up -d

# Watch migration (completes in ~30s)
docker logs -f docker-plane-migrate-1

# Verify all services
docker compose -f docker/docker-compose-plane.yml ps
```

Plane web UI is available at **http://localhost:3001** when `plane-web` shows `(healthy)`.

### Automated first-time setup (recommended)

Skip the browser entirely — one command does everything:

```bash
cd /Users/admin/repos/integrated-ai-platform
python3 bin/setup_plane_automated.py
```

This script:
1. Waits for the API to be ready
2. Sets `instance.is_setup_done = True` via docker exec (required before sign-up)
3. Creates the admin user via Django ORM (avoids CSRF complexity)
4. Signs in to get a session cookie
5. Creates a permanent API token (`plane_api_*` format)
6. Creates workspace `iap` + project `Roadmap`
7. Writes `PLANE_API_TOKEN` and `PLANE_PROJECT_ID` to `docker/.env`
8. Runs `configure_plane_agile.py` (states, labels, sprints, modules)
9. Runs `sync_roadmap_to_plane.py` — loads all 600 roadmap items (~15 min, rate-limited at 60/min)

**Options:**
```bash
python3 bin/setup_plane_automated.py --skip-sync   # skip the 600-item sync
python3 bin/setup_plane_automated.py --dry-run     # no writes
python3 bin/setup_plane_automated.py --skip-instance-setup  # if already done
```

### Manual first-time setup (alternative)

1. Open http://localhost:3001
2. Click **Get Started** → enter your email and a password
3. Create workspace with slug **`iap`** (or change `PLANE_WORKSPACE` in docker/.env)
4. Create a project named **Roadmap**
5. Note the project UUID from the URL: `/iap/projects/{UUID}/issues/`

### Get an API token (manual)

1. Click your avatar (top-right) → **Profile**
2. **API Tokens** → **Add Token**
3. Name it `dashboard-sync`, no expiry
4. Copy the token

### Add credentials to docker/.env

```bash
# Edit docker/.env
PLANE_API_TOKEN=your-token-here
PLANE_PROJECT_ID=your-project-uuid-here
PLANE_WORKSPACE=iap
```

## Phase 2: Configure Agile + PMP Workflow

After getting your API token and project ID (see First-time account setup above):

```bash
export PLANE_URL=http://localhost:8000
export PLANE_API_TOKEN=your-token
export PLANE_WORKSPACE=iap
export PLANE_PROJECT_ID=your-project-uuid

# Set up Agile workflow states + PMP labels + sprint cycles + epic modules
python3 bin/configure_plane_agile.py

# See what was created
python3 bin/configure_plane_agile.py --show
```

This creates:
- **States:** Backlog → Ready → In Progress → In Review → Testing → Done / Cancelled / Deferred
- **Labels:** feature, bug, enhancement, technical-debt, spike, quick-win, blocked, risk, dependency, milestone, + 10 tech category labels
- **Cycles (Sprints):** 6 × 2-week sprints starting from current Monday
- **Modules (Epics):** Core Platform, API & Integrations, Media Pipeline, Developer Tools, Data & Storage, Security & Ops, Testing & QA, Documentation

## Phase 3: Sync Roadmap to Plane

### Initial sync (one-time setup)

```bash
# Set env vars for the session
export PLANE_URL=http://localhost:8000
export PLANE_API_TOKEN=your-token
export PLANE_WORKSPACE=iap
export PLANE_PROJECT_ID=your-project-uuid

# 1. Create states and category labels
python3 bin/sync_roadmap_to_plane.py --init

# 2. Dry run — see what would be created
python3 bin/sync_roadmap_to_plane.py --dry-run

# 3. Full sync (all 600 items, takes ~3 minutes)
python3 bin/sync_roadmap_to_plane.py
```

Expected output:
```
Loaded 600 roadmap items from docs/roadmap/ITEMS
Syncing 600 items to Plane (dry_run=False)...
  [1/600] ✚ RM-A11Y-001 created
  [2/600] ✚ RM-A11Y-002 created
  ...
Done in 187.3s — created=600 updated=0 errors=0 skipped=0
```

### Ongoing: sync individual items

```bash
# Sync a single item after editing its markdown
python3 bin/sync_roadmap_to_plane.py --id RM-API-100

# Sync all "In progress" items
python3 bin/sync_roadmap_to_plane.py --status "In progress"
```

## Phase 4: AI Requirement Translator (Ollama)

Convert natural language into fully structured roadmap items using local Ollama (zero cloud):

```bash
# Translate a single requirement
python3 bin/ai_requirement_translator.py "We need rate limiting on the API gateway with per-IP and per-token limits"

# Translate and create in Plane + write markdown file
python3 bin/ai_requirement_translator.py --create --markdown \
  "Build a webhook system for notifying external services when roadmap items complete"

# Interactive mode (great for brainstorming)
python3 bin/ai_requirement_translator.py --interactive

# Batch translate from a file
python3 bin/ai_requirement_translator.py --file my_requirements.txt --create --markdown

# Use a different Ollama model
python3 bin/ai_requirement_translator.py --model llama3.2 "Add SAML SSO support"
```

Each translation produces:
- RM-* ID suggestion (scans existing items to avoid conflicts)
- Title (imperative verb, max 80 chars)
- Category, Type, Priority, LOE, Story Points (Fibonacci)
- Strategic value / Architecture fit / Execution risk scores (1-5)
- Success criteria (measurable outcomes)
- Subtasks (3-6 concrete implementation steps)
- Business value, Risk level
- Optional: creates Plane issue + writes markdown file

## Phase 5: Pull Changes from Plane → Markdown

When you (or an AI agent) updates a status in Plane, sync it back:

```bash
# Check what changed (no write)
python3 bin/sync_plane_to_markdown.py --dry-run

# Apply changes + git commit
python3 bin/sync_plane_to_markdown.py

# Watch mode: auto-sync every 5 minutes
python3 bin/sync_plane_to_markdown.py --watch 300
```

The sync script will:
1. Fetch all Plane issues
2. Compare each issue's Plane state to the markdown Status field
3. Update any markdown files where status differs
4. Create a git commit: `sync: update N roadmap statuses from Plane`

## Phase 4: MCP Server (AI Agent Access)

### Register with Claude Code

Add to `~/.claude.json` (or run `claude mcp add`):

```json
{
  "mcpServers": {
    "plane-roadmap": {
      "command": "python3",
      "args": ["/Users/admin/repos/integrated-ai-platform/mcp/plane_mcp_server.py"],
      "env": {
        "PLANE_URL": "http://localhost:8000",
        "PLANE_API_TOKEN": "your-token-here",
        "PLANE_WORKSPACE": "iap",
        "PLANE_PROJECT_ID": "your-project-uuid"
      }
    }
  }
}
```

Or via CLI:
```bash
claude mcp add plane-roadmap \
  --command python3 \
  --args /Users/admin/repos/integrated-ai-platform/mcp/plane_mcp_server.py \
  --env PLANE_URL=http://localhost:8000 \
  --env PLANE_API_TOKEN=your-token \
  --env PLANE_WORKSPACE=iap \
  --env PLANE_PROJECT_ID=your-uuid
```

### Register with Claude.ai

1. Go to Settings → Integrations → MCP Servers
2. Add server:
   - **Name:** `plane-roadmap`
   - **Command:** `python3 /Users/admin/repos/integrated-ai-platform/mcp/plane_mcp_server.py`
   - **Working directory:** `/Users/admin/repos/integrated-ai-platform`
   - **Environment:** paste the env vars above

### Available MCP tools

| Tool | Description |
|------|-------------|
| `list_issues` | List roadmap issues with optional status/category filters |
| `get_issue` | Get full details for one issue by RM-* ID |
| `create_issue` | Create a new roadmap item in Plane |
| `update_status` | Change issue status (also syncs markdown) |
| `search_issues` | Full-text search across all issues |
| `get_stats` | Summary counts by state and top categories |
| `list_states` | Available workflow states |
| `list_categories` | Available category labels |

### Example AI agent queries

```
"Show me all In Progress roadmap items"
→ list_issues(status="In Progress")

"Find roadmap items related to authentication"
→ search_issues(query="authentication")

"Mark RM-API-100 as completed"
→ update_status(id="RM-API-100", status="Completed")

"How many items are in each state?"
→ get_stats()

"What are the top categories by item count?"
→ get_stats()  # returns top_categories breakdown
```

## Dashboard Integration

The **Roadmap** tab shows:
- **Plane status indicator** (green dot when reachable)
- **Push to Plane** button — syncs markdown → Plane
- **Pull from Plane** button — syncs Plane → markdown
- **Open Plane ↗** button — opens Plane UI in new tab
- **Last sync** timestamp

The dashboard also exposes:
- `GET /api/plane/status` — Plane health + issue counts
- `POST /api/plane/sync-to` — trigger markdown → Plane sync
- `POST /api/plane/sync-from` — trigger Plane → markdown sync

## Workflow

**Normal day-to-day:**
1. Open Plane at http://localhost:3001
2. Edit issue statuses, add comments, drag cards
3. Click "Pull from Plane" in dashboard (or run sync script)
4. Git shows new commits with updated markdown statuses

**AI agent workflow:**
1. Claude Code or Claude.ai calls `update_status` via MCP
2. Status updates both Plane and the markdown file atomically
3. No manual sync needed for single-item updates

**Bulk markdown edits (CI/executor):**
1. Executor modifies markdown files
2. Click "Push to Plane" in dashboard or run `sync_roadmap_to_plane.py`
3. Plane reflects the new statuses

## Troubleshooting

**Plane web UI blank / 502:**
```bash
docker compose -f docker/docker-compose-plane.yml logs plane-api | tail -30
# Wait for "Application startup complete" before opening browser
```

**API returns 401:**
- Token is wrong or expired — create a new one in Plane UI
- Token goes in `PLANE_API_TOKEN` in docker/.env

**Sync script: "PLANE_PROJECT_ID is not set":**
- Open Plane → click your project → copy UUID from URL
- Add `PLANE_PROJECT_ID=<uuid>` to docker/.env

**Items not appearing after sync:**
- Check the workspace slug matches `PLANE_WORKSPACE` in docker/.env
- Run `python3 bin/sync_roadmap_to_plane.py --init` to create states/labels first

**MCP server not found by Claude Code:**
```bash
# Test the server manually
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}' | python3 mcp/plane_mcp_server.py
```

## Stopping Plane

```bash
docker compose -f docker/docker-compose-plane.yml down

# To also remove all data (destructive!)
docker compose -f docker/docker-compose-plane.yml down -v
```

Data is stored in named Docker volumes (`plane-db-data`, `plane-redis-data`) and persists across restarts.
