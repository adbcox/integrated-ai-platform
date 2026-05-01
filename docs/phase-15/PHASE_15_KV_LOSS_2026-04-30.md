# Phase 15 — Vault KV Data Loss Incident

**Date:** 2026-04-30 (discovered ~22:00 local during Phase 16 follow-on recovery)
**Severity:** Sev-2 (data loss — recoverable by rebuild, no permanent platform damage)
**Author:** Adrian Cox + Claude Code session
**Status:** STOPPED FOR MORNING RECOVERY — no rebuild attempted in-session

---

## Executive Summary

Today's 14:52 "fresh-init" Vault recovery attempt did not just rebuild AppRoles — it **wiped the entire KV `secret/` mount**. This was not surfaced at the time. It was discovered tonight after re-issuing AppRole credentials and observing that sidecars authenticated successfully but every template render failed with `no secret exists at secret/data/<service>/<path>`.

Investigation of Restic backups confirmed **no recoverable backup exists**: the nightly backup cron has fired three times (Apr 28–30) but every run failed at the shell redirect with `Permission denied` before `backup.sh` body ever executed. There is no Restic repository on local disk, and the Vault entries that would have stored the repo password (`secret/restic/backup`) and MinIO credentials (`secret/minio/backup`) are themselves empty post-wipe.

**Conclusion:** ~17 service secrets must be rebuilt from source tomorrow. The session was stopped before any further destructive operations (Transit rebuild was queued but not executed).

## Discovery Chain

1. Phase 16 5-block work completed cleanly. Earlier `api_addr` network incident postmortem written (`PHASE_15_VAULT_API_ADDR_NETWORK_INCIDENT_2026-04-30.md`).
2. Operator approved a "vault unseal + sidecar restart" sequence.
3. Manual Shamir unseal with new keys (`~/vault-init-keys-NEW-20260430.txt`) succeeded.
4. Sidecar restart attempted — sidecars came up but `credentials.env` files did not refresh.
5. Sidecar logs revealed `permission denied` on AppRole login: AppRole role-id/secret-id files on host were stale (Apr 28/29) but Vault had been re-initialized at 14:52 today.
6. Re-issued all 29 AppRole credentials via root token loop. Result: `ok=29 fail=`. Backup of pre-existing AppRole files at `~/.vault-approle.backup-20260430-214643`.
7. Restarted all 27 running sidecars. Only 2 of ~27 expected `credentials.env` files re-rendered.
8. Logs from `vault-agent-control-plane` showed:
   ```
   WARN agent: (view) vault.read(secret/data/control-plane/operator):
     no secret exists at secret/data/control-plane/operator
     (retry attempt 7 after "16s")
   ```
   AppRole auth was working — sidecars had tokens. The KV data they read was missing.
9. KV mount listing (root token) showed only 12 surviving paths out of 25+ expected.
10. Restic investigation: cron exists, mail-spool shows three firings, but every firing died at the log redirect (`/var/log/restic-backup.log: Permission denied`) before `backup.sh` ran. No repo exists. No restoration is possible.

## What Was Wiped

### Surviving KV paths (12)
These exist because they were re-populated (manually or by service init) between the 14:52 wipe and tonight:
```
github/, homeassistant/, minio, plane/, plex/, prowlarr/,
qnap/, radarr/, restic, seedbox/, sonarr/, strava/
```

Note: `restic` and `minio` are listed but their leaf data is empty — the parent metadata exists, the values do not. Verified:
```bash
$ curl -s -H "X-Vault-Token: $ROOT" .../v1/secret/data/restic/backup
{"errors": []}
$ curl -s -H "X-Vault-Token: $ROOT" .../v1/secret/data/minio/backup
{"errors": []}
```

### Lost KV paths — must rebuild (17+ services)

