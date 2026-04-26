# Phase 5 Completion Checklist

**Goal:** Validate Phase 3 stack end-to-end + migrate Arr stack from QNAP to Mac Mini

---

## Week 1: Arr Stack Migration (QNAP .201 → Mac Mini .145)

### Pre-migration (manual — SSH to QNAP required)
- [ ] SSH to QNAP: `ssh admin@192.168.10.201`
- [ ] Backup Sonarr: `docker exec sonarr tar czf /tmp/sonarr-backup.tar.gz -C /config .`
- [ ] Backup Radarr: `docker exec radarr tar czf /tmp/radarr-backup.tar.gz -C /config .`
- [ ] Backup Prowlarr: `docker exec prowlarr tar czf /tmp/prowlarr-backup.tar.gz -C /config .`
- [ ] Copy backups to Mac Mini: `scp ~/sonarr-backup-*.tar.gz ~/radarr-backup-*.tar.gz ~/prowlarr-backup-*.tar.gz admin@192.168.10.145:~/arr-backups/`
- [ ] Document QNAP share names for media and downloads (check QNAP File Station)

### QNAP SMB mount setup (run on Mac Mini)
- [ ] Identify QNAP SMB share names (typically "Media", "Downloads", "Public")
- [ ] Set env vars: `export QNAP_SMB_USER=admin QNAP_SMB_PASS=<password>`
- [ ] Test mount: `~/mount-qnap.sh`
- [ ] Verify paths exist: `ls /Volumes/qnap-media /Volumes/qnap-downloads`

### Arr stack deployment on Mac Mini
- [ ] Confirm mounts work: `ls /Volumes/qnap-media /Volumes/qnap-downloads`
- [ ] Deploy: `cd ~/control-center-stack/stacks/arr-stack && docker compose up -d`
- [ ] Wait for healthy status: `docker ps --filter name=sonarr --filter name=radarr --filter name=prowlarr`
- [ ] Access fresh installs: http://192.168.10.145:8989, :7878, :9696

### Config restore from QNAP backups
- [ ] Restore Sonarr: `docker cp ~/arr-backups/sonarr-backup-*.tar.gz sonarr:/tmp/ && docker exec sonarr sh -c 'cd /config && tar xzf /tmp/sonarr-backup-*.tar.gz' && docker restart sonarr`
- [ ] Restore Radarr: same pattern
- [ ] Restore Prowlarr: same pattern
- [ ] Verify indexers working in Prowlarr
- [ ] Verify root folders accessible in Sonarr/Radarr (update to /media/TV, /media/Movies)
- [ ] Test search in Sonarr and Radarr

### Cutover (only after full verification)
- [ ] ⚠️ **MANUAL ONLY**: SSH to QNAP and stop Arr services: `docker stop sonarr radarr prowlarr`
- [ ] Verify Mac Mini Arr stack handles all requests
- [ ] Update config/connectors.yaml URLs from .201 to .145

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

## Arr Stack Migration Notes

**Current state:** Arr services RUNNING on QNAP .201 (do not stop without verification)
- Sonarr: http://192.168.10.201:8989 (401 = auth required, service up)
- Radarr: http://192.168.10.201:7878 (302 = redirect, service up)
- Prowlarr: http://192.168.10.201:9696 (302 = redirect, service up)

**QNAP NFS:** RPC timeout — use SMB instead (`mount -t smbfs`)

**Arr stack compose:** `~/control-center-stack/stacks/arr-stack/docker-compose.yml`
**Mount script:** `~/mount-qnap.sh` (set `QNAP_SMB_USER` + `QNAP_SMB_PASS` env vars first)
**Backup dir:** `~/arr-backups/`
**API keys needed:** `SONARR_API_KEY`, `RADARR_API_KEY`, `PROWLARR_API_KEY` (get from Settings → General in each web UI before migration)
