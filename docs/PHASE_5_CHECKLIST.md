# Phase 5 Completion Checklist

**Goal:** Validate Phase 3 stack end-to-end + migrate Arr stack from QNAP to Mac Mini

---

## Week 1: Arr Stack Migration (QNAP .201 → Mac Mini .145) ✅ COMPLETE 2026-04-26

### Pre-migration ✅
- [x] SSH key auth set up: Mac Mini → QNAP (passwordless)
- [x] Full QNAP inventory captured: `~/qnap-inventory-20260426/`
- [x] Configs backed up via rsync: `~/arr-backups/20260426/` (sonarr 485MB, radarr 875MB, prowlarr 128MB, sportarr 68MB)

### QNAP SMB mount ✅
- [x] Share `//192.168.10.201/download` mounted at `~/mnt/qnap-downloads` (23TB, 37% used)
- [x] Contains: TV (169 dirs), Movies (357 dirs), rtorrent, sabnzbd, sports
- [x] Mount script: `~/mount-qnap.sh` (run after reboot)

### Arr stack deployment on Mac Mini ✅
- [x] docker-compose.yml updated: paths use `~/mnt/qnap-downloads`
- [x] Sonarr :8989 — healthy, **185 shows** restored
- [x] Radarr :7878 — healthy, **425 movies** restored
- [x] Prowlarr :9696 — healthy, **5 indexers** restored
- [x] Sportarr :1867 — healthy

### Cutover ✅
- [x] QNAP: sonarr-1, radarr, prowlarr, sportarr **stopped**
- [x] QNAP still running: Plex :32400, FlareSolverr :8191, rclone-mover, rclone-sabnzbd
- [x] Prowlarr → Sonarr/Radarr connections already pointing to 192.168.10.145
- [x] FlareSolverr URL correct: http://192.168.10.201:8191
- [x] Download clients: SABnzbd enabled → seedbox (5.nl19.seedit4.me:443); rtorrent disabled
- [x] Indexer sync triggered via Prowlarr API

### API Keys (confirmed)
- Sonarr: `2731353744504eb0a5d4225b7c40dfc6`
- Radarr: `2a3636f0d3b44ee48082c96298dc5194`
- Prowlarr: `9dbcdf169ec8477bb051fdc60e30f17a`

### MCP Servers deployed ✅
- [x] `arr-orchestration`: search_show, search_movie, get_calendar, get_queue, get_library_stats, get_indexer_health
- [x] `pipeline-monitor`: get_pipeline_health, get_rclone_health, get_rclone_logs, get_disk_space
- [x] Both registered in `~/.claude.json` — restart Claude Code to activate
- [x] venv: `~/mcp-servers/venv2/` (Python 3.14 + mcp[cli] + requests)

---

## Week 2: Phase 3 Integration Validation

### LiteLLM → Ollama ✅ VALIDATED
- [x] Chat test passes (293ms first token, qwen-coder-7b)
- [x] 8 models available (5 Ollama + claude-sonnet + claude-haiku + gpt-4o)
- [ ] Test in Open WebUI browser: http://192.168.10.145:3002
- [ ] Test RAG: upload a PDF and ask questions

### MCPO → Filesystem MCP ✅ VALIDATED
- [x] 14 tools available at /openapi.json
- [x] read_file works (tested CLAUDE.md)
- [x] list_directory works (1730 items in workspace)
- [ ] Connect MCPO to Open WebUI: Settings → Tools → http://mcpo-proxy:8081

### MCP Servers (7/10 active)
- [x] plane-roadmap active
- [x] filesystem-mcp active
- [x] postgresql-mcp active
- [x] docker-mcp active
- [x] sequential-thinking active
- [x] memory active
- [x] sqlite active
- [ ] github-mcp: add `GITHUB_TOKEN=ghp_xxx` to docker/.env, restart Obot
- [ ] brave-search: add `BRAVE_API_KEY=BSA_xxx` to docker/.env
- [ ] obot-gateway: complete browser OAuth at http://192.168.10.145:8090

### Homarr widgets
- [ ] Add Sonarr widget (after migration): http://192.168.10.145:8989 + API key
- [ ] Add Radarr widget: http://192.168.10.145:7878 + API key
- [ ] Add Prowlarr widget: http://192.168.10.145:9696 + API key

