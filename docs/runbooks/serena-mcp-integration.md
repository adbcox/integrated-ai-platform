# Serena MCP Integration Runbook

**Source:** Local AI Workstation Roadmap §11 (feat/foundation-install-track-2), with corrections based on Serena 1.2.0 actual CLI
**Date:** 2026-05-10
**Purpose:** Configure Serena as an MCP server for agent worktrees and validate per-project symbol lookup.

---

## Overview

Serena is the semantic code-intelligence layer, providing symbol search, definition lookup, reference lookup, and repo structure analysis to coding agents. This runbook configures Serena to operate as an MCP server with per-worktree project configuration.

---

## Prerequisites

- Serena 1.2.0 or later installed (`serena --version`)
- Agent worktrees created (see AGENT_WORKTREE_POLICY.md)
- At least one target repo with git repository structure

---

## Configuration pattern: Per-worktree MCP server

The canonical roadmap §11.3 specifies:

```
Use per-workspace Serena configuration for coding clients where possible.
```

**Implementation:** Start a Serena MCP server for each agent worktree with the `--project` flag:

```bash
serena start-mcp-server --project /path/to/worktree [OPTIONS]
```

This ensures each agent (OpenCode, Aider, Cline, etc.) has its own isolated Serena context and does not share symbol caches or project state.

---

## Starting Serena MCP server for a worktree

### Basic startup (stdio transport, default)

```bash
cd ~/local-ai-workstation/worktrees/integrated-ai-platform-opencode
serena start-mcp-server --project .
```

Or with absolute path:

```bash
serena start-mcp-server --project ~/local-ai-workstation/worktrees/integrated-ai-platform-opencode
```

**Options explained:**

- `--project .` or `--project /path/to/worktree` — Initialize Serena for the specified project
- `--transport stdio` (default) — Use stdio for MCP communication (typical for CLI agents)
- `--enable-web-dashboard true` (default) — Show the web dashboard (useful for debugging)
- `--open-web-dashboard true` (default) — Open dashboard in browser on startup

### Headless startup (no dashboard, for automation)

```bash
serena start-mcp-server \
  --project ~/local-ai-workstation/worktrees/integrated-ai-platform-opencode \
  --enable-web-dashboard false \
  --open-web-dashboard false
```

### With HTTP transport (for IDE clients)

```bash
serena start-mcp-server \
  --project ~/local-ai-workstation/worktrees/integrated-ai-platform-opencode \
  --transport streamable-http \
  --port 8000 \
  --host 127.0.0.1
```

Then configure IDE client to connect to `http://127.0.0.1:8000`.

---

## Verification: Test symbol lookup

Once the Serena MCP server is running, verify symbol search works:

### Method 1: Via Serena CLI (in the project)

```bash
cd ~/local-ai-workstation/worktrees/integrated-ai-platform-opencode
serena project health-check
```

Expected output: Shows project health, symbol cache status, indexed files.

### Method 2: Via Serena project tools (after init)

```bash
cd ~/local-ai-workstation/worktrees/integrated-ai-platform-opencode
serena project index
```

This forces indexing of all source files and populates the symbol cache.

### Method 3: Manual testing of symbol resolution

If the MCP server is running, you can test via the MCP client. Example test query (MCP-compatible format):

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "find_symbol",
    "arguments": {
      "symbol": "TaskCreate",
      "type": "class"
    }
  }
}
```

Serena should return symbol locations and definitions.

---

## Multi-agent setup: Start servers for each worktree

To support OpenCode, Aider, and Cline in parallel on the same repo, start separate Serena MCP servers for each:

```bash
# Terminal 1: OpenCode worktree
serena start-mcp-server --project ~/local-ai-workstation/worktrees/integrated-ai-platform-opencode

# Terminal 2: Aider worktree
serena start-mcp-server --project ~/local-ai-workstation/worktrees/integrated-ai-platform-aider

# Terminal 3: Cline worktree
serena start-mcp-server --project ~/local-ai-workstation/worktrees/integrated-ai-platform-cline
```

Each server has isolated symbol caches and project state. No cross-worktree cache pollution.

---

## Agent-side configuration (Phase 7)

For each coding agent (OpenCode, Aider, Cline), configure the MCP server endpoint:

### OpenCode config

In `.opencode/opencode.json` or via OpenCode CLI:

```json
{
  "mcp_servers": {
    "serena": {
      "command": "serena",
      "args": ["start-mcp-server", "--project", "<worktree_path>"],
      "transport": "stdio"
    }
  }
}
```

### Aider config

In `.aider.conf.yml`:

```yaml
mcp:
  serena:
    command: serena
    args:
      - start-mcp-server
      - --project
      - <worktree_path>
```

### Cline config (VS Code extension)

In VS Code settings (`settings.json`):

```json
{
  "cline.mcp_servers": {
    "serena": {
      "command": "serena",
      "args": ["start-mcp-server", "--project", "<worktree_path>"],
      "transport": "stdio"
    }
  }
}
```

Replace `<worktree_path>` with the absolute path to the agent's worktree.

---

## Troubleshooting

### Serena command not found

If `serena` is not on PATH, use the full executable path:

```bash
/Users/adriancox/.local/bin/serena start-mcp-server --project <path>
```

Or add to PATH:

```bash
export PATH="/Users/adriancox/.local/bin:$PATH"
```

### Symbol cache not populating

Run explicit indexing:

```bash
cd ~/local-ai-workstation/worktrees/integrated-ai-platform-opencode
serena project index
```

### MCP server not responding

Check server logs:

```bash
serena start-mcp-server --project <path> --log-level DEBUG
```

Look for LSP connection errors. Verify `.serena/project.yml` exists in the worktree.

### Per-project config not being used

Verify project initialization:

```bash
cd ~/local-ai-workstation/worktrees/integrated-ai-platform-opencode
ls -la .serena/
```

If `.serena/` doesn't exist, Serena will create it on first server start. Inspect `.serena/project.yml` to confirm project settings.

---

## Benchmark policy (§11.4)

When benchmarking coding agents, record whether Serena was used:

```json
{
  "task_id": "TASK-0001",
  "agent": "opencode",
  "serena_enabled": true,
  "serena_project_path": "~/local-ai-workstation/worktrees/integrated-ai-platform-opencode",
  "result": "success|failure",
  "artifact_path": "..."
}
```

Every multi-file benchmark must test:
- Agent WITHOUT Serena
- Agent WITH Serena

This allows measurement of Serena's impact on code quality and task completion.

---

## Implementation note

The canonical roadmap §11.3 specifies the per-workspace configuration pattern but does not detail the `start-mcp-server` command syntax. This runbook documents the actual Serena 1.2.0 CLI implementation, which uses:

```bash
serena start-mcp-server --project /path/to/worktree
```

rather than a hypothetical `serena --project` flag. The intent and design are identical to the roadmap specification.
