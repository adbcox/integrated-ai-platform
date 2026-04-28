# RETIRED: rclone SFTP seedbox→QNAP pipeline

## Status
RETIRED 2026-04-27 — replaced by Syncthing (ADR-A-007)

## Why retired
- seedit4me's per-account SFTP throughput cap held transfers to ~2 Mbps
- rclone's SFTP backend's `--multi-thread-streams` did not bypass the cap
- WebDAV not provisioned on this seedit4me account
- Syncthing native peer connection achieves 136+ Mbps sustained

## Containers stopped (not removed)
- `rclone-sabnzbd`
- `rclone-mover`

## Files retained for rollback
- `/share/CACHEDEV2_DATA/Container/rclone/run-sabnzbd.sh` (last patched 2026-04-27 with curl→wget + SFTP tuning)
- `/share/CACHEDEV2_DATA/Container/rclone/run-mover.sh`
- `/share/CACHEDEV2_DATA/Container/rclone/docker-compose.yml`
- `/share/CACHEDEV2_DATA/Container/rclone/rclone.conf`

To resume rclone: stop Syncthing folders, start rclone containers via existing compose file.
