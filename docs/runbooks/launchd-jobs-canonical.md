# Runbook — adding a launchd job (canonical, post-D-17-51)

Add a new `com.iap.*` LaunchDaemon (system domain, headless-safe) to
the platform.

## Authority and supersession

This runbook is the canonical reference for **adding** a new scheduled
launchd job post-D-17-51 (2026-05-03). It is the single source of
truth for plist authoring, install, verification, and rollback of a
new job.

The pre-existing `docs/runbooks/launchd-jobs.md` remains active for
the **fleet-wide** concerns it covers (inventory in §2, batch install
via `d-17-51-migrate-to-launchdaemons.sh` in §3, manual kickstart in
§4, recency-drift check in §5, modify/remove flows in §6/§7). This
runbook does not duplicate that material; it focuses on the
per-new-job authoring path.

## Why LaunchDaemon (system domain) on this host

Per `docs/architecture-facts/integration-audit-doctrine.md` Finding
15: on the headless Mac Mini, `launchctl print gui/<uid>` fails with
`Domain does not support specified action` (no active GUI session),
and `launchctl bootstrap user/<uid> <plist>` fails with `Bootstrap
failed: 5: Input/output error` even under sudo. LaunchAgents in
either user-facing domain are therefore **not a reliable unattended
substrate** on this host configuration.

Resolution: LaunchDaemons in the `system` domain with `UserName=admin`
applied per plist. This is the canonical path for any new unattended
`com.iap.*` job.

GUI-dependent jobs (Notification Center, screen capture, user-context
Keychain) cannot run as LaunchDaemons; see "When LaunchDaemon is the
wrong choice" below.

## Plist authoring shape

The two reference plists in `docker/launchd-agents/` exhibit the two
canonical command shapes:

- **Direct exec** (`com.iap.platform-registry.plist`) — `ProgramArguments`
  is a single-element array containing the script path. Use this when
  the script needs no shell features.
- **Shell-wrapped** (`com.iap.arr-apikey-sweep.plist`) — `ProgramArguments`
  is `[/bin/bash, -c, "<command>"]`. Use this when the command needs
  pipes, redirects, exit-code preservation, or an inline heartbeat
  `touch` after the script returns.

Required fields (taken verbatim from both reference plists):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.iap.<name></string>

    <key>ProgramArguments</key>
    <array>
        <!-- Direct-exec form: -->
        <string>/Users/admin/repos/integrated-ai-platform/scripts/<script>.sh</string>
        <!-- OR shell-wrapped form: -->
        <!-- <string>/bin/bash</string> -->
        <!-- <string>-c</string> -->
        <!-- <string>/path/to/script.sh &gt;&gt; /Users/admin/Library/Logs/iap/<name>.log 2&gt;&amp;1; rc=$?; touch /Users/admin/Library/Logs/iap/<name>.heartbeat; exit $rc</string> -->
    </array>

    <key>StartInterval</key>
    <integer><seconds></integer>
    <!-- OR <key>StartCalendarInterval</key><dict>…</dict> for wall-clock -->

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/admin/Library/Logs/iap/<short>.out.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/admin/Library/Logs/iap/<short>.err.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
```

Two notes on field uniformity vs source plists:

- `RunAtLoad=true` is present in `com.iap.platform-registry.plist`
  but absent in `com.iap.arr-apikey-sweep.plist`. Include it if you
  want the job to run once on bootstrap; omit if a scheduled-only
  cadence is correct for the work.
- `UserName=admin` and `GroupName=staff` are **not** authored in the
  source plist. They are applied by
  `scripts/d-17-51-migrate-to-launchdaemons.sh` at install time
  (lines 44–45 of that script). Do not add them to the source plist;
  the migration script is the single owner of that field.

## Canonical paths

| What | Where |
|---|---|
| Plist source (repo-tracked) | `docker/launchd-agents/com.iap.<name>.plist` |
| Plist install (runtime, root-owned) | `/Library/LaunchDaemons/com.iap.<name>.plist` |
| Stdout/stderr (post-migration) | `/Users/admin/Library/Logs/iap/com.iap.<name>.out.log` and `.err.log` |
| Heartbeat (touched by job script) | `/Users/admin/Library/Logs/iap/<short>.heartbeat` (no `com.iap.` prefix) |

The `<short>` form drops the `com.iap.` prefix — for label
`com.iap.foo`, the heartbeat is `…/foo.heartbeat`. This is the form
both `com.iap.arr-apikey-sweep.plist` and the verify script
(`scripts/d-17-51-verify-launchdaemons.sh` lines 27–38) use. The
**stdout/stderr** paths, by contrast, **do** carry the `com.iap.`
prefix because the migration script writes them as
`{label}.out.log` / `{label}.err.log` (lines 52–53 of the migration
script, where `label` is the full plist `Label` value).

Source-plist log paths in the two examples may differ from the
canonical post-migration paths (e.g.,
`com.iap.platform-registry.plist` writes to
`/Users/admin/.platform-registry/launchd.{stdout,stderr}.log`;
`com.iap.arr-apikey-sweep.plist` writes to
`/Users/admin/.platform-logs/arr-apikey-sweep.launchd.log`). The
migration script normalizes legacy `~/.platform-logs` paths in shell
commands (lines 56–59), but it **also** rewrites `StandardOutPath` /
`StandardErrorPath` to the canonical `iap/` directory regardless of
what the source plist held. For new jobs authored today, write the
canonical `/Users/admin/Library/Logs/iap/com.iap.<name>.{out,err}.log`
paths directly in the source plist; the normalization is then a
no-op.

## Install sequence (per-job)

For a single new job (the fleet-wide migrate script handles all jobs
at once; this is the per-job equivalent):

```bash
# 1. Copy plist to system-domain install location
sudo cp docker/launchd-agents/com.iap.<name>.plist /Library/LaunchDaemons/

