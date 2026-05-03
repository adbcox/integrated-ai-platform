# MCP Server Architecture

**Last updated:** 2026-04-29 (Phase 14 D-DOC rewrite — supersedes Phase 10 version)
**Phase:** 14 D-DOC (post-Phase-13 state)

---

## Overview

The MCP (Model Context Protocol) infrastructure routes tool calls from Claude Code
and other AI clients through an Obot gateway at `:8090`. Obot dispatches to backend
MCP servers, which run as Docker-managed containers.

All credential-bearing MCP servers use the canonical Vault Agent sidecar pattern:
a one-shot Vault Agent sidecar renders `credentials.env` before the service starts.

---

## Network topology

```
Claude Code / AI Client
        │
        ▼
  Obot Gateway (:8090)
  [Docker: obot-net + plane-net + control-center-net]
  [Vault Agent sidecar: vault-agent-obot]
        │
   ┌────┴──────────────────────────────────────────────────┐
   │                                                       │
   ▼ Remote HTTP (Streamable HTTP/MCP)                     │
   ├── mcp-filesystem-remote   (:8091)  obot-net           │
   ├── mcp-docker-remote       (:8092)  macOS host         │
   ├── mcp-docs-remote         (:8093)  obot-net           │
   └── plex-mcp                (:8094)  bridge             │
                                                           │
   ▼ Obot-managed (internal, lifecycle managed by Obot)    │
   ├── sms1obot-mcp-server     (:8080)  bridge             │
   └── sms1obot-mcp-server-shim (:8099) bridge             │
```

---

## Deployment models

### Remote HTTP (Docker-managed, compose-controlled)

Persistent containers exposing Streamable HTTP endpoints. Obot proxies to
`http://<container-name>:<port>/mcp` (or `http://host.docker.internal:<port>/mcp`
for host-side processes).

| Container | Port | Compose file | Credentials | cap_drop |
|---|---|---|---|---|
| mcp-filesystem-remote | 8091 | obot-stack.yml | none | ALL |
| mcp-docker-remote | 8092 | docker-compose.mcp-docker-remote.yml | none | ALL |
| mcp-docs-remote | 8093 | obot-stack.yml | none | ALL (+ SETUID/SETGID/CHOWN/DAC_OVERRIDE for startup apt-get) |
| plex-mcp | 8094 | mcp/docker-compose.yml | Vault Agent sidecar | ALL |

**mcp-docker-remote** runs on the macOS host network (`--network host` equivalent)
because the Colima Docker socket is not mountable from inside containers.
It is compose-managed via `docker/mcp/docker-compose.mcp-docker-remote.yml`.

**mcp-docs-remote** runs `apt-get` + `npm install -g @arabold/docs-mcp-server` at
startup due to native `tree-sitter` compilation requirements. This is a known
fragility (see `docs/known-issues/KI-mcp-docs-remote-startup.md`). Start period: 3 min.

### Obot-managed containers

`sms1obot-mcp-server` and `sms1obot-mcp-server-shim` are started dynamically by
Obot's internal container management. They are not compose-managed; `cap_drop`
cannot be applied durably without Obot configuration API support.
See `docs/known-issues/KI-mcp-docs-remote-startup.md` for the Phase 14 tracking issue.

---

## Credential management

All MCP server credentials flow through Vault:

```
Vault KV  →  Vault Agent sidecar  →  /vault/secrets/credentials.env  →  service entrypoint
```

The entrypoint wrapper pattern:
```sh
set -a && . /vault/secrets/credentials.env && set +a && exec <binary>
```

**No credentials in `environment:` compose blocks or `.env` files.**
`detect-secrets` pre-commit hook enforces this on tracked files.

### Current credential-bearing MCP servers

| Server | Vault path(s) |
|---|---|
| plex-mcp | `secret/plex/api`, `secret/arr/{sonarr,radarr}` |
| obot | `secret/obot/{admin,github,plane}` |

---

## Audit logging

Obot writes a JSON-lines audit log to `/data/audit.log` (container volume `obot-data`):

```bash
docker exec obot tail -f /data/audit.log
```

Each entry records: timestamp, tool name, server, caller identity, and input hash.

---

## Current server inventory

| Server | Port | Package | Purpose | Auth |
|---|---|---|---|---|
| mcp-filesystem-remote | 8091 | @modelcontextprotocol/server-filesystem | Read/write workspace files | None |
| mcp-docker-remote | 8092 | mcp-server-docker (uvx) | Docker container management | None |
| mcp-docs-remote | 8093 | @arabold/docs-mcp-server | Tech docs search + fetch | None |
| plex-mcp | 8094 | @adamwdraper/mcp-server-plex | Plex/Sonarr/Radarr management | Vault sidecar |

Additional servers registered in Obot (Obot-managed lifecycle):
- PostgreSQL MCP (Plane DB)
- Sequential Thinking
- Memory graph
- SQLite
- Plane roadmap connector
- Pipeline monitor
- arr-orchestration

---

## Hardening

All compose-managed MCP containers have:
- `cap_drop: [ALL]` (minimal `cap_add` where required — see table above)
- `security_opt: [no-new-privileges:true]`

Known gaps (Phase 14 D-DOC tracking):
- `sms1obot-mcp-server*` — Obot-managed; not compose-hardened (D#30)
- `mcp-docs-remote` — broad `cap_add` required for startup `apt-get`; pre-built image recommended (D#29)

---

## Adding a new MCP server

See `docs/runbooks/add-new-mcp-server.md` for the full procedure including
Vault provisioning, sidecar template, compose block, and Obot registration.
