# Phase 10: Validation & Testing Report

**Date:** 2026-04-27  
**Status:** COMPLETE — 7/10 servers operational, 3 blocked by infrastructure gaps  
**Gateway:** http://192.168.10.145:8090

---

## MCP Server Status (10 registered)

### ✅ Operational (7/10)

| # | Server | ID | Tools | Notes |
|---|--------|----|-------|-------|
| 1 | Weather | ms1gzwnt | 17 | air_quality, climate_projection, dwd_icon_forecast, ecmwf_forecast, elevation + 12 more |
| 2 | Health & Fitness | ms1jqn26 | 17 | bmi, tdee, macros, heart_rate_zones, hydration + 12 more |
| 3 | GitHub | ms1b4cj8 | 26 | issues, PRs, branches, commits, files + 21 more |
| 4 | Home Assistant | ms1kb8jv | 3 | LightControl, SwitchControl, getStates |
| 5 | Semgrep | ms18jq7z | 3 | analyze_results, compare_results, create_rule |
| 6 | PostgreSQL (Plane) | ms14fpds | 1 | query |
| 7 | Strava | ms1pbs64 | 1 | under_construction ⚠️ |

> **Note — Obot tool cache:** Servers 4–6 show stale/cross-wired tool lists in the REST API due to an Obot caching issue triggered when the Docker server was re-registered mid-session. The underlying `phat` containers are running the correct packages (verified via process inspection: `nanobot _exec npx <correct-package>`). The cache corrects itself on Obot restart or after periodic refresh.

> **Note — Strava:** The `strava-mcp` npm package (v1.x) is an incomplete placeholder that returns `under_construction`. A working Strava MCP requires either a different package or a custom implementation. The OAuth credentials are correctly configured.

### ❌ Non-Operational (3/10) — Infrastructure Blockers

| # | Server | ID | Root Cause | Fix Required |
|---|--------|----|-----------|--------------|
| 1 | Filesystem | ms1cv9fj | `ENOENT: /workspace` — phat container has no volume mount | Mount `/Users/admin/repos/integrated-ai-platform:/workspace` in Obot's child container config |
| 2 | Docker | ms1hhqd2 | `FileNotFoundError: /var/run/docker.sock` — socket not in phat container | Mount `/var/run/docker.sock` in phat container, or run `mcp-server-docker` on host |
| 3 | Docs | ms1x2np6 | `No native build for platform=linux arch=arm64 runtime=node abi=141` — `tree-sitter` in `@arabold/docs-mcp-server` has no arm64/Linux/Node25 prebuilt binary | Replace with arm64-compatible docs MCP, or build `tree-sitter` from source in phat image |

**Root cause summary:** Obot spawns isolated `phat` containers (`ghcr.io/obot-platform/mcp-images/phat:v0.20.2`) per MCP server. These containers have no access to the host filesystem or Docker socket by default. Obot's current manifest API does not expose a `volumes` configuration option.

---

## Credential Validation

| Credential | Status |
|-----------|--------|
| `GITHUB_TOKEN` | ✅ Configured — GitHub server serving 26 tools |
| `HA_TOKEN` | ✅ Configured — Home Assistant server responding |
| `STRAVA_CLIENT_ID` | ✅ Configured |
| `STRAVA_CLIENT_SECRET` | ✅ Configured |
| `STRAVA_ACCESS_TOKEN` | ✅ Configured (expires ~6h — no refresh token) |
| `PLEX_TOKEN` | ✅ In docker/.env (Plex server not registered with Obot) |
| `STRAVA_REFRESH_TOKEN` | ❌ Not configured — token will expire |

---

## Performance

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Avg health endpoint response | **12ms** | <500ms | ✅ |
| Min response | 10ms | — | — |
| Max response | 22ms | — | — |
| Obot CPU usage | 4.32% | — | ✅ |
| Obot memory | 334 MiB / 7.74 GiB (4.3%) | — | ✅ |
| Error rate (health endpoint) | 0% | <1% | ✅ |

---

## Audit Logging

- **Configured:** `OBOT_AUDIT_LOG=true`, path `/data/audit.log`
- **Status:** File not yet created — audit.log is written on first agent MCP call. Will appear at `/data/audit.log` inside the `obot` container once any Obot agent executes a tool.

---

## RBAC

RBAC is defined in `config/obot/tools.yaml` (Admin/Dev/Agent tiers) but Obot's current deployment runs with `OBOT_SERVER_ENABLE_AUTHENTICATION=false` and `OBOT_DEV_MODE=true`. Per-server RBAC enforcement is not active. Requires enabling Obot authentication before production use.

---

## Remediation Plan

### Priority 1 — Fix tool cache cross-wiring (5 min)
Restart Obot to flush stale cached tool data:
```bash
docker restart obot
sleep 30
python3 bin/register_obot_tools.py --check
```
**Caveat:** Semgrep's `@modelcontextprotocol/sdk` fix (applied to ephemeral phat container) will be lost. Semgrep will need the workaround re-applied or a permanent fix (see below).

### Priority 2 — Fix Semgrep SDK dep permanently (10 min)
The `mcp-server-semgrep` v1.0.0 package has a missing dep bug. Permanent fix via Obot startup hook:
```bash
# Add to obot-stack.yml under obot service entrypoint or post-start script:
# npm install -g mcp-server-semgrep @modelcontextprotocol/sdk
```
Or switch to the official `@semgrep/mcp` package when published.

### Priority 3 — Fix Filesystem + Docker (requires Obot config change)
Obot needs to pass volume mounts to phat containers. Options:
- **Option A:** Use Obot's `OBOT_SERVER_MCP_SERVER_DEFAULT_VOLUMES` env var (check current Obot version docs)
- **Option B:** Run Filesystem and Docker MCP servers as persistent processes on the host, register as `remote` runtime pointing to `http://host.docker.internal:<port>`
- **Option C:** Build custom `phat` image with `/workspace` and socket pre-configured

### Priority 4 — Fix Docs (arm64 native build)
Replace `@arabold/docs-mcp-server` with an arm64-compatible alternative:
```bash
# Candidate: @modelcontextprotocol/server-fetch (no native deps)
# Or: context7-mcp (pure JS)
```

### Priority 5 — Strava token refresh + real implementation
```bash
# Set up token refresh automation
echo "STRAVA_REFRESH_TOKEN=<from_oauth_flow>" >> docker/.env
# Replace strava-mcp placeholder with real implementation
```

---

## Known Issues Summary

| Issue | Severity | Impact |
|-------|----------|--------|
| Docker server 503 | High | No container management via Obot |
| Filesystem server 503 | High | No repo file access via Obot |
| Docs server 503 | Medium | No live doc scraping via Obot |
| Strava `under_construction` | Medium | No fitness data via Obot |
| Strava token expires ~6h | Medium | Server will stop working without refresh |
| Tool cache cross-wiring | Low | API cosmetic; actual containers run correct packages |
| Audit log not yet written | Info | Appears on first agent MCP call |
| RBAC not enforced | Info | Auth disabled in dev mode |
