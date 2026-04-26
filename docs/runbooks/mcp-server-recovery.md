# MCP Server Recovery

## Current MCP Servers (7 active)

All registered in `~/.claude.json` for project `/Users/admin/repos/integrated-ai-platform`.

| Server | Command | Recovery |
|--------|---------|---------|
| plane-roadmap | python3 mcp/plane_mcp_server.py | Restart process |
| filesystem-mcp | npx @mcp/server-filesystem | Clear npx cache |
| postgresql-mcp | npx @mcp/server-postgres | Check port 5433 |
| docker-mcp | uvx mcp-server-docker | Check docker.sock |
| sequential-thinking | npx @mcp/server-sequential-thinking | Clear npx cache |
| memory | npx @mcp/server-memory | Restart (data reset) |
| sqlite | uvx mcp-server-sqlite | Check DB file |

## Diagnosis Flow

```bash
# 1. Check if the underlying dependency is reachable
python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',5433)); print('DB: OK')"
curl -sf http://localhost:11434/api/tags > /dev/null && echo "Ollama: OK"
curl -sf http://localhost:8000/api/v1/workspaces/iap/projects/ \
  -H "x-api-key: $(grep PLANE_API_TOKEN /Users/admin/repos/integrated-ai-platform/docker/.env | cut -d= -f2)" \
  > /dev/null && echo "Plane: OK"

# 2. Test an MCP server manually
python3 mcp/plane_mcp_server.py 2>&1 | head -5

# 3. Check npx/uvx package cache
npx --version && uvx --version

# 4. Clear stale caches if needed
npm cache clean --force 2>/dev/null
uv cache clean
```

## Common Recovery Actions

### postgresql-mcp: Connection refused

Port 5433 not listening — Plane DB container down or port mapping lost:

```bash
docker ps --filter name=plane-db --format "{{.Status}} {{.Ports}}"
# Should show: Up X hours (healthy) | 127.0.0.1:5433->5432/tcp

# If port missing, recreate plane-db:
cd /Users/admin/repos/integrated-ai-platform/docker
docker compose -f docker-compose-plane.yml up -d plane-db
```

### filesystem-mcp: Cannot read files

If workspace path changes or permissions wrong:

```bash
ls /Users/admin/repos/integrated-ai-platform/
# Verify path exists and is accessible
```

### docker-mcp: Permission denied on socket

```bash
ls -la /var/run/docker.sock
# On macOS, Docker Desktop manages this — restarting Docker Desktop resolves it
```

### memory MCP: Knowledge graph reset

Expected behavior — memory MCP is in-process and resets with each Claude Code session.
For persistent memory, use the sqlite MCP instead:

```bash
# Query existing analytics/notes from SQLite
sqlite3 /Users/admin/repos/integrated-ai-platform/data/platform_analytics.db \
  "SELECT name FROM sqlite_master WHERE type='table';"
```

## Re-Registering an MCP Server

If an MCP server needs to be re-added to Claude Code:

```python
import json
from pathlib import Path

claude_json = Path.home() / ".claude.json"
data = json.loads(claude_json.read_text())
repo = "/Users/admin/repos/integrated-ai-platform"
mcp = data["projects"][repo]["mcpServers"]

# Re-add a server (example):
mcp["server-name"] = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-name"]
}

claude_json.write_text(json.dumps(data, indent=2))
```

Restart Claude Code for changes to take effect.