---

## Week 3: Monitoring

### Uptime Kuma (http://192.168.10.145:3033)
- [ ] Open WebUI :3002
- [ ] LiteLLM :4000/v1/models
- [ ] MCPO :8081/openapi.json
- [ ] Homarr :7575
- [ ] Home Assistant :8123
- [ ] Vault :8200/v1/sys/health
- [ ] Obot :8090/api/healthz
- [ ] Sonarr :8989 (after migration)
- [ ] Radarr :7878 (after migration)
- [ ] Prowlarr :9696 (after migration)
- [ ] Ollama :11434/api/tags
- [ ] Plane :3001

### Grafana (http://192.168.10.145:3030)
- [ ] Dashboard: Control Center overview (all service status)
- [ ] Dashboard: Arr Stack (queue sizes, disk usage)
- [ ] Dashboard: Performance (response times, request rates)

---

## Week 4: Performance & Stability

### Baseline captured ✅
- [x] Performance baseline: `~/phase5-performance-baseline.txt`
- [x] Script: `~/phase5-performance-test.sh`

### Stability targets
- [ ] All Phase 3 services stable 7+ consecutive days
- [ ] Vault stays unsealed across restarts (note: requires manual unseal procedure)
- [ ] No container OOM restarts

---

## Performance Baseline (captured 2026-04-26)

| Service | Response Time |
|---------|-------------|
| Open WebUI | 3ms |
| Homarr | 28ms |
| Home Assistant | 3ms |
| LiteLLM /v1/models | 2ms |
| MCPO /openapi.json | 2ms |
| Vault health | 1ms |
| Ollama /api/tags | 1ms |
| LLM inference (qwen-coder-7b) | 293ms first token |

Colima VM memory: 7.737GiB — increase with `colima stop && colima start --memory 16` if containers need more headroom.

---

## Arr Stack Migration Notes ✅ COMPLETE 2026-04-26

**Current state:** Arr services running on Mac Mini .145 — QNAP .201 services stopped.
- Sonarr: http://192.168.10.145:8989 (185 shows)
- Radarr: http://192.168.10.145:7878 (425 movies)
- Prowlarr: http://192.168.10.145:9696 (5 indexers)
- Sportarr: http://192.168.10.145:1867

**QNAP still hosts:** Plex :32400 (native QPKG), FlareSolverr :8191, rclone seedbox sync
**Media storage:** 23TB at `~/mnt/qnap-downloads` (SMB mount) — run `~/mount-qnap.sh` after reboot
**Backup dir:** `~/arr-backups/20260426/`
**Download architecture:** Sonarr/Radarr → SABnzbd on seedbox (5.nl19.seedit4.me) → rclone pulls to QNAP → scan triggered

**Key discovery:** QNAP Container Station creates a root-level `config.xml` decoy; actual Sonarr config lives in `config/` subdir. rclone scripts had the correct Sonarr API key all along.

---

## Manual Completion Checklist

Steps requiring direct access (SSH/browser) — check off as you go:

### Steps 1–6: Arr Migration ✅ COMPLETE 2026-04-26
All automated via Claude Code session. See migration notes above.

### Step 7: MCP Credentials
- [ ] GitHub PAT (scopes: repo, read:org, workflow) → `GITHUB_TOKEN=ghp_xxx` in `~/control-center-stack/stacks/gateways/.env`
- [ ] Brave Search API key → `BRAVE_API_KEY=BSA_xxx` in same .env
- [ ] Restart Obot: `docker restart obot`
- [ ] Complete Obot OAuth browser setup: http://192.168.10.145:8090

### Step 8: Homarr Widgets (after Arr migration)
- [ ] Open http://192.168.10.145:7575 → Edit mode
- [ ] Add Sonarr widget → http://192.168.10.145:8989 + API key
- [ ] Add Radarr widget → http://192.168.10.145:7878 + API key
- [ ] Add Prowlarr widget → http://192.168.10.145:9696 + API key
- [ ] Add Calendar widget

### Step 9: Validate
- [ ] `~/validate-phase5-complete.sh` — all checks pass

### Step 10: Security
- [ ] Back up `~/vault-init-keys.txt` to QNAP or password manager (CRITICAL — contains Vault unseal keys)