| Path | Type | Source for rebuild |
|---|---|---|
| `secret/control-plane/operator` | auto-gen password | `openssl rand -hex 32` |
| `secret/control-plane/backup` | auto-gen password | `openssl rand -hex 32` |
| `secret/grafana/admin` | auto-gen password | `openssl rand -hex 32`; reset Grafana admin from container env |
| `secret/inventree/db` | auto-gen password | regenerate; rotate Postgres password |
| `secret/inventree/secret-key` | auto-gen | `openssl rand -hex 50` |
| `secret/litellm/master-key` | auto-gen | `openssl rand -hex 32` |
| `secret/litellm/db` | auto-gen | regenerate; rotate Postgres |
| `secret/mcpo/api-key` | auto-gen | `openssl rand -hex 32` |
| `secret/netbox/db` | auto-gen | regenerate; rotate Postgres |
| `secret/netbox/secret-key` | auto-gen | `openssl rand -hex 50` |
| `secret/netbox/superuser` | auto-gen | `openssl rand -hex 24`; reset via `manage.py changepassword` |
| `secret/nextcloud/db` | auto-gen | regenerate; rotate Postgres |
| `secret/nextcloud/admin` | auto-gen | reset via `occ user:resetpassword admin` |
| `secret/obot/db` | auto-gen | regenerate; rotate Postgres |
| `secret/openhands/*` | mixed | check OpenHands compose for required keys |
| `secret/openwebui/secret-key` | auto-gen | `openssl rand -hex 32` |
| `secret/plex-mcp/token` | external | re-issue via Plex account UI |
| `secret/vaultwarden/admin-token` | auto-gen | `openssl rand -hex 32` |
| `secret/zabbix/db` | auto-gen | regenerate; rotate Postgres |
| `secret/zabbix/web` | auto-gen | reset Zabbix admin via DB or UI |
| `secret/zabbix/api` | API token | re-issue via Zabbix UI after web admin reset |
| `secret/headscale/oidc-client-secret` | external | re-issue via OIDC provider UI (if used) |
| `secret/restic/backup` | new repo | re-init repo with fresh password (see backup-script bug below) |

### Already-rebuilt today (not in scope tomorrow)

- All 29 AppRoles (`role-id` + `secret-id`) — completed tonight, files at `~/.vault-approle/<svc>/`, backup at `~/.vault-approle.backup-20260430-214643`.

## Root Cause: Backup Script Permission Bug

```cron
0 2 * * * /Users/admin/repos/integrated-ai-platform/scripts/backup.sh >> /var/log/restic-backup.log 2>&1
```

The cron user (`admin`) cannot write to `/var/log/` on macOS without sudo. The shell redirect fails before `backup.sh` ever launches. Three nightly firings, three silent (mail-spool-only) failures. The platform has been operating without backups since the Restic backup policy was introduced.

This needs fixing as a P0 before any further fresh-init / rebuild operations:

```bash
# Fix candidate (subject to morning review)
0 2 * * * /Users/admin/repos/integrated-ai-platform/scripts/backup.sh >> /Users/admin/Library/Logs/restic-backup.log 2>&1
```

Plus: `backup.sh` should `mkdir -p "$(dirname "$LOG_FILE")"` and write its own log instead of relying on cron's redirect.

Plus: backup script should fail loudly if the repo is uninitialized — currently line 89-92 silently calls `restic init`, which masks "we have no repo to restore from" with "we have a repo we just made (and never tested)."

## What Was NOT Done Tonight (intentionally stopped)

(See `## Transit Auto-Unseal Rebuild — DONE (post-stop)` below — operator overrode this section after the initial pause and the Transit rebuild was completed successfully.)

Original rationale for stopping (preserved for the audit trail):

1. The KV mount is empty. Auto-unseal mechanism is independent of KV data, but rebuilding Transit on top of an empty platform with no working services serves no purpose.
2. Doing 17 manual secret rebuilds at midnight is exactly the failure mode that got us here today. The operating doctrine rule applies:
   > **"Stop on any unexpected behavior; surface to user."**
3. Vault is currently in a known state: unsealed via Shamir, AppRoles working, KV mostly empty. This is recoverable in daylight.

## Transit Auto-Unseal Rebuild — DONE (post-stop)

After the operator overrode the pause with explicit "EXECUTE TRANSIT REBUILD NOW" direction, the rebuild completed successfully. Final state:

- `Seal Type: transit` ✅
- `Recovery Seal Type: shamir` (5 recovery keys retained for `generate-root` emergencies)
- `Sealed: false`
- Auto-unseal verified across **two consecutive `docker restart vault-server` cycles** — log signature `core: unsealed with stored key` on each.
- seal-vault audit log shows clean `transit/encrypt/autounseal` and `transit/decrypt/autounseal` request/response pairs.

### Sequence executed

