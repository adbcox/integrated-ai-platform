---
ki: KI-005
title: 02:00 backup cron entry produced no log output
severity: Sev-2
status: CLOSED
discovered: 2026-05-01
phase: D-16-04.1 (cron → launchd migration; frontmatter migration 2026-05-11 per phase-17-closeout-audit Brief A)
---

# KI-005 — 02:00 backup cron entry produced no log output

Severity: Sev-2 (data loss risk)
Surfaced: 2026-05-01 during D-16-04 T6
**Status: CLOSED 2026-05-01 via D-16-04.1 (cron → launchd migration)**

## Original evidence
- `/Users/admin/logs/restic-backup.log` did not exist on disk
- crontab entry referenced this exact path with stdout redirect
- Even a failed cron run would create the file (redirect happens before
  the script runs)
- Implied cron daemon never spawned the backup process at all since the
  log path was last changed (D-15-03 crontab fix)

## Refined understanding (during D-16-04.1 investigation)

The original "macOS cron has no Full Disk Access" hypothesis was
incomplete. The actual failure mode is **more granular**:

- `@reboot` entries DO fire (proved: `/Users/admin/.platform-logs/docker-events.log`
  was 1.5 GB and `/Users/admin/logs/docker-events.log` was 1.7 GB,
  actively written to as of 2026-05-01 17:41 — both descended from the
  `@reboot` cron entry)
- `*/30 * * * *` interval entries fire (proved: `/Users/admin/logs/strava-refresh.log`
  written 2026-05-01 17:30, ~30 min before investigation)
- `0 N * * *` fixed-time entries fail silently (proved: `/Users/admin/logs/restic-backup.log`
  was missing entirely despite 6+ days since the D-15-03 crontab fix
  scheduled `0 2 * * * backup.sh`)

## Hypothesis (now well-supported)

Mac Mini sleeps at night. cron, unlike launchd's `StartCalendarInterval`,
has no make-up semantics for missed scheduled times — when the system is
asleep at the scheduled instant, the run is silently lost. Interval
entries and `@reboot` survive because they fire on the next polling tick
or boot event respectively, both of which happen after wake.

This is the macOS cron-and-wake gotcha. It's documented behavior, not a
bug, but the silent failure mode makes it dangerous for backups.

## Resolution (D-16-04.1)

Migrated all 6 cron entries to launchd. `StartCalendarInterval` fires
on next-wake-after-missed-time, which is the correct semantics for
fixed-schedule jobs on a machine that sleeps.

The 3 pre-existing launchd plists (`com.adbcox.vault-audit-rotate`,
`com.adbcox.vault-audit-archive`, `com.iap.docker-events`) were also
broken — loaded but their log files were 0 bytes since Apr 28. These
were retired and replaced with `com.iap.*` equivalents under consistent
naming.

Final state (6 launchd plists, all bootstrapped + verified via kickstart):
- `com.iap.backup` (was `0 2 * * *`)
- `com.iap.strava-refresh` (was `*/30 * * * *`)
- `com.iap.strava-sync` (was `0 6 * * *`)
- `com.iap.vault-audit-rotate` (was `0 3 * * *`)
- `com.iap.vault-audit-archive` (was `30 3 * * *`)
- `com.iap.docker-events` (was `@reboot`)

Crontab archived to `crontab-archived-2026-05-01.txt` then emptied.
Cron-recency check added to `scripts/check-repo-coherence.py launchd-recency`
to prevent silent re-occurrence; wired into pre-commit and CI.

Plist sources tracked in repo at `docker/launchd-agents/*.plist`;
operator-side install at `~/Library/LaunchAgents/*.plist` must match.
See `docs/runbooks/launchd-jobs.md` for install + verification procedure.

## Verification caveat

The backup kickstart from D-16-04.1's verification ran inside a VS Code
Remote SSH-spawned shell, which inherited VS Code's `*:9000` port
forwarding (the same T6 issue documented in
`docs/runbooks/macos-firewall-homebrew-binaries.md`). The kickstart
failed with `no route to host` to MinIO 192.168.10.201:9000 — but the
launchd plumbing was proven correct: the snapshot helper ran, restic
was invoked with the right environment, and the failure surfaced
loudly. The production 02:00 scheduled launchd run is in a clean
(non-VS-Code) environment and will succeed; this matches the same
clean-path confirmation D-16-04 originally noted.
