# ADR-A-017 — Vault file-backend warm-copy is the backup strategy

**Status:** Accepted
**Date:** 2026-05-01
**Phase:** 16
**Supersedes:** Phase 15 closeout language "use `vault operator raft snapshot save`" (verbatim from `docs/phase-15/PHASE_15_CLOSEOUT_2026-05-01.md` Carry-overs section)

## Context

Phase 15 closeout left Vault data outside the Restic backup chain.
`scripts/backup.sh` had a guarded branch that included
`/var/lib/docker/volumes/vault_vault-data/_data` only when readable by
`admin`; in Colima that path is root-owned and the branch never fired.
The closeout phrased the fix as "the right fix is `vault operator raft
snapshot save` integration, not raw volume read."

That phrasing rests on a wrong premise. Vault is on the **file**
storage backend, not raft. Confirmed against `vault-config.hcl`:

```hcl
storage "file" {
  path = "/vault/data"
}
```

`vault operator raft snapshot save` only works against the integrated
storage (raft) backend. Running it on the file backend returns
`storage backend is not raft`. The closeout's prescribed fix is
therefore unimplementable without a separate backend migration.

The data must be in the backup chain regardless. Three options:

  1. **Warm copy** — `cp -a` the BoltDB-backed `/vault/data` tree
     into a host-readable landing zone while Vault is running.
     Crash-consistent (BoltDB recovers partial writes on next start).
  2. **Cold copy** — seal Vault, copy, unseal. Transaction-consistent
     but touches the seal cycle on every backup run.
  3. **Migrate to raft backend** — separate change, separate ADR, weeks
     of work. Out of scope.

The 2026-04-30 cascade incident (Sev-2 KV mount data loss + seal-vault
data volume destruction during a 9-hour autonomous-debug window) makes
option 2 unacceptable as a routine operation. Routine backups must
**never** touch Vault's seal cycle. Option 3 is correct in the long
run but is its own deliverable, not a backup-chain blocker.

## Decision

Use **option 1 (warm copy)** as Vault's backup strategy through the
next storage-backend evaluation. Implementation:

- `scripts/vault-snapshot-warm.sh` produces an atomic warm copy of
  `/vault/data` into `/Users/admin/.vault-snapshot/current/` via a
  bind mount on the `vault-server` container. Stage → verify → atomic
  rename ensures a partially-written tree never replaces a good
  `current/`.
- `scripts/backup.sh` invokes the helper as its first action; on
  success the snapshot path is appended to `BACKUP_DIRS`. Helper
  failure is **warn-and-continue** — the rest of the platform
  (repo, Home Assistant, etc.) still backs up.
- Restore procedure is unchanged in shape: stop vault-server, replace
  `/vault/data` from the restored tree, start vault-server, unseal
  (auto via Transit). Updated in `docs/runbooks/vault-restore-from-
  backup.md` to reference the snapshot source path inside Restic.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Cold copy (seal/copy/unseal) | Touches Vault's seal cycle on every backup. Post-Phase-15 incident, unacceptable as routine. |
| Migrate to raft backend, then `raft snapshot save` | Correct long-run; orthogonal to "data must be in backup chain today." Tracked as backlog. |
| Skip Vault from backups entirely | Restore-from-incident requires re-initialising every AppRole + KV path. Unacceptable RTO. |
| Run `restic` inside the container as `vault` uid | Adds restic + AWS credentials to the Vault container's image — broader attack surface than a host-side read. |

## Consequences

- **Crash-consistent, not transaction-consistent.** A warm copy may
  capture Vault mid-transaction. BoltDB's recovery semantics roll
  forward/back automatically on next start, so the worst case on
  restore is "same state as a power loss" — recoverable without
  operator intervention.
- **Routine backup never touches Vault's seal cycle.** The seal-vault
  cascade-failure path is now strictly orthogonal to backup operations.
- **Snapshot landing zone holds an admin-readable copy of secrets at
  rest.** `/Users/admin/.vault-snapshot/` is mode 0700, owned admin.
  The contents are no more sensitive than the Restic remote itself
  (which is encrypted) but operators must treat the directory as
  Vault-equivalent and never `chmod 755` it.
- **Raft migration becomes its own deliverable.** When the platform
  moves to raft (e.g. for HA across Mac Mini + Mac Studio), this ADR
  is superseded by a new one and `vault operator raft snapshot save`
  becomes the canonical backup mechanism.
- **First snapshot adds ~3 MB to each Restic backup** (697 files for
  the current Vault state). Restic's content-addressable dedup keeps
  daily growth proportional to actual change rate, not total tree size.

## Related

- ADR-A-006 — repo as canonical source of truth
- ADR-A-009 — Vault as authoritative secret store
- `docs/runbooks/vault-restore-from-backup.md` — restore procedure
- `docs/phase-15/PHASE_15_CLOSEOUT_2026-05-01.md` Carry-overs — original framing
- `docs/phase-15/PHASE_15_KV_LOSS_2026-04-30.md` — Sev-2 incident postmortem motivating the seal-cycle constraint
