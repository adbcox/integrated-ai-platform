# QNAP Syncthing — media transfer endpoint

Replaces the retired `rclone-sabnzbd` / `rclone-mover` containers.
See `docs/adr/ADR-A-007-media-sync-syncthing.md` for context.

## Live config
- Container: native QPKG `SyncThing` (not Docker)
- Web UI: http://192.168.10.201:8384
- Config: `/share/CACHEDEV1_DATA/.qpkg/SyncThing/config.xml`
- Process: `/share/CACHEDEV1_DATA/.qpkg/SyncThing/syncthing --gui-address=0.0.0.0:8384 --home=/share/CACHEDEV1_DATA/.qpkg/SyncThing`

## Folders
- `is5fj-3grur` (sabnzbd-complete) → `/share/CACHEDEV2_DATA/download/sabnzbd/` (receiveonly)
- `3qukn-rfdel` (torrents-rtorrent) → `/share/CACHEDEV2_DATA/download/rtorrent/` (receiveonly, ignoreDelete=true to preserve seeding)

## Snapshot
`qnap-config.xml.snapshot` is a sanitized copy of the live config (apikey redacted)
captured 2026-04-27 for version-control reference. Don't deploy it directly —
device IDs are tied to the running daemon.
