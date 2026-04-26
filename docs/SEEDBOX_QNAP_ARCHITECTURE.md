# QNAP + Seedbox Media Pipeline: Architecture

## ASCII Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          QNAP NAS (192.168.10.201)                          │
│                          23.4 TB storage, LAN, 24/7                         │
│                                                                             │
│   ┌─────────────┐   ┌─────────────┐   ┌──────────────┐   ┌─────────────┐  │
│   │  Prowlarr   │──▶│   Sonarr    │   │    Radarr    │   │    Plex     │  │
│   │ (indexers)  │   │  (TV shows) │   │   (movies)   │   │  (streams)  │  │
│   └─────────────┘   └──────┬──────┘   └──────┬───────┘   └──────▲──────┘  │
│                             │                  │                  │         │
│                             └────────┬─────────┘                 │         │
│                                      │ .torrent file              │ scans   │
│                                      │ via SFTP                   │ library │
│                                      ▼                            │         │
│                             /share/download/ ◀─────────────────── ┘         │
│                             (QNAP receive dir) ◀──────────────────────────┐ │
└──────────────────────────────────────────────────────────────────────────┼─┘
                                                                           │
                                     SFTP :22 ──▶ 192.168.10.201          │
                                                                           │
                                      rclone sync (every 15 min)          │
                                      copies completed files ──────────────┘
                                                                           ▲
┌──────────────────────────────────────────────────────────────────────────┼─┐
│                    SEEDBOX (193.163.71.22, SFTP port 2088)               │ │
│                    Fast datacenter connection, no per-GB billing         │ │
│                                                                          │ │
│   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │  SFTP blackhole watch directory                                  │   │ │
│   │  /home/seedit4me/rwatch/          ◀── .torrent arrives here     │   │ │
│   └────────────────────┬────────────────────────────────────────────┘   │ │
│                         │ rTorrent picks up .torrent                     │ │
│                         ▼                                                │ │
│   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │  rTorrent (download engine)                                      │   │ │
│   │  Downloads files to:                                             │   │ │
│   │  /home/seedit4me/torrents/rtorrent/                              │   │ │
│   └────────────────────┬────────────────────────────────────────────┘   │ │
│                         │ completed files                                │ │
│                         ▼                                                │ │
│   ┌─────────────────────────────────────────────────────────────────┐   │ │
│   │  rclone sync job (crontab: */15 * * * *)                         │───┘ │
│   │  Source: /home/seedit4me/torrents/rtorrent/                      │     │
│   │  Dest:   qnap:/share/download/                                   │     │
│   │  Log:    /home/seedit4me/rclone.log                              │     │
│   └─────────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────────┘

Connection summary:
  QNAP → Seedbox SFTP:  sftp://193.163.71.22:2088  (Sonarr/Radarr drop .torrent)
  Seedbox → QNAP SFTP:  sftp://192.168.10.201:22   (rclone pushes completed files)
  Blackhole path:        /home/seedit4me/rwatch/
  Downloads path:        /home/seedit4me/torrents/rtorrent/
