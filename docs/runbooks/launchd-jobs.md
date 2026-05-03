# Runbook — launchd-managed scheduled jobs

**Status:** Active doctrine (replaces cron, established D-16-04.1 2026-05-01; headless pivot D-17-51 2026-05-03)
**Scope:** All `com.iap.*` launchd jobs in `/Library/LaunchDaemons/` (runtime), sourced from `docker/launchd-agents/`

## §1 — Why launchd not cron

macOS cron has a silent-failure mode for fixed-time entries when the
system is asleep at the scheduled time. There is no make-up semantics:
a missed run is silently lost, no error, no log line.

launchd's `StartCalendarInterval` fires on the next wake after a
missed scheduled time. For a Mac Mini that sleeps overnight, this is
the correct semantics for a job scheduled at 02:00.

Full investigation in `docs/known-issues/KI-005-silent-cron-failure.md`.

## §2 — Inventory

The 6 `com.iap.*` plists managed by this platform:

| Label | Schedule | Script |
|---|---|---|
| `com.iap.backup` | Daily 02:00 | `scripts/backup.sh` |
| `com.iap.strava-refresh` | Every 1800s | `scripts/refresh-strava-token.sh` |
| `com.iap.strava-sync` | Daily 06:00 | `scripts/sync-strava-to-calendar.py` |
| `com.iap.vault-audit-rotate` | Daily 03:00 | `~/.platform-scripts/vault-audit-rotate.sh` |
| `com.iap.vault-audit-archive` | Daily 03:30 | `~/.platform-scripts/vault-audit-archive.sh` |
| `com.iap.docker-events` | RunAtLoad + KeepAlive | `docker events` log capture |

Plist source-of-truth: `docker/launchd-agents/com.iap.*.plist` (this
repo). Active runtime copy on operator's Mac at `/Library/LaunchDaemons/`
with `UserName=admin` applied by the migration script.

## §3 — Install / re-install (headless canonical)

```bash
# Single command (converts LaunchAgents -> LaunchDaemons + bootstraps system domain)
sudo /Users/admin/repos/integrated-ai-platform/scripts/d-17-51-migrate-to-launchdaemons.sh \
  && /Users/admin/repos/integrated-ai-platform/scripts/d-17-51-verify-launchdaemons.sh
```
Expected: migration summary with `fail=0`, then verify table with
`loaded=yes` for migrated services.

## §4 — Manual run (kickstart)

```bash
sudo launchctl kickstart -kp system/<label>
```

`-k` kills any existing run, `-p` prints the new PID. Tail the job's
configured `StandardOutPath` to see output.

**Caveat:** if you kickstart from a VS Code Remote SSH session, jobs
that connect to LAN services (e.g., backup → MinIO at 192.168.10.201:9000)
may fail with `no route to host`. VS Code's auto-port-forwarding
intercepts. See `docs/runbooks/macos-firewall-homebrew-binaries.md`.
The scheduled run is in a clean system-launchd environment and is unaffected.

## §5 — Recency / drift detection

Run:

```bash
python3 scripts/check-repo-coherence.py launchd-recency
```

Asserts each known job last ran within its expected interval. Wired
into pre-commit and CI under D-16-06's drift-detection model.

## §6 — Modifying a job

1. Edit `docker/launchd-agents/<label>.plist` in the repo
2. `plutil -lint` it
3. Re-run `scripts/d-17-51-migrate-to-launchdaemons.sh` (sudo)
4. `sudo launchctl kickstart -kp system/<label>` to verify
5. Commit the repo change

Never edit `/Library/LaunchDaemons/` directly without updating the repo
source plist and re-running the migration script.

## §7 — Removing a job

1. `sudo launchctl bootout system/<label>`
2. Delete `/Library/LaunchDaemons/<label>.plist`
3. Delete the repo source `docker/launchd-agents/<label>.plist`
4. Update the inventory in §2 of this runbook
5. Update `scripts/check-repo-coherence.py launchd-recency` expected list

## §8 — References

- `docs/known-issues/KI-005-silent-cron-failure.md` — root cause
- `docs/runbooks/macos-firewall-homebrew-binaries.md` — VS Code port-fwd caveat
- `docs/runbooks/drift-detection.md` — D-16-06 model that wraps §5 check
- `docs/PROJECT_FRAMEWORK.md` §3.5 — D#15 (preflight gate runs §5 check)
- `docker/launchd-agents/` — tracked plist sources
- `docs/known-issues/crontab-archived-2026-05-01.txt` — pre-migration cron snapshot
