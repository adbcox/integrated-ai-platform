# MCP RBAC Policies

## Roles

| Role | Who | Intent |
|------|-----|--------|
| Admin | Adrian (owner) | Full access, all operations |
| Dev | Automated scripts, CI | Read-write on code/issues, no infra changes |
| Agent | Obot agents, Claude | Read-mostly, create but not destroy |

## Per-Server Permission Matrix

### GitHub MCP (pending GITHUB_TOKEN)

| Operation | Admin | Dev | Agent |
|-----------|-------|-----|-------|
| List repos, issues, PRs | ✅ | ✅ | ✅ |
| Create issues, comments | ✅ | ✅ | ✅ |
| Create/update PRs | ✅ | ✅ | ❌ |
| Push code, force push | ✅ | ❌ | ❌ |
| Delete branches, repos | ✅ | ❌ | ❌ |
| Manage workflows | ✅ | ✅ | ❌ |

### Filesystem MCP

| Operation | Admin | Dev | Agent |
|-----------|-------|-----|-------|
| Read all repo files | ✅ | ✅ | ✅ |
| Write repo files | ✅ | ✅ | ❌ |
| Access outside workspace | ✅ | ❌ | ❌ |

> Note: Filesystem MCP is currently registered read-write (no internal RBAC).
> The `/workspace` mount in Obot is read-only (`:ro` volume flag).

### PostgreSQL MCP (Plane DB)

| Operation | Admin | Dev | Agent |
|-----------|-------|-----|-------|
| SELECT (read data) | ✅ | ✅ | ✅ |
| INSERT, UPDATE | ✅ | ✅ | ❌ |
| DELETE | ✅ | ❌ | ❌ |
| DDL (CREATE, DROP, ALTER) | ✅ | ❌ | ❌ |

> Note: Currently using `plane:plane` credentials (superuser). To enforce Dev/Agent
> limits, create read-only postgres user:
> ```sql
> CREATE ROLE mcp_reader WITH LOGIN PASSWORD 'mcp_ro_pass';
> GRANT CONNECT ON DATABASE plane TO mcp_reader;
> GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_reader;
> ```
> Then update `postgresql-mcp` args to use `mcp_reader` credentials.

### Plane MCP (roadmap)

| Operation | Admin | Dev | Agent |
|-----------|-------|-----|-------|
| List projects, issues | ✅ | ✅ | ✅ |
| Create issues | ✅ | ✅ | ✅ |
| Update issue status | ✅ | ✅ | ✅ |
| Delete issues | ✅ | ✅ | ❌ |
| Delete projects | ✅ | ❌ | ❌ |

### Docker MCP

| Operation | Admin | Dev | Agent |
|-----------|-------|-----|-------|
| Inspect containers, logs | ✅ | ✅ | ✅ |
| Stats, resource usage | ✅ | ✅ | ✅ |
| Start/stop containers | ✅ | ✅ | ❌ |
| Remove containers | ✅ | ❌ | ❌ |
| Pull images | ✅ | ✅ | ❌ |

### Sequential Thinking, Memory, SQLite

These are user-isolated tools with no sensitive system access — all roles have full access.

## Implementation Notes

RBAC is currently documented-only. Enforcement requires Obot gateway to be set up:
- Config: `config/obot/rbac.yaml`
- Tool config: `config/obot/tools.yaml`
- Registration: `python3 bin/register_obot_tools.py` (after Obot browser setup)

For direct MCP server connections (current mode, without Obot gateway), there is no
per-role filtering — all connections use the same tool capabilities.
