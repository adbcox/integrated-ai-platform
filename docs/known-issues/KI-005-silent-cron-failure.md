# KI-005 — 02:00 backup cron entry produces no log output

Severity: Sev-2 (data loss risk)
Surfaced: 2026-05-01 during D-16-04 T6
Status: Open; deliverable D-16-04.1 to follow

## Evidence
- `/Users/admin/logs/restic-backup.log` does not exist on disk
- crontab entry references this exact path with stdout redirect
- Even a failed cron run would create the file (redirect happens before
  the script runs)
- Implies cron daemon never spawned the backup process at all since the
  log path was last changed (D-15-03 crontab fix)

## Hypothesis
macOS cron has required Full Disk Access since Catalina. The cron
daemon at `/usr/sbin/cron` is likely not granted Full Disk Access in
System Settings → Privacy & Security, blocking it from writing to
`/Users/admin/*` paths. This would manifest as cron silently failing
to spawn the job entirely.

## Mitigation while pending D-16-04.1
D-16-04 ships the snapshot+backup integration. Operator-manual runs
via `bash scripts/backup.sh` work correctly (verified 2026-05-01,
Restic snapshot `b351273e`). Until cron is fixed, operator runs the
backup manually or via launchd plist.

## D-16-04.1 scope
1. Determine whether all three cron entries (backup + 2 strava) are
   silent or just backup
2. Investigate Full Disk Access status for `/usr/sbin/cron`
3. Either grant FDA + verify, or migrate cron entries to launchd
   plists (operator preference)
4. Add cron-recency check to `scripts/check-repo-coherence.py` so a
   silent cron failure cannot recur undetected
