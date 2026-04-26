# Phase 6 Completion Checklist

**Goal:** DNS infrastructure, hostname migration, secrets management
**Started:** 2026-04-26

---

## Week 1: rclone Audit & Legacy Cleanup ✅ COMPLETE 2026-04-26

- [x] Full rclone audit: containers, scripts, configs, health monitor
- [x] Fixed CRITICAL: health monitor auto-restarting QNAP Arr containers (split-brain)
- [x] Fixed CRITICAL: health monitor checking dead QNAP Prowlarr (localhost:9696 → 192.168.10.145:9696)
- [x] Fixed CRITICAL: health monitor Arr health checks (localhost:8989/7878 → 192.168.10.145)
- [x] Stopped QNAP Arr containers (sonarr-1/radarr/prowlarr/sportarr) — no longer managed
- [x] Validated: rclone-mover/sabnzbd untouched and healthy

**Artifacts:** `~/QNAP_RCLONE_CURRENT_STATE.md`, `~/QNAP_RCLONE_LEGACY_ISSUES.md`, `~/PHASE6_RCLONE_MIGRATION_PLAN.md`

---

## Week 2: DNS Infrastructure ✅ COMPLETE 2026-04-26

- [x] `extra_hosts` added to all 4 arr-stack containers (sonarr/radarr/prowlarr/sportarr)
  - `mac-mini.internal` → 192.168.10.145
  - `qnap.internal` → 192.168.10.201
  - `opnsense.internal` → 192.168.10.1
- [x] Containers verified: `mac-mini.internal` resolves inside sonarr/radarr/prowlarr
- [ ] **Manual:** Add `/etc/hosts` entries on Mac Mini (run: `cat /tmp/hosts-addition.txt | sudo tee -a /etc/hosts`)
- [ ] **Manual:** OPNsense host overrides (Services → Unbound DNS → Host Overrides):
  - `mac-mini` / `internal` / `192.168.10.145`
  - `qnap` / `internal` / `192.168.10.201`
  - Enable "Register DHCP leases in DNS"

---

## Week 3: Hostname Migration ✅ COMPLETE 2026-04-26

- [x] **Fixed CRITICAL**: Prowlarr app connections were pointing to dead QNAP Prowlarr (.201:9696)
  - Sonarr: prowlarrUrl `192.168.10.201:9696` → `mac-mini.internal:9696` ✅
  - Radarr: prowlarrUrl `192.168.10.201:9696` → `mac-mini.internal:9696` ✅
  - Sportarr: baseUrl `192.168.10.201:1867` → `mac-mini.internal:1867` ✅
  - Sonarr/Radarr baseUrl updated to `mac-mini.internal` ✅
- [x] **Fixed CRITICAL**: All 6 Prowlarr-synced indexers in Sonarr/Radarr updated
  - Was: `http://192.168.10.201:9696/x/` (dead QNAP Prowlarr)
  - Now: `http://mac-mini.internal:9696/x/` (Mac Mini Prowlarr) ✅
- [x] Download clients already using hostname (`5.nl19.seedit4.me`) — no changes needed

**Before this fix, RSS sync and all searches were silently failing against dead QNAP Prowlarr.**

---

## Week 4: Secrets to Vault ✅ COMPLETE 2026-04-26

### Vault KV v2 (`secret/` mount)

| Path | Contents |
|------|----------|
| `secret/arr/sonarr` | api_key, url (mac-mini.internal:8989) |
| `secret/arr/radarr` | api_key, url (mac-mini.internal:7878) |
| `secret/arr/prowlarr` | api_key, url (mac-mini.internal:9696) |
| `secret/seedbox/sftp` | host, port, user, rclone_obscured_pass |
| `secret/seedbox/sabnzbd` | host, port, user, rclone_obscured_pass |

### rclone Vault Integration
- [x] Vault policy `rclone-reader`: read-only on `secret/seedbox/*`
- [x] Vault token written to QNAP: `/share/CACHEDEV2_DATA/Container/rclone/vault-token` (chmod 600)
- [x] `run-mover.sh` and `run-sabnzbd.sh`: Vault credential injection at startup, fallback to rclone.conf
- [x] **Tested**: rclone connects to seedbox using Vault-injected credentials (no rclone.conf pass)
- [x] **Passwords removed** from `/share/CACHEDEV2_DATA/Container/rclone/rclone.conf`
  - Backup at: `rclone.conf.pre-vault`
  - No `pass =` lines remain in rclone.conf
- [x] rclone containers restarted: `Listed 166` and `Listed 5` confirmed — seedbox connection healthy

---

## Weeks 5–6: Validation & Monitoring

### DNS validation (run `~/validate-dns.sh`)
- [x] Docker containers: `mac-mini.internal` resolves ✅
- [ ] Host /etc/hosts: needs manual sudo step
- [ ] OPNsense DNS: needs host overrides in web UI
- [ ] Full service reachability by hostname: blocked by above

### Uptime Kuma monitoring
- [ ] Add Sonarr monitor: http://192.168.10.145:8989 (already on checklist)
- [ ] Add Radarr monitor: http://192.168.10.145:7878
- [ ] Add Prowlarr monitor: http://192.168.10.145:9696
- [ ] Add Vault monitor: http://192.168.10.145:8200/v1/sys/health

---

## Two Manual Steps Remaining

### 1. Mac Mini /etc/hosts (run once)
```bash
cat /tmp/hosts-addition.txt | sudo tee -a /etc/hosts
```

### 2. OPNsense Host Overrides (web UI)
Navigate to `https://192.168.10.1` → Services → Unbound DNS → Host Overrides

| Host | Domain | IP |
|------|--------|-----|
| mac-mini | internal | 192.168.10.145 |
| qnap | internal | 192.168.10.201 |
| opnsense | internal | 192.168.10.1 |

Also enable: General Settings → "Register DHCP leases in DNS" → Save → Restart Unbound

After both steps, run `~/validate-dns.sh` — all checks should be green.

---

## Architecture Summary (post Phase 6)

```
Seedbox (5.nl19.seedit4.me / 193.163.71.22:2088)
  ↓ rclone (Vault-fetched credentials, no plaintext in rclone.conf)
QNAP (qnap.internal / 192.168.10.201)
  ├── rclone-mover (downloads → /share/download/rtorrent/)
  ├── rclone-sabnzbd (downloads → /share/download/sabnzbd/)
  ├── FlareSolverr :8191
  └── Plex :32400

Mac Mini (mac-mini.internal / 192.168.10.145)
  ├── Sonarr :8989 (indexers via mac-mini.internal:9696) ✅
  ├── Radarr :7878 (indexers via mac-mini.internal:9696) ✅
  ├── Prowlarr :9696 (apps connected via mac-mini.internal) ✅
  ├── Sportarr :1867 ✅
  └── Vault :8200 (secrets: arr keys, seedbox creds)
```