# 2. Apply ownership and permissions required by launchd for system-domain plists
sudo chown root:wheel /Library/LaunchDaemons/com.iap.<name>.plist
sudo chmod 644 /Library/LaunchDaemons/com.iap.<name>.plist

# 3. Bootout any existing registration (best-effort; harmless if not loaded)
sudo launchctl bootout system/com.iap.<name> 2>/dev/null || true

# 4. Bootstrap into system domain
sudo launchctl bootstrap system /Library/LaunchDaemons/com.iap.<name>.plist

# 5. Enable at load (persists across reboots)
sudo launchctl enable system/com.iap.<name>

# 6. Kickstart immediately (does not wait for next schedule tick)
sudo launchctl kickstart -k system/com.iap.<name>
```

The four `launchctl` operations (bootout, bootstrap, enable, kickstart)
match the per-job loop in
`scripts/d-17-51-migrate-to-launchdaemons.sh` lines 84–87. Steps 1–2
mirror the script's pre-loop chown/chmod pass (lines 68–73); the
script does this in a batch, the per-job form does it inline.

## Verification

```bash
# Job loaded in system domain?
launchctl print system/com.iap.<name>
# Inspect output: state should be running | waiting (not exited),
# last exit code should be 0.

# Heartbeat file exists and is recent?
stat -f %m /Users/admin/Library/Logs/iap/<short>.heartbeat
# Compare to current epoch (`date +%s`) — age must be less than the
# job's expected interval plus margin.

