# Phase 9: MCP Server Deployment — COMPLETE

**Date:** 2026-04-26  
**Status:** ✅ Installed | ⚠️ Credentials required for 4 servers

## Installed MCP Servers

### Coding Intelligence
| Server | Path | Status | Tools |
|--------|------|--------|-------|
| Code Research | `~/mcp-servers/code-research/build/index.js` | ✅ Active | search_stackoverflow, search_mdn, search_github, search_npm, search_pypi, search_all |
| Docs | `~/mcp-servers/docs/dist/index.js` | ✅ Active | scrape_docs, search_docs, fetch_url, list_libraries + 6 more |
| Brave Search | `brave/node_modules/.bin/brave-search-mcp-server` | ⚠️ Needs `BRAVE_API_KEY` | Web, image, video, news, local search |

### Fitness & Health
| Server | Path | Status | Tools |
|--------|------|--------|-------|
| Strava | `~/mcp-servers/strava/dist/server.js` | ⚠️ Needs OAuth | 26 tools: activities, segments, routes, athlete stats |
| Health/Fitness | `health/node_modules/.bin/health-fitness-mcp` | ✅ Active | BMI, TDEE, macros, workouts, heart rate zones, Strava integration + 17 tools |

> Note: No "Open Wearables MCP" exists; `health-fitness-mcp` provides equivalent fitness/health calculation tools.

### Media
| Server | Path | Status | Tools |
|--------|------|--------|-------|
| Plex | `~/mcp-servers/plex/build/plex-mcp-server.js` | ⚠️ Needs `PLEX_TOKEN` + `PLEX_URL` | Media library access, playback, search |
| Arr Stack | `~/mcp-servers/arr-orchestration/` | ✅ Active (existing) | Already wired in Claude Code |

### Home & Environment
| Server | Path | Status | Tools |
|--------|------|--------|-------|
| Home Assistant | `home-assistant/node_modules/.bin/home-mcp` | ⚠️ Needs `HA_BASE_URL` + `HA_TOKEN` | Device control, state query, automation |
| Weather | `weather/node_modules/.bin/open-meteo-mcp-server` | ✅ Active | Forecast, historical, air quality, marine + 17 tools |

### Security
| Server | Path | Status | Tools |
|--------|------|--------|-------|
| Semgrep | `semgrep/node_modules/.bin/mcp-server-semgrep` | ✅ Active | scan_directory, list_rules, create_rule, analyze/filter/export/compare results |

## Claude Desktop Configuration

Config written to: `~/Library/Application Support/Claude/claude_desktop_config.json`

All 9 new servers registered. Restart Claude Desktop to activate.

## Required Credentials

To activate the 4 servers showing ⚠️:

### Brave Search
1. Sign up at https://api-dashboard.search.brave.com/app/keys
2. Create a free-tier API key
3. Set `"BRAVE_API_KEY": "<your-key>"` in claude_desktop_config.json

### Plex
1. Find your Plex server IP (replace `192.168.10.XXX` in config)
2. Get your token: open Plex Web → any media item → `...` menu → Get Info → View XML → copy `X-Plex-Token` from URL
3. Set `PLEX_URL` and `PLEX_TOKEN` in claude_desktop_config.json

### Home Assistant
1. Open Home Assistant at http://192.168.10.141:8123
2. Profile → Long-Lived Access Tokens → Create token
3. Set `HA_TOKEN` in claude_desktop_config.json

### Strava
1. Create app at https://www.strava.com/settings/api
2. Set `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET` in claude_desktop_config.json
3. In Claude Desktop, say "Connect my Strava account" — it will open a browser for OAuth

## Package Corrections vs. Original Plan

| Original Plan | Actual Package | Reason |
|---------------|----------------|--------|
| Brave Search (custom) | `@brave/brave-search-mcp-server` v2.0.80 | Official Brave package exists |
| Open Wearables MCP | `health-fitness-mcp` | No such package; health-fitness provides equivalent |
| Arr Assistant MCP | `mcp-arr-server` (not installed) | Already covered by existing arr-orchestration |
| homeassistant-ai/ha-mcp | `home-mcp` | Updated package (Feb 2026 vs stale URL) |
| Weather (unspecified) | `open-meteo-mcp-server` | Global, free, no auth required |
| Semgrep MCP | `mcp-server-semgrep` | Auto-installs semgrep CLI |

## Obot Gateway Registration

The new MCP servers are Node.js stdio processes (not containers), so they are not added to `obot-stack.yml`. To expose them through Obot for agent use:

1. Open http://localhost:8090 (Obot admin UI)
2. Navigate to MCP Servers → Add New
3. Add each server using the paths listed above

## Next Steps

Phase 10: Credential population + integration testing
- [ ] Obtain Brave Search API key (free at api-dashboard.search.brave.com)
- [ ] Configure Plex token + server URL
- [ ] Create Home Assistant long-lived token
- [ ] Complete Strava OAuth flow in Claude Desktop
- [ ] Run integration tests per Step 6 of the deployment plan
