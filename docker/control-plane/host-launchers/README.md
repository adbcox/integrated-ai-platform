# control-plane host-launchers

Host-side scripts that the operator control plane dispatches to for
operations requiring elevated credentials. Per Block 2.5 doctrine
(D8), the control-plane container never holds:

- Vault root token (lives at `~/.vault-token`)
- Direct `docker exec` privileges (lives implicitly with the
  operator's local docker socket)
- The `backup` AppRole's role-id / secret-id (lives at
  `~/.vault-approle/backup/`)

Instead, control-plane writes a *trigger file* to a shared volume.
A host-side launchd-managed watcher picks it up, validates a
timestamp + nonce, runs the matching `iap-<action>-trigger` script,
writes the result back, and deletes the trigger.

## Install

```bash
# 1. Trigger directory (shared with control-plane via bind mount)
mkdir -p /Users/admin/iap-triggers/results
chmod 0700 /Users/admin/iap-triggers /Users/admin/iap-triggers/results

# 2. Launcher scripts
sudo install -m 0755 iap-trigger-watcher.sh        /usr/local/bin/
sudo install -m 0755 iap-backup-trigger.sh         /usr/local/bin/
sudo install -m 0755 iap-regression-probe-trigger.sh /usr/local/bin/

# 3. Launchd job — runs as the operator's user (admin), not root
cp com.iap.control-plane.trigger-watcher.plist \
   ~/Library/LaunchAgents/
launchctl load -w \
   ~/Library/LaunchAgents/com.iap.control-plane.trigger-watcher.plist

# 4. Verify
launchctl list | grep com.iap.control-plane
tail -F /Users/admin/iap-triggers/watcher.log
```

## Protocol

### Trigger file (control-plane → host)

Path: `/Users/admin/iap-triggers/<action>-<uuid>.json` (mode 0600).

```json
{
  "nonce": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-04-28T20:15:00Z",
  "action": "backup-trigger",
  "params": {}
}
```

### Validation (host watcher)

The watcher rejects a trigger and writes a `.rejected.json` if any of:

- Timestamp is outside ±30s of host clock (replay defense /
  clock-skew protection)
- Nonce already in the recent-nonce cache (last 300 s)
- Action is not in the allowlist (`backup-trigger`,
  `regression-probe`, `credential-rotate`)
- JSON is malformed

Rejected triggers do NOT execute. The reason is written to the
rejection file and to `watcher.log`. Both control-plane and the
operator can grep `watcher.log` for the rejection reason.

### Result file (host → control-plane)

Path: `/Users/admin/iap-triggers/results/<uuid>.json` (mode 0600).

```json
{
  "nonce": "550e8400-e29b-41d4-a716-446655440000",
  "exit_code": 0,
  "started_at": "2026-04-28T20:15:00Z",
  "finished_at": "2026-04-28T20:18:02Z",
  "stdout_tail": "...",
  "stderr_tail": "...",
  "structured": { ... }
}
```

control-plane polls for the result file by uuid, reads it, and
deletes it.

### Allowlisted actions

| Action | Wrapper | Purpose |
|---|---|---|
| `backup-trigger` | `iap-backup-trigger.sh` | runs `scripts/backup.sh` (uses `backup` AppRole) |
| `regression-probe` | `iap-regression-probe-trigger.sh` | runs `docs/phase-13/h1-regression-probe.sh <gate-id>` |
| `credential-rotate` | `iap-credential-rotate-trigger.sh` | Phase 3; per-service rotation script dispatch |

Adding a new action requires editing both the watcher's allowlist
and `app/triggers.py:ALLOWED_ACTIONS`.

## Why this pattern (and not the alternatives)

| Alternative | Rejected because |
|---|---|
| Mount `~/.vault-token` into control-plane | Hands out root token; collapses entire trust model |
| Mount `/var/run/docker.sock` into control-plane | Allows `docker exec`, image pulls, network operations beyond allowlist; we use a hardened proxy for the *limited* Docker surface we DO expose |
| Run the watcher inside a docker container | Container would need the same elevated creds we are trying to keep out of containers; circular |
| Direct SSH from control-plane container to host | Requires SSH key inside container; same trust problem |
| systemd path-based activation | Mac, no systemd |

launchd watching a trigger directory keeps the secrets on the host
where they already live, and the control-plane container stays
unprivileged.
