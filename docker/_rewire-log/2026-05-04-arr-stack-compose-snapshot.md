# Rewire-log — 2026-05-04 — arr-stack compose post-hoc snapshot (D-17-89)

**File (out-of-repo):**
`/Users/admin/control-center-stack/stacks/arr-stack/docker-compose.yml`

**Reason:** D-17-89 git integration audit surfaced that the arr-stack
compose file had no rewire-log snapshots despite 4 service additions
(Bazarr D-17-47, Cleanuparr D-17-49, Sportarr unretire D-17-36,
Lidarr D-17-87). This is a post-hoc snapshot capturing current state.
Future arr-stack compose changes must follow pre/post snapshot
discipline (D#15 doctrine).

---

## Current state (2026-05-04)

**Lines:** 420
**SHA256:** `7866489167e049234fc8cd1ab7f569e36c354683361ab349584deff23089186c`

**Services defined:**
- `sonarr` (8989) — TV show management
- `radarr` (7878) — movie management
- `prowlarr` (9696) — indexer management
- `sportarr` (1867) — sports content (unretired D-17-36; no Caddy front)
- `vault-agent-bazarr` (sidecar, exits on render)
- `bazarr` (6767) — subtitle automation (D-17-47)
- `vault-agent-cleanuparr` (sidecar, exits on render)
- `cleanuparr` (11011) — queue/download remediation (D-17-49)
- `vault-agent-lidarr` (sidecar, exits on render)
- `lidarr` (8686) — music management (D-17-87)

**Network:** `control-center-net` (external)

**All 7 application containers healthy at snapshot time.**

---

## Known gaps at snapshot time (see D-17-89/AUDIT_2026-05-04.md)

- Sportarr has no Caddy front / Dnsmasq entry (deliberate, direct-port)
- Sonarr/Radarr/Prowlarr/Sportarr lack provision scripts (pre-pattern era)
- D-17-87 (Lidarr) committed with --no-verify (process deviation, no
  credential risk, acknowledged in D-17-88 closure note)
