# D-17-51 — Finding Y resolution (PARTIAL)

Date: 2026-05-03
Status: PARTIAL (operator-run root bootstrap pending)

## What was proven

1. `gui/<uid>` is unavailable on this host (`Domain does not support specified action`) because no active GUI login session exists (headless server posture).
2. `user/<uid>` domain exists and is queryable (`launchctl print user/502` works).
3. Non-root bootstrap from this execution context fails globally with `Bootstrap failed: 5: Input/output error` (reproduced on both real and minimal probe plists).
4. Therefore the canonical pattern for this host is `user/<uid>` domain with privileged bootstrap execution.

## Deliverables added

- Root-run rollout script:
  - `scripts/d-17-51-launchagents-bootstrap-user-domain.sh`
- Verification script:
  - `scripts/d-17-51-launchagents-verify.sh`

## Operator execution sequence (single sudo invocation)

```bash
sudo /Users/admin/repos/integrated-ai-platform/scripts/d-17-51-launchagents-bootstrap-user-domain.sh \
  && /Users/admin/repos/integrated-ai-platform/scripts/d-17-51-launchagents-verify.sh
```

Expected:
- bootstrap script summary reports `fail=0`
- verify script shows `loaded=yes` for affected agents
- heartbeats move into-budget after first scheduled/manual run

## Affected critical-path agents

- `com.iap.buildarr-sync`
- `com.iap.arr-apikey-sweep`
- `com.iap.platform-registry`
- `com.iap.docker-events`
- `com.iap.strava-refresh`
- `com.iap.backup`
- plus remaining `com.iap.*` entries present in `~/Library/LaunchAgents`

## Remaining gate to close D-17-51

- Operator executes the root bootstrap script once on-host.
- Post-run verification evidence captured via `d-17-51-launchagents-verify.sh`.
- Then Finding Y can be marked RESOLVED and dependent backlog items (e.g., persistent SMB mount agentization) can proceed.
