# D-17-51 — Finding Y Resolution via LaunchDaemon Pivot

Date: 2026-05-03
Status: READY FOR OPERATOR EXECUTION (sudo required)

## Empirical conclusion

- `gui/<uid>` domain is unavailable in headless posture (`Domain does not support specified action`).
- `user/<uid>` domain exists (`session=Background`) but `bootstrap user/<uid>` fails with `Input/output error` even under sudo for this agent set.
- Therefore LaunchAgents are not a reliable unattended substrate on this host configuration.

## Canonical resolution

Pivot from LaunchAgents to LaunchDaemons in `system` domain, with `UserName=admin` on each migrated plist.

## Migration artifacts

- `scripts/d-17-51-migrate-to-launchdaemons.sh`
  - Converts `~/Library/LaunchAgents/com.iap*.plist` to `/Library/LaunchDaemons/com.iap*.plist`
  - Applies `UserName=admin`, `GroupName=staff`
  - Excludes GUI-dependent `com.iap.d-17-27-reminder`
  - Normalizes heartbeat/log paths from `/Users/admin/.platform-logs` to `/Users/admin/Library/Logs/iap`
  - Bootout/bootstrap/enable/kickstart in `system` domain

- `scripts/d-17-51-verify-launchdaemons.sh`
  - Verifies `system/<label>` loaded/state/last-exit
  - Reports heartbeat recency vs budget

## Operator command sequence (single sudo invocation preferred)

```bash
sudo /Users/admin/repos/integrated-ai-platform/scripts/d-17-51-migrate-to-launchdaemons.sh \
  && /Users/admin/repos/integrated-ai-platform/scripts/d-17-51-verify-launchdaemons.sh
```

## Expected post-run indicators

- `summary ... fail=0` from migration script
- Verification shows `loaded=yes` for critical unattended agents:
  - `com.iap.buildarr-sync`
  - `com.iap.arr-apikey-sweep`
  - `com.iap.platform-registry`
  - `com.iap.docker-events`
  - `com.iap.strava-refresh`
  - `com.iap.backup`

## Notes

- GUI/session-dependent reminder agent is intentionally left as LaunchAgent.
- No TCC/FDA changes required for this pivot.
