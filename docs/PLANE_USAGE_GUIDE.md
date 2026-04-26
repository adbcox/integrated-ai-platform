# Plane CE Usage Guide

Plane CE is the agile project management frontend for the IAP roadmap. It runs locally and syncs bidirectionally with `docs/roadmap/ITEMS/*.md`.

## Quick Start

### First-time setup (zero manual steps)

```sh
# 1. Start Plane containers
docker compose -f docker/docker-compose-plane.yml up -d

# 2. Run automated setup
bash bin/setup_plane_automated.sh

# 3. Open browser
open http://localhost:3001
# Login: admin@local.dev / Admin1234!
```

The setup script creates the admin account, workspace, project, all agile states/labels/sprints, and syncs all 600 roadmap items automatically.

### Prerequisites

- Docker running with Plane containers healthy (`docker ps | grep plane`)
- `docker/.env` with `PLANE_ADMIN_EMAIL` and `PLANE_ADMIN_PASSWORD` set
- Python 3.9+ in PATH

---

## Architecture

```
docs/roadmap/ITEMS/*.md  ←→  sync_roadmap_to_plane.py
                         ←→  sync_plane_to_markdown.py
                              ↓
                         Plane API (localhost:8000)
                              ↓
                         Plane UI  (localhost:3001)
```

**Plane is the working surface. Markdown is the source of truth.**  
Status changes made in Plane can be synced back to markdown. New items should be created in markdown first, then synced to Plane.

---

## Syncing Roadmap → Plane

### Full sync (all 600 items)

```sh
python3 bin/sync_roadmap_to_plane.py
```

### Dry run (preview changes)

```sh
python3 bin/sync_roadmap_to_plane.py --dry-run
```

### Sync a single item

```sh
python3 bin/sync_roadmap_to_plane.py --id RM-API-100
```

### Filter by status or category

```sh
python3 bin/sync_roadmap_to_plane.py --status "In progress"
python3 bin/sync_roadmap_to_plane.py --category API
python3 bin/sync_roadmap_to_plane.py --category MEDIA --verbose
```

---

## Syncing Plane → Markdown

When a status changes in the Plane UI (e.g. move card to "Done"), sync it back:

```sh
# Preview what would change
python3 bin/sync_plane_to_markdown.py --dry-run

# Apply changes and auto-commit
python3 bin/sync_plane_to_markdown.py

# Watch mode (poll every 60s)
python3 bin/sync_plane_to_markdown.py --watch 60

# Single item
python3 bin/sync_plane_to_markdown.py --id RM-API-100
```

**State mapping:**

| Plane state  | Markdown status |
|-------------|-----------------|
| Backlog      | Accepted        |
| In Progress  | In progress     |
| Done         | Completed       |
| Cancelled    | Retired         |

---

## AI Requirement Translator

Translate natural language requirements into fully structured roadmap items using a local Ollama model.

### Single requirement

```sh
python3 bin/ai_requirement_translator.py "Add OAuth2 login with GitHub and Google"
```

### Translate and create in Plane

```sh
python3 bin/ai_requirement_translator.py --create "Add rate limiting to the API gateway"
```

### Translate and write as markdown file

```sh
python3 bin/ai_requirement_translator.py --markdown "Add dark mode to dashboard"
```

### Translate, write markdown, AND create in Plane

```sh
python3 bin/ai_requirement_translator.py --create --markdown "Implement webhook notifications"
```

### Batch from file (one requirement per line)

```sh
python3 bin/ai_requirement_translator.py --file requirements.txt --create --markdown
```

### Batch from stdin

```sh
echo "Add two-factor authentication" | python3 bin/ai_requirement_translator.py --stdin --create
cat requirements.txt | python3 bin/ai_requirement_translator.py --stdin --markdown
```

### Interactive REPL

```sh
python3 bin/ai_requirement_translator.py --interactive
```

### Custom Ollama model

```sh
python3 bin/ai_requirement_translator.py --model deepseek-coder-v2 "Migrate PostgreSQL to CockroachDB"
```

**Requirements:** Ollama running locally at `localhost:11434` with `qwen2.5-coder:14b` pulled.

