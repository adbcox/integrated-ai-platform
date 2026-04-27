# MCP Server Architecture

**Last Updated:** April 27, 2026
**Phase:** 10 Complete

## Overview

The MCP (Model Context Protocol) infrastructure consists of 10 servers managed by an Obot gateway. All tool calls from Claude Code or other AI clients route through Obot at `:8090`.

## Network Topology

```
Claude Code / AI Client
        │
        ▼
  Obot Gateway (:8090)
  [Docker container]
        │
   ┌────┴────────────────────────────────┐
   │                                     │
   ▼ NPX (phat containers)              ▼ Remote HTTP
   ├── Weather                          ├── Filesystem (:8091)
   ├── PostgreSQL                       │   [Docker: mcp-filesystem-remote]
   ├── Health & Fitness                 ├── Docker (:8092)
   ├── Semgrep                          │   [macOS host: nohup process]
   ├── GitHub                           └── Docs (:8093)
   ├── Home Assistant                       [Docker: mcp-docs-remote]
   └── Strava
```

## Deployment Models

### NPX Phat Containers
Obot spawns an isolated Docker container (`ghcr.io/obot-platform/mcp-images/phat`) per server.
- **Cold start:** 20-30 seconds
- **Use case:** Stateless servers with no host dependencies
- **Servers:** Weather, PostgreSQL, Health & Fitness, Semgrep, GitHub, Home Assistant, Strava

### Remote HTTP (supergateway)
Server runs as a persistent process (Docker container or macOS host), exposing Streamable HTTP.
Obot's `remote` runtime proxies to `http://host.docker.internal:<port>/mcp`.
- **Cold start:** Instant (already running)
- **Use case:** Servers needing host access (filesystem, Docker socket, native binaries)
- **Servers:** Filesystem (:8091), Docker (:8092), Docs (:8093)

## Server Inventory

| Server | Runtime | Port | Package | Tools | Auth |
|--------|---------|------|---------|-------|------|
| Filesystem | remote | 8091 | @modelcontextprotocol/server-filesystem | 14 | None |
| Docker | remote | 8092 | mcp-server-docker (uvx) | 19 | None |
| Docs | remote | 8093 | @arabold/docs-mcp-server | 10 | None |
| PostgreSQL | npx | — | @modelcontextprotocol/server-postgres | 1 | DSN |
| GitHub | npx | — | @modelcontextprotocol/server-github | 26 | PAT |
| Weather | npx | — | open-meteo-mcp-server | 17 | None |
| Health & Fitness | npx | — | health-fitness-mcp | 17 | None |
| Semgrep | npx | — | mcp-server-semgrep | 7 | None |
| Strava | npx | — | strava-mcp-server | 24 | OAuth |
| Home Assistant | npx | — | home-mcp | 3 | Token |

**Total: 138 tools**

## Credential Management

All credentials stored in `docker/.env`:
```
GITHUB_TOKEN=ghp_...
HA_TOKEN=...
HA_BASE_URL=http://192.168.10.141:8123
STRAVA_CLIENT_ID=225374
STRAVA_CLIENT_SECRET=...
STRAVA_ACCESS_TOKEN=...
STRAVA_REFRESH_TOKEN=...
POSTGRES_DSN=postgresql://plane:plane@docker-plane-db-1:5432/plane
```

Credentials are injected as environment variables by `register_obot_tools.py` into the Obot API at registration time.

**Note:** `STRAVA_ACCESS_TOKEN` expires every ~6 hours. Manual rotation required until refresh token automation is implemented.

## Audit Logging

Obot writes an audit log to `/data/audit.log` inside the container.
- Volume-mounted: `obot-data:/data`
- To read: `docker exec obot cat /data/audit.log`
- Format: JSON lines, one entry per tool call

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Gateway | Obot | latest |
| Container runtime | Docker via Colima | — |
| Stdio→HTTP bridge | supergateway | 3.4.3 |
| NPX phat image | ghcr.io/obot-platform/mcp-images/phat | v0.20.2 |
| Filesystem server | @modelcontextprotocol/server-filesystem | 0.2.0 |
| Docker MCP | mcp-server-docker (uvx) | latest |
| Docs server | @arabold/docs-mcp-server | 0.1.0 |

## Key Architectural Decisions

### Why Remote HTTP for Filesystem/Docker/Docs?
Obot's phat containers are isolated — they cannot mount host volumes or access the Colima Docker socket. Remote HTTP lets these servers run where they have the necessary access, then Obot proxies to them.

### Why `host.docker.internal` URLs?
Phat containers are not on `obot-net`, so they cannot resolve Docker container names. Using `host.docker.internal` routes through the macOS host's loopback, accessible from any container.

### Why `npm install -g` for Docs server?
`@arabold/docs-mcp-server` depends on `tree-sitter`, a native Node.js module. `npx -y` downloads to a temp directory where `node-gyp` cannot compile it. Global install provides the build step needed on linux/arm64 (no prebuilt binary available for ABI 127).

## Integration Points

- **Obot UI:** http://localhost:8090 — manage servers, view audit logs
- **Registration script:** `bin/register_obot_tools.py`
- **Stack definition:** `docker/obot-stack.yml`
- **Credentials:** `docker/.env`
