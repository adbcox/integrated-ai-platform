# MCP Infrastructure Documentation

**Status:** Phase 10 Complete — 10/10 servers operational  
**Last Updated:** April 27, 2026

## Quick Links

- [Architecture Overview](architecture/mcp-server-architecture.md)
- [Phase 1-10 Summary](phases/phase-1-10-summary.md)
- [Performance Baseline](performance/baseline-metrics.md)

## Runbooks

- [Restart Services](runbooks/restart-services.md)
- [Add New MCP Server](runbooks/add-new-mcp-server.md)
- [Rotate Credentials](runbooks/rotate-credentials.md)

## Troubleshooting

- [Common Issues](troubleshooting/common-issues.md)

## Current Status

### MCP Servers (10/10 Operational)

| # | Server | Type | Port | Tools |
|---|--------|------|------|-------|
| 1 | Filesystem | Remote HTTP | 8091 | 14 |
| 2 | Docker | Remote HTTP | 8092 | 19 |
| 3 | Docs | Remote HTTP | 8093 | 10 |
| 4 | PostgreSQL | NPX phat | — | 1 |
| 5 | GitHub | NPX phat | — | 26 |
| 6 | Weather | NPX phat | — | 17 |
| 7 | Health & Fitness | NPX phat | — | 17 |
| 8 | Semgrep | NPX phat | — | 7 |
| 9 | Strava | NPX phat | — | 24 |
| 10 | Home Assistant | NPX phat | — | 3 |

**Total: 138 tools**

### Performance

- Average response time: ~12ms
- CPU usage: ~4.3%
- RAM usage: ~334 MB
- Error rate: 0%

### Access

- **Obot Gateway:** http://192.168.10.145:8090
- **Credentials:** `docker/.env`
- **Registration script:** `bin/register_obot_tools.py`
- **Stack definition:** `docker/obot-stack.yml`

## Phase History

| Phase | Description | Status |
|-------|-------------|--------|
| 1-2 | Foundation & Gateway | ✅ Complete |
| 3-7 | Infrastructure Hardening | ✅ Complete |
| 8 | Core Services (Plane, AnythingLLM) | ✅ Complete |
| 9 | MCP Server Expansion (10 servers) | ✅ Complete |
| 10 | Validation & Remediation | ✅ Complete |
| 11 | Documentation & Knowledge Transfer | ✅ Complete |

## Next Steps: Phase 12

**P2 External Integrations**
- Gmail MCP (email automation)
- Slack MCP (team communication)
- Notion MCP (documentation management)
- Brave Search MCP (web search)

Estimated timeline: 2-3 weeks
