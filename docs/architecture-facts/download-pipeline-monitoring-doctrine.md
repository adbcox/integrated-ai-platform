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

## Finding 24 — Syncthing QNAP is a silent SPOF for all arr-stack imports (D-17-112, 2026-05-04)

**Failure mode observed:** Syncthing process on QNAP died silently (no error log entry; OOM kill suspected — process exited cleanly without logging cause). No monitoring existed for the QNAP Syncthing process health — the existing Zabbix trapper item (`com.iap.syncthing-zabbix-sender` launchd on Mac Mini) pushes staleness metrics from the QNAP GUI, but if Syncthing itself is dead, the GUI is unreachable and the sender logs an error but does NOT emit a Zabbix alert — the trapper item simply goes stale (which does eventually fire the staleness trigger at 48h).

**Impact:** With Syncthing down, `/share/CACHEDEV2_DATA/download/sabnzbd/lidarr/` on QNAP contained only `.smbdelete*` placeholder files. Lidarr, Sonarr, Radarr, and Sportarr ALL import via this single Syncthing pipe. All arr-stack imports were silently blocked. The failure manifested as `importPending` in Lidarr queues with `No files found` — which is indistinguishable from category drift or permission issues without probing Syncthing state directly.

**Scope:** The Syncthing process on QNAP is a **single point of failure for the entire arr-stack import path.** Losing it silently blocks Lidarr + Sonarr + Radarr + Sportarr simultaneously with no immediate alert.

**Resolution:** `/etc/init.d/SyncThing.sh start` — Syncthing came up, connected to seedbox (`7UTBN2T`, 193.163.71.22:26401), began draining 393-file / ~751 GB backlog immediately.

**Recommended monitoring (WP-09d, D-17-112):**

| Monitor | Mechanism | Alert threshold |
|---|---|---|
| Syncthing REST reachability | Zabbix HTTP check to `http://192.168.10.201:8384/rest/system/ping` with API key header | Unreachable > 5 min → CRITICAL |
| Syncthing folder sync state | `GET /rest/db/status?folder=is5fj-3grur` → `state` field | `state=error` → CRITICAL |
| Pending files backlog | `needFiles` from folder status | `needFiles > 100` for > 1h → WARNING |
| Process-level (backup) | The existing staleness trigger | ≥ 48h without transfer → WARNING (already deployed) |

The REST reachability check is the highest-value add: it detects Syncthing down in <5 minutes, vs the current 48h staleness fallback.

**Implementation note:** The Zabbix trapper sender `scripts/syncthing-zabbix-sender.sh` already fetches from `http://192.168.10.201:8384/rest/...` — if Syncthing is down, the sender exits with a curl error. Adding a separate Zabbix external check (or HTTP item pointing directly at port 8384) would provide the fast-fail signal.

**Architectural note:** Long-term, consider a redundant transport (e.g., rclone SFTP from seedbox direct to QNAP as fallback) to eliminate the Syncthing SPOF. Short-term, WP-09d monitoring is the mitigation.
