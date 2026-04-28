# ADR-A-007: Syncthing replaces rclone SFTP for seedbox→QNAP transfers

## Status
Accepted (2026-04-27)

## Context

Seedit4me applies a per-account SFTP throughput cap that limited rclone transfers from `seedbox:/home/seedit4me/{sabnzbd/complete,torrents}/` to QNAP `/share/CACHEDEV2_DATA/download/{sabnzbd,rtorrent}/` to ~250 KiB/s (≈2 Mbps), with periodic SSH channel timeouts. WAN baseline at the Mac mini is ~270 Mbps single-stream and ~815 Mbps with 8 parallel streams; LAN to QNAP via SMB is 113 MB/s (904 Mbps). The bottleneck was provider-side, on the SFTP transport specifically.

WebDAV is not provisioned by seedit4me on this account (`PROPFIND /` returns 405; `/files/`, `/dav/`, `/webdav/` all 404). However both Syncthing and Resilio Sync daemons are running on the seedbox, and Syncthing was already installed on the QNAP via QPKG.

## Decision

Adopt **Syncthing** as the seedbox→QNAP transfer mechanism; retire the `rclone-sabnzbd` and `rclone-mover` containers.

- **`is5fj-3grur` `sabnzbd-complete`**: seedbox `/home/seedit4me/sabnzbd/complete/` (sendonly) → QNAP `/share/CACHEDEV2_DATA/download/sabnzbd/` (receiveonly). `ignoreDelete=false` so cleaned-up source files don't leave stale copies on QNAP.
- **`3qukn-rfdel` `torrents-rtorrent`**: seedbox `/home/seedit4me/torrents/rtorrent/` (sendonly) → QNAP `/share/CACHEDEV2_DATA/download/rtorrent/` (receiveonly). `ignoreDelete=true` to preserve seeding obligations: Syncthing on QNAP will not push deletions back, and the seedbox keeps source files indefinitely.
- Syncthing relay used by default (216.144.231.157:443); direct connection negotiated when seedbox NAT permits.
- Folder marker `.stfolder` contains a `README.txt` so future `--delete-empty-src-dirs`-style sweeps (rclone or otherwise) don't delete the marker.

## Why Syncthing, not Resilio

Both daemons run on the seedbox; Resilio's web UI is publicly reachable at `5.nl19.seedit4.me:26400`. But Resilio is **not** installed on the QNAP — only Syncthing is. Installing the Resilio QPKG would have added an installation step and a second sync stack with no measured benefit. Syncthing was already deployed end-to-end and met the throughput bar.

## Consequences

### Throughput

| Backend | 100 MB | 1 GB | Notes |
|---|---|---|---|
| rclone SFTP (prior) | — | ~9 min | 200–600 KiB/s peaks, 250 KiB/s avg, periodic SSH timeouts |
| Syncthing (this ADR) | ~10 s | **60 s** | 136 Mbps avg, 180 Mbps peak (relay) |

**68× faster on 1 GB sustained transfer.** Above the 100 Mbps target.

### Sonarr/Radarr import latency

The retired `run-sabnzbd.sh` trigger-script POSTed `DownloadedEpisodesScan` / `DownloadedMoviesScan` to Sonarr/Radarr immediately after each rclone batch finished (also broken since `curl` isn't in the rclone:1.73.2 alpine image — fixed to `wget` before retirement). Without that hook, imports now happen on Sonarr's/Radarr's internal 60-second poll cycle. Acceptable for now; can be re-added with a Syncthing event listener (`/rest/events?events=ItemFinished`) if low-latency is needed.

### Operational changes

- `rclone-sabnzbd` and `rclone-mover` containers stopped on QNAP (not removed; can be restarted as a fallback).
- `run-sabnzbd.sh` updated and pushed earlier with curl→wget fix and SFTP tuning; that copy retained as documentation but no longer the active path.
- No change to Sonarr/Radarr download client config; they already point at the same QNAP paths.

## Credentials and config locations

- Seedbox Syncthing: API key `cdseDJXQVHvuPS9vtcRQuGkNPHwJtzc5`, device `FIOKLLV-TKSK3JT-FCBNC2K-RBTC7MD-YFXRF33-EJW2UYU-7RNTFER-PE2K5QA`, web UI `127.0.0.1:8384` (loopback; SSH-tunnel on port 2088 to manage), config `/home/seedit4me/.config/syncthing/config.xml`.
- QNAP Syncthing: device `QIOHAF7-MD4Z5MH-26DFUNN-2HYZQJR-HJC7FWQ-GJA5IE6-PMAWJBM-5IQOZQA`, web UI `http://192.168.10.201:8384`, config `/share/CACHEDEV1_DATA/.qpkg/SyncThing/config.xml`.

## Rollback

If Syncthing causes problems:
1. Pause both folders on QNAP (`POST /rest/folder/pause?folder=is5fj-3grur` etc.)
2. Restart rclone containers: `docker start rclone-sabnzbd rclone-mover` (on QNAP)
3. The rclone configuration is unchanged and ready to resume.
