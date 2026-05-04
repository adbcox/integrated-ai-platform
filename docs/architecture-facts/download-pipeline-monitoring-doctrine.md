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

## Syncthing staleness threshold — 48h rationale (D-17-107, 2026-05-04)

`{$PIPE_SYNC_STALE_HOURS}` set to **48** (not 6).

**Why 6h was too tight:**
- Syncthing staleness (`max_stale_h`) is computed from the `lastFile.at` timestamp across
  all folders in `/rest/stats/folder`. This timestamp updates only when a new file is
  transferred to completion — it does NOT update during quiet periods when no new content
  is available.
- The seedbox→QNAP pipeline (folder `is5fj-3grur`) and the rTorrent folder
  (`3qukn-rfdel`) both have natural quiet windows of multiple days when no new
  content has been seeded/queued.
- A 6h threshold generates noise alerts during normal quiet periods, producing
  alert fatigue that causes operators to dismiss real failures.

**Why 48h is appropriate:**
- Pipeline health check frequency on the Sonarr/Radarr side is typically weekly-to-daily
  (episode releases, calendar-driven Radarr monitoring). A 48h staleness window covers
  normal gaps.
- If Syncthing is genuinely broken (folder in error state, SSH unreachable), the
  `d17105.syncthing.qnap.state` trigger (state=2) fires immediately — the staleness
  trigger is a secondary signal for the case where Syncthing is technically "up" but
  quietly stalled with no file activity.
- 48h provides ~2× margin over typical peak quiet windows observed empirically.

**Adjust if pipeline cadence changes:**
If the platform transitions to a higher-frequency feed (e.g. daily bulk transfers), reduce
`{$PIPE_SYNC_STALE_HOURS}` to 12h. Update via provisioner re-run:
```sh
scripts/provision-zabbix-download-pipeline.sh
```
The provisioner reads this macro and `ensure_macro` will update it idempotently.

## Known gaps update (2026-05-04 close)

Items 1–3 from the original gap list:

1. ~~Syncthing API credentials absent~~ — RESOLVED. `secret/syncthing/qnap` populated; `secret/syncthing/seedbox` added. Syncthing metrics live via host-side trapper sender (launchd `com.iap.syncthing-zabbix-sender`).
2. ~~SAB failed-job metric parser-sensitive~~ — RESOLVED. JSONPath preprocessing (`$.history.noofslots`) replaces regex; stable.
3. rTorrent stuck-count — still deferred per operator decision D1 (D-17-107). Cleanuparr (D-17-86) provides stuck-torrent coverage operationally.

4. **SABnzbd recent-failures-only trigger** (new, D-17-107): Operator requested tuning the failed-jobs trigger to fire only on failures-in-last-7-days, not cumulative count. Current implementation (`d17105.sab.failed_jobs` via `mode=history&failed_only=1&limit=100`) returns all current failed items in history. The `limit=100` parameter bounds it but the rolling-7-day window requires either: (a) Zabbix calculated item with `last()` against a timestamp item, or (b) SABnzbd API filtering by date client-side. Deferred — current SABnzbd behavior of clearing stale failures on success is operationally adequate.
