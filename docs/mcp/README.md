# MCP Architecture — Integrated AI Platform

## Overview

Claude Code connects to 7 MCP servers registered in `~/.claude.json` for this project.
Obot gateway (`:8090`) is running and becomes an 8th connection point once browser setup is complete.

## Active Servers (7)

| Server | Tier | Transport | Purpose | Status |
|--------|------|-----------|---------|--------|
| plane-roadmap | P0 | stdio | Plane CE roadmap CRUD via API | Active |
| filesystem-mcp | P0 | stdio | Read repo files at `/workspace` | Active |
| postgresql-mcp | P0 | stdio | SQL queries → Plane DB (port 5433) | Active |
| docker-mcp | P0 | stdio | Container inspect/manage | Active |
| sequential-thinking | P1 | stdio | Multi-step reasoning chains | Active |
| memory | P1 | stdio | Persistent knowledge graph | Active |
| sqlite | P1 | stdio | Local analytics DB (`data/platform_analytics.db`) | Active |

## Pending

| Server | Tier | Blocker |
|--------|------|---------|
| github-mcp | P0 | Needs `GITHUB_TOKEN` in `docker/.env` (PAT: repo, read:org, workflow) |
| obot-gateway | Hub | Needs browser setup at http://192.168.10.113:8090 → generate API key |
| brave-search | P1 | Needs Brave Search API key (free tier at brave.com/search/api/) |

## Ollama (Native — Not MCP)

Ollama runs natively on the Mac Mini at `http://localhost:11434`. It is NOT an MCP server — Claude Code calls it directly via the Ollama HTTP API, or through `domains/task_decomposer.py`.

**Loaded models:**
| Model | Size | Use case |
|-------|------|----------|
| qwen2.5-coder:32b | 19.9 GB | Complex code generation |
| devstral:latest | 14.3 GB | Aider primary (code tasks) |
| deepseek-coder-v2 | 8.9 GB | Code review / fallback |
| qwen2.5-coder:14b | 9.0 GB | Balanced speed/quality |
| qwen2.5-coder:7b | 4.7 GB | Fast iteration |

## Connection Map

```
Claude Code CLI
    │
    ├── plane-roadmap (stdio) ─── mcp/plane_mcp_server.py ─── Plane API :8000
    ├── filesystem-mcp (stdio) ── npx @mcp/server-filesystem ── /workspace (repo root)
    ├── postgresql-mcp (stdio) ── npx @mcp/server-postgres ──── localhost:5433 (Plane DB)
    ├── docker-mcp (stdio) ────── uvx mcp-server-docker ──────── docker.sock
    ├── sequential-thinking (stdio) ─ npx @mcp/server-sequential-thinking
    ├── memory (stdio) ──────────── npx @mcp/server-memory
    ├── sqlite (stdio) ──────────── uvx mcp-server-sqlite ──── data/platform_analytics.db
    │
    └── [Pending] obot-gateway (HTTP) ── localhost:8090 ── Obot MCP hub
                                                                │
                                                                ├── github-mcp (needs token)
                                                                ├── [all P0 servers mirrored]
                                                                └── audit log + RBAC
```

## Quick References

- Obot Admin UI: http://192.168.10.113:8090
- Obot healthcheck: `curl http://localhost:8090/api/healthz`
- Plane API: http://localhost:8000/api/v1
- Ollama API: http://localhost:11434/api
- Plane DB (host): `psql postgresql://plane:plane@localhost:5433/plane`
- SQLite analytics: `sqlite3 data/platform_analytics.db`

## Adding a New MCP Server

```bash
# 1. Test the package
npx -y @modelcontextprotocol/server-NAME --help

# 2. Add to ~/.claude.json via Python
python3 - << 'PYEOF'
import json; from pathlib import Path
d = json.loads((Path.home()/".claude.json").read_text())
d["projects"]["/Users/admin/repos/integrated-ai-platform"]["mcpServers"]["new-server"] = {
    "type": "stdio", "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-NAME"]
}
(Path.home()/".claude.json").write_text(json.dumps(d, indent=2))
PYEOF

# 3. Restart Claude Code to pick up changes
```
