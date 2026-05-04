# Download Pipeline Monitoring Doctrine

Date: 2026-05-04
Deliverable: D-17-105

## Canonical posture

`container (healthy)` is not sufficient for media-pipeline integrity.
Monitoring must cover stage outcomes:

1. Indexer/search health (Prowlarr + arr health surfaces)
2. Queue pressure (Sonarr/Radarr/Lidarr queue depth, SAB queue)
3. Transfer continuity (Syncthing folder state + staleness)
4. Import completion (arr import-history failure signals)
5. Storage path viability (seedbox/QNAP reachability + free space)

## Zabbix implementation baseline

- Host: `mac-mini` (existing Zabbix host id 10783)
- Item key namespace: `d17105.*`
- Provisioner: `scripts/provision-zabbix-download-pipeline.sh`
- Threshold macros:
  - `{$PIPE_STUCK_HOURS}=2`
  - `{$PIPE_DISK_MIN_PCT}=10`
  - `{$PIPE_IMPORT_FAIL_PCT}=5`
  - `{$PIPE_SYNC_STALE_HOURS}=6`

## Known gaps (2026-05-04)

1. Syncthing API credentials expected at `secret/syncthing/{seedbox,qnap}` were absent in current Vault mount, so Syncthing metrics are pending.
2. SAB failed-job metric requires endpoint shaping that remains parser-sensitive under Zabbix HTTP-agent preprocessing; queue depth is live, failed-job signal needs hardening.
3. rTorrent stuck-count signal is not exposed directly by Cleanuparr API and requires dedicated RPC-level probe.

## Operational rule

Every future arr-stack change that touches download clients, path mappings, or transfer substrate must include a D-17-105 item-state check (`d17105.*`) as part of closeout verification.