```

---

## Why This Architecture?

### QNAP runs the management stack
- 23.4 TB storage capacity — enough for long-term media library
- Stable always-on LAN device (runs 24/7, low power)
- Hosts Sonarr, Radarr, Prowlarr, and Plex — the management and serving layer
- All media is organized and served from one place

### Seedbox is download-only
- Datacenter-grade connection: fast downloads, high upload ratios
- No per-GB billing on the seedbox plan means heavy downloading is cost-effective
- Isolated from home network: seedbox activity does not affect LAN bandwidth for streaming
- rTorrent is purpose-built for this workload — stable, low-overhead torrent client

### rclone bridges them
- Runs on a schedule (every 15 minutes) — no manual intervention needed
- Handles partial file exclusion (`--exclude "*.part"`) so only completed files transfer
- Retries automatically on transient network failures
- Logs every sync operation for debugging
- One-way sync: seedbox → QNAP (QNAP is the authoritative library store)

### Plex on QNAP serves the final media
- Plex scans `/share/download/` after Sonarr/Radarr organize the files into the library
- Streaming from the LAN NAS avoids seedbox bandwidth limits
- All transcoding happens on QNAP hardware, not the seedbox

---

## Data Flow Step-by-Step

1. **Prowlarr finds a release** and notifies Sonarr (TV) or Radarr (movies) via its indexer feed.

2. **Sonarr/Radarr downloads the `.torrent` file** (or magnet link) from the indexer.

3. **Sonarr/Radarr sends the `.torrent` to the seedbox blackhole via SFTP:**
   - Host: `193.163.71.22`, Port: `2088`
   - Drop path: `/home/seedit4me/rwatch/`
   - This is configured in Sonarr/Radarr under Settings → Download Clients → rTorrent (blackhole mode) or a dedicated blackhole client pointing at the SFTP path.

4. **rTorrent on the seedbox picks up the `.torrent` from `rwatch/`** and begins downloading the content to its configured download directory.

5. **Downloaded files appear in `/home/seedit4me/torrents/rtorrent/`** once the torrent completes (or as pieces finish, for large releases).

6. **rclone sync (runs every 15 minutes via crontab)** copies completed files from the seedbox to QNAP:
   - Source: `/home/seedit4me/torrents/rtorrent/`
   - Destination: `qnap:/share/download/` (SFTP remote pointing at `192.168.10.201:22`)
   - Partial files (`.part`) are excluded so only finished content transfers.

7. **Sonarr/Radarr on QNAP detects the file** arriving in `/share/download/`, renames and organizes it into the media library (e.g., `/share/media/TV/`, `/share/media/Movies/`).

8. **Plex scans the library** and makes the newly organized title available for streaming on the local network and remotely.

---

## Remote Path Mapping

Sonarr and Radarr track downloads by the path the torrent client reports. Because the torrent client (rTorrent) runs on the seedbox but the files ultimately land on QNAP, you must tell Sonarr/Radarr how to translate between the two paths.

**Where to configure:**
`Settings → Download Clients → Remote Path Mappings`

| Field | Value |
|-------|-------|
| Host | `193.163.71.22` (the seedbox) |
| Remote Path | `/home/seedit4me/torrents/rtorrent/` |
| Local Path | `/share/download/` |

**What this does:**
When rTorrent reports that a file is at `/home/seedit4me/torrents/rtorrent/Show.Name.S01E01/`, Sonarr rewrites that path to `/share/download/Show.Name.S01E01/` before looking for the file on QNAP. This is how Sonarr knows where to find the file after rclone has synced it.

**Important:** The local path must be the actual mount point or share path that QNAP exposes. Adjust `/share/download/` if your QNAP download share is mounted elsewhere.

---

## What to Install on the Seedbox

| App | Role | Required? |
|-----|------|-----------|
| **rclone** | Syncs completed downloads to QNAP | **CRITICAL** |
| **Flood** | Modern web UI for rTorrent monitoring | Recommended |
| **Autobrr** | IRC announce monitoring for instant grabs | Advanced / Optional |
| Sonarr | TV management | **DO NOT INSTALL** — already on QNAP |
| Radarr | Movie management | **DO NOT INSTALL** — already on QNAP |
| Plex | Media streaming | **DO NOT INSTALL** — already on QNAP |
| Syncthing | File sync alternative | **DO NOT USE** — use rclone instead |
| Jellyfin | Media streaming alternative | **DO NOT INSTALL** — already on QNAP |

### rclone (CRITICAL)
Without rclone, downloaded files stay on the seedbox forever and never reach QNAP. This is the single most important piece of software to install and configure correctly. See `SEEDBOX_APPS_SETUP.md` for full setup instructions.

### Flood (Recommended)
A modern web UI for rTorrent with a REST API. Lets you monitor active torrents, check download progress, and verify the blackhole is being picked up — all from a browser. The Mac Mini dashboard can surface seedbox torrent status via the Flood API.

### Autobrr (Advanced/Optional)
Monitors IRC announce channels for trackers and grabs releases the moment they are announced — before they appear on RSS feeds. Only useful if you are on trackers with IRC announce and want race-level speed. Requires IRC credentials for each tracker.

---

## Monitoring

### Dashboard (Mac Mini at http://mac-mini:8080)
The AI platform dashboard shows seedbox status as part of the media stack monitoring panel. It connects via SFTP to verify connectivity and can surface:
- Seedbox online/offline status
- rclone last sync time (parsed from `~/rclone.log`)
- Active torrent count (via Flood REST API if installed)

### Circuit Breaker
The dashboard uses a circuit breaker pattern to protect against seedbox DNS or network failures. If SFTP connectivity to `193.163.71.22` fails more than a threshold number of times within a window, the circuit opens and stops hammering the connection, falling back to a cached "last known" status.

### DNS Bypass
The seedbox dashboard connects directly to the IP address `193.163.71.22` rather than using a hostname. This avoids DNS resolution failures causing false "offline" readings. The SFTP port is `2088` (non-standard — required by this seedbox provider).

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Downloads stuck in queue, not completing | rclone sync not running on seedbox | SSH to seedbox, check `crontab -l` and `tail ~/rclone.log` |
| Sonarr shows "import failed" | Remote path mapping is wrong | Check Settings → Download Clients → Remote Path Mappings; verify paths match exactly |
| Seedbox shows "offline" in dashboard | SFTP connection failed | Try connecting directly: `sftp -P 2088 seedit4me@193.163.71.22`; check if seedbox is in maintenance |
| Files not showing in Plex | Sonarr/Radarr did not organize the file | Check `/share/download/` on QNAP for the raw file; check Sonarr/Radarr activity log for import errors |
| rclone sync completes but files missing on QNAP | QNAP SFTP credentials expired or path wrong | Run `rclone ls qnap:/share/download/` from seedbox to verify remote is reachable |
| rTorrent not picking up `.torrent` from blackhole | rwatch directory path is wrong in rTorrent config | Verify rTorrent's `directory.watch.added` config points to `/home/seedit4me/rwatch/` |
| Very slow sync speeds | Low `--transfers` or `--checkers` in rclone script | Increase `--transfers 8 --checkers 16` in `sync_to_qnap.sh` and re-test |
