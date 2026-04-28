# Post-H1 Backup "Repair" — actually a false alarm

**Date**: 2026-04-28
**Status**: NO REPAIR NEEDED. Audit's BLOCKER finding was a probe-script error, not a real platform issue.

## What the audit reported

`docs/phase-13/PRE_BLOCK_2_READINESS_AUDIT_2026-04-28.md` reported:
> Restic backup auth broken (MinIO Access Key Id mismatch) — BLOCKER

The audit's verification probe ran `vault kv get -field=username secret/minio/backup` and `-field=password`. Both returned **error messages** (field doesn't exist) which the probe then passed to restic as `AWS_ACCESS_KEY_ID`. MinIO correctly rejected the bogus keys. The probe interpreted this rejection as "MinIO auth broken".

## Actual state

`secret/minio/backup` field structure is `access_key, endpoint, secret_key` — NOT `username/password`. The actual `scripts/backup.sh` correctly reads:
```bash
AWS_ACCESS_KEY_ID=$(vault_get minio/backup access_key)
AWS_SECRET_ACCESS_KEY=$(vault_get minio/backup secret_key)
```

Manual run of `scripts/backup.sh` completed cleanly:
- Snapshot `e608e7d4` created at 2026-04-28 16:08:33
- Forget retention applied (1 old snapshot removed; prune ran)
- Repository repacking + index rebuild completed

## Verification

```
$ restic snapshots latest
ID        Time                 Host               Tags    Paths                          Size
e608e7d4  2026-04-28 16:08:33  mac-mini.internal  daily   /Users/admin/repos/...         1.717 MiB
```

## Lessons

1. **Audit-time probes must use the same field names that real consumers use.** The audit invented field names instead of reading what `backup.sh` actually consumes.

2. **Hash-only verification doctrine extends to error-message handling**: when `vault kv get -field=X` fails, the stderr message has non-zero length. Tests that use `[ -n "$VAR" ]` to validate "got the value" treat error messages as success. Use exit-code checks instead.

3. **The probe (e) restic-recency check is value-add for Block 2.** Currently warns "Restic creds Vault-only" — should be enhanced to do exactly what `backup.sh` does (use AppRole + correct field names) and check that latest snapshot < 36h old.

## Action

- No backup repair needed. ✅
- Update regression probe (e) to use correct field names + check snapshot age. (Pre-Block-2 follow-up; bundled with main pre-Block-2 commit.)
- Update audit document with this correction.
