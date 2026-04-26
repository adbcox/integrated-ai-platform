# P1 MCP Servers

## Deployed (active in ~/.claude.json)

### Sequential Thinking
- **Purpose**: Break complex tasks into verified reasoning chains; reduces hallucination
- **Command**: `npx -y @modelcontextprotocol/server-sequential-thinking`
- **Use when**: Multi-step architecture decisions, debugging complex failures, planning sequences
- **Token cost**: Minimal startup overhead; runs inline

### Memory (Knowledge Graph)
- **Purpose**: Persist entities and relationships across Claude Code sessions
- **Command**: `npx -y @modelcontextprotocol/server-memory`
- **Storage**: In-memory knowledge graph (resets when server restarts)
- **Use when**: Tracking long-running context across multiple sessions (projects, decisions, people)

### SQLite Analytics
- **Purpose**: Local structured data for platform analytics and prototyping
- **Command**: `uvx mcp-server-sqlite --db-path data/platform_analytics.db`
- **Database**: `data/platform_analytics.db` (already has `execution_queue.db` schema)
- **Use when**: Querying platform execution history, running analytics on aider benchmarks

## Pending (blocked on credentials)

### Brave Search
- **Purpose**: Real-time web search for documentation lookups
- **Command**: `npx -y @modelcontextprotocol/server-brave-search`
- **Blocker**: Requires `BRAVE_API_KEY` — sign up free at: https://brave.com/search/api/
- **To activate after getting key**:
  ```bash
  # Add to docker/.env:
  echo "BRAVE_API_KEY=BSA_your_key" >> docker/.env

  # Register in Claude Code:
  python3 - << 'PYEOF'
  import json, os; from pathlib import Path
  d = json.loads((Path.home()/".claude.json").read_text())
  d["projects"]["/Users/admin/repos/integrated-ai-platform"]["mcpServers"]["brave-search"] = {
      "type": "stdio", "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {"BRAVE_API_KEY": "BSA_your_key"}
  }
  (Path.home()/".claude.json").write_text(json.dumps(d, indent=2))
  PYEOF
  ```

### GitHub MCP (P0 blocked)
- **Purpose**: Issue creation, PR management, code search
- **Blocker**: `GITHUB_TOKEN` in `docker/.env` (PAT with `repo`, `read:org`, `workflow` scopes)
- **Command (when available)**: Via Obot gateway (GitHub MCP needs server-side storage for token)

## Not Deployed — Ollama (Native)

Ollama runs natively on the Mac Mini, NOT as an MCP server. Available at `http://localhost:11434`.

**Current models:**
| Model | Size | Primary Use |
|-------|------|-------------|
| qwen2.5-coder:32b | 19.9 GB | Complex code generation, stage6 planning |
| devstral:latest | 14.3 GB | Aider tactical execution |
| deepseek-coder-v2 | 8.9 GB | Code review, alternative reasoning |
| qwen2.5-coder:14b | 9.0 GB | Balanced default (make aider-fast) |
| qwen2.5-coder:7b | 4.7 GB | Fast iteration (make aider-micro-safe) |

**Integration points:**
- `domains/task_decomposer.py` — calls `localhost:11434/api/generate` directly
- `make aider-fast` / `make aider-hard` / `make aider-smart` — use OLLAMA_API_BASE
- `OLLAMA_API_BASE=http://localhost:11434` in docker/.env

**No llama3.3 currently.** To pull if needed: `ollama pull llama3.3`

## P2 Roadmap (Future)

| Server | Purpose | Notes |
|--------|---------|-------|
| Gmail MCP | Email automation | Needs Google OAuth |
| Plex MCP | Media queries | Token in docker/.env |
| Home Assistant MCP | Home automation | Needs HA instance |
| Vector DB MCP | RAG embeddings | Needs embedding infrastructure |
| Custom Training MCP | LoRA pipeline | When Mac Studio arrives |
