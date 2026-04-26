# Phase 5 Completion Checklist

**Goal:** Validate Phase 3 stack end-to-end + migrate Arr stack from QNAP to Mac Mini

---

## Week 1: Arr Stack Migration (QNAP .201 → Mac Mini .145) ✅ COMPLETE 2026-04-26

### QNAP Storage Migration ✅ COMPLETE 2026-04-26
- [x] @Recycle emptied: 371GB freed
- [x] New directory structure created: `/share/CACHEDEV2_DATA/data/{media,torrents,usenet}/{tv,movies,sports}`
- [x] Symlink created: `/share/download/data → /share/CACHEDEV2_DATA/data` (SMB-accessible)
- [x] Staging moved to review: rtorrent/, sonarr/, radarr/ → review-for-deletion/old-staging/
- [x] TV migrated: 169 dirs instant-moved to `/share/CACHEDEV2_DATA/data/media/tv/` (CACHEDEV2 local mv)
- [x] Movies migrated: 357 dirs instant-moved to `/share/CACHEDEV2_DATA/data/media/movies/` (CACHEDEV2 local mv)
- [x] Plex DB backed up: `/share/CACHEDEV2_DATA/backups/plex/` (222MB)
- [x] Plex library paths updated via Plex SQLite: `/data/media/movies` + `/data/media/tv`
- [x] Plex library scan triggered — refreshing at new paths
- [x] Sonarr root folder: `/downloads/TV` → `/data/media/tv` (id=10, accessible, 2815GB free)
- [x] Radarr root folder: `/downloads/Movies` → `/data/media/movies` (id=8, accessible, 2815GB free)
- [x] Sonarr bulk path update: 185/185 series paths updated, library rescan triggered
- [x] Radarr bulk path update: 424/425 movies updated (1 corrected separately), rescan triggered
- [x] Validation: Sonarr 4,106 episode files ✅ | Radarr 335 movies on disk ✅ (matches pre-migration)
- [x] docker-compose updated: `/data` volume mount added (symlink path through `/downloads/data`)

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

## Week 2: Phase 3 Integration Validation ✅ COMPLETE 2026-04-26

### Root Folder Fix ✅ COMPLETE 2026-04-26
- [x] Sonarr root folder: `/tv` (inaccessible) → `/downloads/TV` (2.6TB free) ✅
- [x] Radarr root folder: `/movie` (inaccessible) → `/downloads/Movies` (2.6TB free) ✅
- [x] All 185 Sonarr series paths bulk-updated via API
- [x] All 424 Radarr movie paths bulk-updated via API
- [x] Library rescan: Sonarr 4,106 episode files | Radarr 335 movies on disk

### Download Pipeline Validated ✅ 2026-04-26
- [x] RSS Sync: 400 reports found, 0 grabbed (library current — last import 2026-04-25)
- [x] Sonarr history: grabs + imports active (Gold Rush S16E22, Fire Country S04E16, Hunting Party S02E11)
- [x] SABnzbd download client: enabled → 5.nl19.seedit4.me:443 (SSL)
- [x] rclone-mover + rclone-sabnzbd: running on QNAP
- [x] All 4 services healthy: :8989 :7878 :9696 :1867

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

## Week 3: Monitoring ✅ COMPLETE 2026-04-26 (Phase 7)

### Uptime Kuma (http://192.168.10.145:3033) ✅ 12 monitors configured
- [x] Open WebUI :3002
- [x] LiteLLM :4000/v1/models
- [x] MCPO :8081/openapi.json
- [x] Homarr :7575
- [x] Home Assistant .141 :8123
- [x] Vault :8200/v1/sys/health
- [x] Obot :8090/api/healthz
- [x] Sonarr :8989
- [x] Radarr :7878
- [x] Prowlarr :9696
- [x] Plex .201 :32400
- [x] IAP Dashboard :8080/api/status
- [ ] Ollama :11434/api/tags (optional — not externally exposed)
- [ ] Plane :3001 (optional)

### Grafana (http://192.168.10.145:3030) ✅ Dashboard provisioned
- [x] Dashboard: Phase 7 — Infrastructure Status (CPU, memory, network, disk, containers)
- [ ] Dashboard: Arr Stack (queue sizes, disk usage) — future
- [ ] Dashboard: Performance (response times, request rates) — future

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