1. Stopped vault-server (was unsealed via Shamir; healthy).
2. Backed up seal-vault data volume to `~/seal-vault-data.pre-rebuild-20260430.tgz` (19 KB).
3. Removed stopped seal-vault container; deleted both `seal-vault_seal-vault-data` and `seal-vault_seal-vault-logs` volumes.
4. Started fresh seal-vault. **Hit permission error** on `/vault/data` — fix: `docker run alpine chown -R 100:1000 /vault/data` because compose has `SKIP_CHOWN: "true"`.
5. Initialized seal-vault with `vault operator init -key-shares=1 -key-threshold=1`. Saved keys to `~/seal-vault-init-keys-20260430.json` (mode 600).
6. Unsealed seal-vault.
7. `vault secrets enable transit` on seal-vault.
8. `vault write -f transit/keys/autounseal` — created the AES-256-GCM96 encryption key.
9. Wrote scoped policy `autounseal` (update on `transit/encrypt/autounseal` and `transit/decrypt/autounseal` only).
10. Generated periodic auth token (`-period=24h -orphan -policy=autounseal`). Saved to `~/vault-server-autounseal-token-20260430.json`.
11. Wrote bare token to `~/control-center-stack/stacks/vault/autounseal-token` (95 bytes, no trailing newline). sha256 prefix `a0db2412668d` (was `4dc8ad84af6b`).
12. Added `seal "transit" { ... }` stanza to `vault-config.hcl`.
13. **Discovered Vault 2.0 does not support `token_file` in the seal "transit" stanza.** Verified against developer.hashicorp.com/vault/docs/configuration/seal/transit — the docs use inline `token = "..."` (discouraged) or `VAULT_TOKEN` env var (recommended). Vault silently ignored the unknown `token_file` field, sent unauthenticated `transit/encrypt/autounseal` requests, and seal-vault correctly returned 403.
14. Removed `token_file` from seal stanza. Modified vault-server compose `command:` to read the token from the mounted file and export it as `VAULT_TOKEN` before exec'ing vault:
    ```yaml
    entrypoint: ["/bin/sh", "-c"]
    command: ['VAULT_TOKEN="$$(cat /vault/config/autounseal-token)" exec vault server -config=/vault/config']
    ```
    Keeps the token out of HCL, out of `docker inspect`, and out of process-table — only present in the bind-mounted file.
15. Tried `seal "shamir" { disabled = "true" }` for migration — Vault 2.0 rejects with "shamir seals cannot be set disabled". Removed; not required for 2.0.
16. Restarted vault-server. Vault correctly entered seal-migration mode: `core: entering seal migration mode; from_barrier_type=shamir to_barrier_type=transit`.
17. Submitted 3 of 5 Shamir keys with `vault operator unseal -migrate`. Migration completed; `Seal Type` flipped from `shamir` to `transit`; original Shamir keys are now `Recovery` keys.
18. Verified auto-unseal across two restart cycles. Both succeeded with `core: unsealed with stored key`.

### Files touched (out-of-repo `~/control-center-stack`)

- `~/control-center-stack/stacks/vault/vault-config.hcl` — added Transit seal stanza
  - Pre-rebuild backup: `vault-config.hcl.pre-transit-20260430`
- `~/control-center-stack/stacks/vault/docker-compose.yml` — wrapper command for VAULT_TOKEN
- `~/control-center-stack/stacks/vault/autounseal-token` — replaced
  - Pre-rebuild backup: `autounseal-token.pre-rebuild-20260430`

### Files created (home dir, mode 0600)

- `~/seal-vault-init-keys-20260430.json` — seal-vault unseal key + root token
- `~/vault-server-autounseal-token-20260430.json` — vault-server's Transit auth token
- `~/seal-vault-data.pre-rebuild-20260430.tgz` — pre-rebuild seal-vault volume backup

### What auto-unseal does NOT solve

Tonight's rebuild fixed the seal mechanism. The platform is **still degraded** because:
- KV mount is still mostly empty (~17+ secrets missing — see lost-paths table above).
- Most sidecars are still failing template renders with `no secret exists at secret/data/<svc>/...`.
- Most consumer services are still failing health/auth.

The morning recovery plan below is unchanged: **rebuild secrets**, then test sidecars, then take a verified Restic snapshot.

