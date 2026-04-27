# ADR-A-002 — Three-tier MCP server strategy
**Status:** Accepted
**Date:** 2026-04-25
**Source:** Phase 9 MCP deployment decision

## Context

Claude Code, Claude Desktop, and the Obot gateway all require access to tools (filesystem, git, databases, Docker, third-party APIs). Three approaches were considered: (1) wire every MCP server directly into each client, (2) use Obot as a single gateway that proxies all tool calls, or (3) a hybrid where high-frequency local tools bypass the gateway.

## Decision

Adopt a three-tier MCP routing model:
- **Tier 1 — Direct (Claude Code):** Servers that require local filesystem access or low latency are registered directly in `~/.claude.json`: filesystem-mcp, docker, plane-roadmap, postgresql, sequential-thinking, memory, sqlite.
- **Tier 2 — Gateway (Obot :8090):** Third-party and cloud-backed tools route through Obot for RBAC, audit logging, and credential isolation: GitHub, Plane API, weather, fitness, Home Assistant, Strava, Semgrep.
- **Tier 3 — Subprocess (mcpo-proxy):** Legacy stdio MCP servers without HTTP transport are wrapped by mcpo-proxy and exposed as HTTP endpoints.

## Consequences

- Claude Code has zero round-trip overhead for local tools (filesystem reads, DB queries)
- Obot provides a single credential store and audit log for all cloud API calls
- Adding a new cloud tool requires only registering it in Obot, not reconfiguring each client
- mcpo-proxy is a single point of failure for Tier-3 servers — mitigated by health monitoring
- Container naming for Obot dynamic shims (ms1xxxxx pattern) requires `container: null` in the service registry to avoid false MISSING alerts
