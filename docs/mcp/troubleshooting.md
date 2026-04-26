# MCP Troubleshooting Guide

## Common Issues

### Server fails to start

**Symptom:** Tool not available in Claude Code, or `npx`/`uvx` errors on first use.

**Diagnosis:**
```bash
# Test a specific server manually
npx -y @modelcontextprotocol/server-filesystem /tmp 2>&1 | head -5
uvx mcp-server-docker 2>&1 | head -5
python3 mcp/plane_mcp_server.py 2>&1 | head -10
```

**Common causes:**
- `npx` cache stale → `npx cache clean --force`
- `uvx` package not found → `uv cache clean`
- Python deps missing → `pip install -r requirements.txt`
- Plane API down → `curl http://localhost:8000/api/v1/workspaces/iap/`

### PostgreSQL MCP connection refused

**Symptom:** `Connection refused` on `postgresql://plane:plane@localhost:5433/plane`

**Diagnosis:**
```bash
python3 -c "import socket; s=socket.socket(); s.connect(('127.0.0.1',5433)); print('OK')"
docker ps --filter name=plane-db --format "{{.Names}}: {{.Status}} {{.Ports}}"
```

**Fix:** Plane DB container may have lost its port mapping:
```bash
cd docker && docker compose -f docker-compose-plane.yml up -d plane-db
```

### Docker MCP permission denied

**Symptom:** `permission denied while trying to connect to the Docker daemon socket`

**Fix:** Ensure the user is in the `docker` group or the socket has the right permissions:
```bash
ls -la /var/run/docker.sock
# On macOS, Docker Desktop manages this automatically
```

### Obot gateway 403 Forbidden

**Symptom:** Obot at `:8090` returns 403 on all API calls.

**Current known state:** Obot requires browser-based bootstrap setup before API is accessible.
See `docs/mcp/obot-setup.md` for setup instructions.

**Quick check:**
```bash
curl http://localhost:8090/api/healthz  # should return "ok"
docker ps --filter name=obot --format "{{.Status}}"  # should be "healthy"
```

### Plane MCP tool returns empty results

**Symptom:** `list_issues` returns 0 items even though Plane has issues.

**Diagnosis:**
```bash
# Check Plane API directly
curl -s "http://localhost:8000/api/v1/workspaces/iap/projects/" \
  -H "x-api-key: $(grep PLANE_API_TOKEN docker/.env | cut -d= -f2)" | python3 -m json.tool | head -20

# Check MCP server directly
python3 mcp/plane_mcp_server.py 2>&1 | head -20
```

**Common cause:** PLANE_PROJECT_ID mismatch — verify `docker/.env` has the right UUID.

### Memory MCP resets between sessions

**Expected behavior.** The `@modelcontextprotocol/server-memory` stores data in-process memory.
It resets when the MCP server process restarts (i.e., each new Claude Code session).

For persistent memory, consider using the SQLite MCP to store key facts in `data/platform_analytics.db`.

### Ollama slow or timing out

**Symptom:** Task decomposition takes >30 seconds, or `_call_ollama()` times out.

**Diagnosis:**
```bash
curl -s http://localhost:11434/api/tags | python3 -m json.tool  # list loaded models
curl -s http://localhost:11434/api/ps   # show running models
```

**Fix:** Smaller model for speed: set `OLLAMA_DEFAULT_MODEL=qwen2.5-coder:7b` in `docker/.env`.
Or switch to 14b as the balanced option.

## Health Checks

### Quick platform health
```bash
# All critical services
curl -sf http://localhost:8000/api/v1/workspaces/iap/projects/ \
  -H "x-api-key: $(grep PLANE_API_TOKEN docker/.env | cut -d= -f2)" > /dev/null && echo "Plane API: OK"
curl -sf http://localhost:8090/api/healthz > /dev/null && echo "Obot: OK"
curl -sf http://localhost:11434/api/tags > /dev/null && echo "Ollama: OK"
curl -sf http://localhost:8080/health > /dev/null && echo "Dashboard: OK"
curl -sf http://localhost:3030 > /dev/null && echo "Grafana: OK"
```

### MCP server smoke test
```bash
# plane-roadmap: should return stats JSON
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_stats","arguments":{}}}' | \
  python3 mcp/plane_mcp_server.py 2>/dev/null | head -5
```

## Token Consumption

Current 7-server setup uses approximately **6,170 tokens** (~3.1% of 200K context).
Run `python3 -c "$(cat docs/mcp/token_estimate.py)"` (if added) for live estimates.

| Server count | Estimated tokens | Context used |
|-------------|-----------------|--------------|
| 7 (current) | ~6,170 | 3.1% |
| 10 (+3 P1)  | ~8,000 | 4.0% |
| 15 (P2)     | ~12,000 | 6.0% |

Even at 20 servers, token cost stays under 15K (7.5% of 200K context).
Progressive discovery (lazy loading via Obot) would reduce this further by only loading
tool definitions when needed.
