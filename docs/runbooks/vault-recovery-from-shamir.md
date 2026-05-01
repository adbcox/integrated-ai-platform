# Vault Recovery from Shamir Keys — Runbook

**When to use**: Auto-unseal failed, seal-vault is unrecoverable, and main Vault must be unsealed using its Shamir keys directly.

This is the LAST RESORT. Auto-unseal recovery via `docs/runbooks/vault-unseal.md` should be tried first.

## Prerequisites

- Main Vault Shamir keys (5 keys, threshold 3) — offline storage location:
  - Primary: USB drive in fire safe
  - Backup: printed copy in fire safe
  - Tertiary: encrypted password manager (Vaultwarden — bootstrap problem if Vaultwarden is also down; use printed)

- Root token (currently periodic, 30-day TTL) — `~/.vault-token` on Mac Mini

## Procedure

### Step 1: Confirm vault-server is reachable

```bash
docker exec vault-server vault status -format=json
```

Expected: shows `sealed: true`. If container is exited or unreachable, recreate first:

```bash
docker compose -f /Users/admin/control-center-stack/stacks/vault/docker-compose.yml up -d
sleep 10
docker exec vault-server vault status
```

### Step 2: Provide 3 of 5 Shamir keys

Retrieve 3 keys from offline storage. Pipe each through stdin (do NOT echo):

```bash
# Per key:
echo "<key-1>" | docker exec -i vault-server vault operator unseal -
echo "<key-2>" | docker exec -i vault-server vault operator unseal -
echo "<key-3>" | docker exec -i vault-server vault operator unseal -
```

Each command shows current unseal progress. After 3rd key, Vault unseals.

### Step 3: Verify

```bash
docker exec vault-server vault status -format=json | jq '{sealed, initialized}'
# Expected: {"sealed":false, "initialized":true}
```

### Step 4: Restore root token to ~/.vault-token

If `~/.vault-token` was lost or revoked:

```bash
# Bootstrap a new root token using one Shamir key (regenerate-root flow)
# This requires online platform with shell access:
docker exec vault-server vault operator generate-root -init
# Returns OTP and nonce. Save both.

# Provide 3 keys with the nonce:
docker exec vault-server vault operator generate-root -nonce=<NONCE>
# Repeat 3 times with each Shamir key.

# Returns encoded token. Decode:
docker exec vault-server vault operator generate-root -decode=<ENCODED> -otp=<OTP>
# Save decoded token to ~/.vault-token
```

Note: this flow requires Vault 2.0.0+'s `enable_unauthenticated_access` (set during Block 1.7 recovery) for the `/sys/generate-root` endpoint.

### Step 5: Re-engage auto-unseal for future restarts

If seal-vault is healthy, the next `docker restart vault-server` should auto-unseal. Verify:

```bash
docker restart vault-server
sleep 15
docker exec vault-server vault status -format=json | jq '.sealed'
# Expected: false
```

If `true`, seal-vault has a problem — see vault-unseal.md Step 3.

## Post-recovery checklist

- [ ] Vault unsealed and accepting requests
- [ ] AppRole logins working (test with backup AppRole)
- [ ] Audit log capturing
- [ ] All sidecars (vault-agent-*) renewing or completing successfully
- [ ] Move offline keys back to safe location
- [ ] Verify ~/seal-vault-init-keys-MOVE-OFFLINE.txt is NOT on Mac Mini disk

## Verification (D-16-07 — REQUIRED before declaring handoff complete)

Recovery is NOT complete when paths are populated. It is complete when
**values are correct**. The two are not the same — see "Why this section
exists" below.

### Population check (necessary but insufficient)

For each expected vault path, verify `vault kv get <path>` succeeds:

```bash
# Example for the 47 paths from the 2026-04-30 cascade rebuild:
for p in $(cat docs/phase-15/expected-vault-paths.txt); do
  $DOCKER exec vault-server vault kv get "$p" >/dev/null 2>&1 && echo "OK $p" || echo "MISSING $p"
done
```

Count: N of M paths populated. This proves the WRITE worked.

### Value-correctness check (REQUIRED for handoff acceptance)

For at least one secret per CRITICAL service category, perform an
**end-to-end auth attempt against the live target** using the Vault-stored
credentials. Run:

```bash
VAULT_TOKEN=$(cat ~/.vault-token) bash scripts/vault-handoff-verify.sh
```

The helper checks:

1. **minio/backup**: `restic snapshots --no-cache` (or `mc ls` fallback)
   succeeds against MinIO at 192.168.10.201:9000 — proves the access_key
   and secret_key in `secret/minio/backup` are the actual MinIO user
   credentials, not stale or bogus values.
2. **AppRole surface alive**: root token can `vault list auth/approle/role`
   — proves the auth mount is present and the token is valid.
3. **Audit device writing**: `vault audit list` returns `file/` —
   proves the audit-log write path is intact.

A failed value-correctness check = handoff **REJECTED** until remediated,
even if all paths are populated. The helper exits 1 on any failure with
detail per failed check.

### Why this section exists

The 2026-04-30 Vault cascade post-recovery verification only counted
leaf-path population (47/47 paths populated). The bogus 11-character
MinIO access key in `secret/minio/backup` survived rebuild and only
surfaced when Restic auth retried with exponential backoff during
D-15-03 testing **five days later**. Recovery doctrine now requires
value-correctness verification.

## When this fails

If 3 keys don't unseal: keys are wrong/corrupt. Try other 2. If none work, Vault data is recoverable from Restic backup (see vault-restore-from-backup.md, scheduled for Phase 14).