## Recovery Plan for Morning

**Order matters** — do these in sequence, not parallel:

1. **Fix the backup script first.** Move log to user-writable path; add explicit "no repo, abort" check rather than auto-init. Test one manual run end-to-end and verify a snapshot lands.
2. **Take a Restic snapshot of current Vault state.** Even half-empty, it's a baseline. If the next rebuild attempt goes wrong, we can roll back to "12 surviving paths plus AppRoles."
3. **Rebuild auto-gen secrets in bulk** (all `openssl rand` items above). Use a single script that writes them to Vault and updates dependent services in one pass.
4. **Rebuild Postgres-rotation secrets per service.** For each of inventree-db, litellm-db, netbox-db, nextcloud-db, obot-db, zabbix-db: `ALTER USER ... PASSWORD '...';` in the running container, then write to Vault, then restart the sidecar, then restart the consumer.
5. **External token re-issues last** (Plex, OIDC if any).
6. **Verify all 27 sidecars rendering credentials.env fresh.**
7. **Then** Transit auto-unseal rebuild — once the platform is back to known-good baseline.
8. **Then** snapshot again. Keep two known-good snapshots before any further structural work.

## Files & References

- Pre-existing AppRole backup: `~/.vault-approle.backup-20260430-214643`
- Current root token: `~/vault-init-keys-NEW-20260430.txt` (5 unseal keys + 1 root token)
- Earlier today's `api_addr` postmortem: `docs/phase-15/PHASE_15_VAULT_API_ADDR_NETWORK_INCIDENT_2026-04-30.md`
- Backup script needing fix: `scripts/backup.sh`
- Backup AppRole policy (orphaned tonight): `config/vault-policies/backup-policy.hcl`

## Lessons

### L1 — A backup that has never been verified is not a backup

The cron job was added per H1 §2 doctrine and never tested. Three nights of silent failure went unnoticed because no one watched the mail spool, no monitoring alarmed on missing snapshots, and no quarterly restore test (per CLAUDE.md backup policy) had yet occurred. **Backup verification must be a Day-1 acceptance gate, not a Day-30 quarterly task.**

### L2 — "Fresh init" is destructive and must be labeled as such in the runbook

Today's three recovery attempts (13:58, 14:26, 14:52) escalated from "rotate keys" to "fresh init" without an explicit operator confirmation step that surfaced *what fresh-init means* (= "delete everything"). The runbook for vault-restore needs a "DESTRUCTIVE — erases all KV data, all policies, all auth methods" warning at the fresh-init step, plus a mandatory pre-confirmation that backup exists and has been recently verified.

### L3 — Sidecar restarts surface KV state

Tonight's sequence — re-issue AppRoles, restart sidecars, see "no secret exists" errors — is exactly the right diagnostic to detect post-wipe data loss. **Sidecar restart should be part of any post-recovery verification gate.** A vault that comes back unsealed but with no consumers re-rendering credentials is not recovered.

### L4 — Stop-and-surface saved hours of bad work

Re-running Path 1 on autopilot or executing the Transit rebuild on top of an empty KV would have spent 90+ minutes producing no usable platform state. Stopping at the surface ("KV is empty, no backup exists, deferring to morning") is the right call by the operating doctrine.

## Action Items

| # | Item | Owner | Due |
|---|---|---|---|
| 1 | Fix `scripts/backup.sh` log redirect (writable path + script-internal logging) | Adrian | Morning, before any rebuild |
| 2 | Manual test of fixed backup.sh; verify snapshot lands | Adrian | Morning |
| 3 | Bulk rebuild of auto-gen secrets (script-driven, single pass) | Adrian + Claude | Morning |
| 4 | Postgres password rotations per service | Adrian + Claude | Morning |
| 5 | External token re-issues (Plex, OIDC) | Adrian | Morning (UI work) |
| 6 | Verify all sidecars rendering credentials.env | Claude | Morning |
| 7 | ~~Transit auto-unseal rebuild~~ — **DONE 2026-04-30 ~22:18** (see "Transit Auto-Unseal Rebuild — DONE" section above) | — | — |
| 8 | Document destructive runbook step in vault-restore-from-backup.md | Adrian | Phase 15 |
| 9 | Add "backup verified within 7 days" gate to phase-close checklist | Adrian | Phase 15 |