---

## Agile Configuration

To reconfigure workflow states, labels, sprints, or modules:

```sh
# Configure everything (idempotent)
python3 bin/configure_plane_agile.py

# Configure only specific parts
python3 bin/configure_plane_agile.py --states
python3 bin/configure_plane_agile.py --labels
python3 bin/configure_plane_agile.py --cycles --sprints 8
python3 bin/configure_plane_agile.py --modules

# Show current configuration
python3 bin/configure_plane_agile.py --show
```

**Workflow states:** Backlog → Ready → In Progress → In Review → Testing → Done (+ Cancelled, Deferred)

**Sprint cycles:** 6 × 2-week sprints starting from the current Monday

**Modules (epics):** Core Platform · API & Integrations · Media Pipeline · Developer Tools · Data & Storage · Security & Ops · Testing & QA · Documentation

---

## MCP Server (Claude Code Integration)

The MCP server lets Claude Code query and update the roadmap directly.

### Register with Claude Code

```sh
bash bin/register_plane_mcp.sh
```

Or manually:

```sh
claude mcp add plane-roadmap \
  --command python3 \
  --args /path/to/integrated-ai-platform/mcp/plane_mcp_server.py \
  --env PLANE_URL=http://localhost:8000 \
  --env PLANE_API_TOKEN=plane_api_f6c2c3cc049d4fedb24b0f62acbfc00b \
  --env PLANE_WORKSPACE=iap \
  --env PLANE_PROJECT_ID=dbcd4476-1e37-4812-a443-0914ec8380fc
```

### Available MCP tools

| Tool | Description |
|------|-------------|
| `list_issues` | Paginated issue list with status/category filters |
| `get_issue` | Single issue by RM-* ID |
| `create_issue` | Create a new roadmap item |
| `update_status` | Change issue status (syncs to markdown) |
| `search_issues` | Full-text search across all issues |
| `get_stats` | Summary counts by state and category |
| `list_states` | Available workflow states |
| `list_categories` | Available category labels |

### Example Claude Code queries (once MCP is registered)

```
What roadmap items are In Progress?
Show me all API items in Backlog
Search for "OAuth" in the roadmap
Mark RM-API-100 as Done
```

---

## Environment Variables

All scripts read credentials from `docker/.env` (or shell environment):

| Variable | Default | Description |
|----------|---------|-------------|
| `PLANE_URL` | `http://localhost:8000` | Plane API base URL |
| `PLANE_API_TOKEN` | — | API token (from Plane UI: Profile → API Tokens) |
| `PLANE_WORKSPACE` | `iap` | Workspace slug |
| `PLANE_PROJECT_ID` | — | Project UUID (from Plane URL) |
| `PLANE_ADMIN_EMAIL` | `admin@local.dev` | Admin email for setup |
| `PLANE_ADMIN_PASSWORD` | — | Admin password for setup |

---

## Troubleshooting

### Plane containers not starting

```sh
docker compose -f docker/docker-compose-plane.yml logs plane-api --tail=50
```

### Rate limit errors (HTTP 429)

The sync scripts back off automatically (65s wait, then retry). If you see persistent 429 errors, wait 2 minutes and retry. Plane CE allows 60 API requests per minute per token.

### Token authentication failing

```sh
# Verify token is active
docker exec docker-plane-api-1 python3 -c "
import os; os.environ['DJANGO_SETTINGS_MODULE']='plane.settings.production'
import django; django.setup()
from django.apps import apps
APIToken = apps.get_model('db', 'APIToken')
print(list(APIToken.objects.values('token', 'label', 'is_active')))
"
```

### Re-run setup (idempotent)

```sh
bash bin/setup_plane_automated.sh --skip-instance
```

### Check sync status

```sh
docker exec docker-plane-api-1 python3 -c "
import os; os.environ['DJANGO_SETTINGS_MODULE']='plane.settings.production'
import django; django.setup()
from django.apps import apps
Issue = apps.get_model('db', 'Issue')
print(Issue.objects.filter(project_id='dbcd4476-1e37-4812-a443-0914ec8380fc').count(), 'issues')
"
```