# Fleet-wide health:
/Users/admin/repos/integrated-ai-platform/scripts/d-17-51-verify-launchdaemons.sh
```

The verify script enumerates every `com.iap*.plist` in
`/Library/LaunchDaemons/`, prints loaded/state/exit-code per job, and
flags heartbeat as `ok` / `stale` / `missing` against per-label
budgets. Per-label budgets are hard-coded in the script's
`budget_sec` function (lines 9–23); add an entry there when
introducing a new job whose default 86400 s budget is wrong.

## Pre-commit recency-hook integration

`scripts/check-repo-coherence.py launchd-recency` enforces that every
`com.iap.*.plist` in `docker/launchd-agents/` has a matching entry in
the `LAUNCHD_RECENCY_EXPECTATIONS` dict (defined at line 76 of that
script). A new plist added to the repo without an expectations entry
will fail the pre-commit hook with `in expectations but no plist` /
`missing in expectations` errors.

To add a new job's expectations entry:

```python
# scripts/check-repo-coherence.py — LAUNCHD_RECENCY_EXPECTATIONS
"com.iap.<name>": {
    "max_age_sec": <interval_seconds_with_grace>,
    "probe_paths": [
        "/Users/admin/Library/Logs/iap/<short>.heartbeat",
        "/Users/admin/.platform-logs/<short>.heartbeat",
    ],
},
```

The `probe_paths` list is searched in order; the first existing path
is used for mtime checks. The legacy `/Users/admin/.platform-logs/`
fallback exists for transition compatibility — keep both entries on
new jobs even though new heartbeats will land in the `iap/` path.

GUI-only / never-in-recency-check jobs go in
`LAUNCHD_RECENCY_EXEMPT_LABELS` (line 125) instead.

## Failure modes

### Heartbeat missing past budget

Most common failure. The job is registered in launchd but the
heartbeat file is absent or stale.

- Check `launchctl print system/com.iap.<name>` for `state` (should
  be `running` or `waiting`, not `exited`) and `last exit code`
  (should be 0). Non-zero exit means the script ran and failed —
  inspect the configured `StandardOutPath` / `StandardErrorPath`
  for cause.
- Verify the heartbeat `touch` is actually in the script (or in the
  `ProgramArguments` shell-wrapped form, as in
  `com.iap.arr-apikey-sweep.plist` line 11). A direct-exec form that
  doesn't internally touch the heartbeat will be silently absent
  even on success.
- Force a run: `sudo launchctl kickstart -k system/com.iap.<name>`,
  then re-check heartbeat mtime.

### Bootstrap I/O error (historical, user-domain attempts only)

`Bootstrap failed: 5: Input/output error` was the empirical block
that motivated the D-17-51 pivot (Finding 15). It only manifested on
`bootstrap user/<uid>`; system-domain bootstrap does not exhibit this
failure. If you see it, you are bootstrapping into the wrong domain
— re-issue against `system`, not `user/<uid>`.

### Exit-code persistence

`launchctl print system/<label>` shows `last exit code` from the most
recent run. Non-zero exits do **not** suppress the next scheduled
run; launchd re-runs on the next interval regardless. Treat
exit-code as observability only; the operational gate is the
recency-hook (`check-repo-coherence.py launchd-recency`) which
catches "job loaded but never producing fresh heartbeats".

## When LaunchDaemon is the wrong choice

Jobs that depend on user-session resources cannot run as
LaunchDaemons. The canonical example is `com.iap.d-17-27-reminder`,
which uses `osascript` to post a Notification Center alert and
requires GUI context. It is explicitly excluded from the migration
script (`EXCLUDE_LABELS` array, lines 24–26) and from the recency
hook (`LAUNCHD_RECENCY_EXEMPT_LABELS`, line 125).

Do not move a job to LaunchDaemon if it touches any of:

- Notification Center (`osascript display notification`)
- Screen capture / screenrecording APIs (TCC-gated, user-only)
- User-scoped Keychain (system Keychain is accessible from
  daemons; user Keychains are not)
- Active GUI window state (frontmost-app queries, accessibility APIs)

Such jobs remain LaunchAgents under `~/Library/LaunchAgents/` and
require a logged-in GUI session to run. They are out of scope for
this runbook.

## Rollback

```bash
# Unload from system domain (stops the job immediately)
sudo launchctl bootout system/com.iap.<name>

# Remove the installed plist
sudo rm /Library/LaunchDaemons/com.iap.<name>.plist

# If retiring the job entirely, also remove the repo source and
# update the recency-hook expectations dict:
rm docker/launchd-agents/com.iap.<name>.plist
# Edit scripts/check-repo-coherence.py — remove the matching entry
# from LAUNCHD_RECENCY_EXPECTATIONS (or add to LAUNCHD_RECENCY_EXEMPT
# if the job is being demoted to LaunchAgent rather than retired).
git add docker/launchd-agents/ scripts/check-repo-coherence.py
git commit -m "Retire com.iap.<name> launchd job"
```

For temporary disablement (job will return), stop at the first two
commands and leave the repo source in place.

## Cross-references

- `docs/architecture-facts/integration-audit-doctrine.md` Finding 15
  — empirical investigation of the headless launchd domain failure
  and the daemon-domain canonical resolution.
- `docs/runbooks/launchd-jobs.md` — fleet-level operations
  (inventory, batch migrate/verify, manual kickstart, modify, remove,
  drift-detection).
- `docs/phase-18/d-17-51/RESOLUTION_PLAN_2026-05-03.md` — D-17-51
  resolution context and the operator's single-sudo migration command.
- `scripts/d-17-51-migrate-to-launchdaemons.sh` — the batch migration
  primitive this runbook's per-job sequence is derived from.
- `scripts/d-17-51-verify-launchdaemons.sh` — fleet health check.
- `scripts/check-repo-coherence.py` — pre-commit recency hook
  enforcement.
