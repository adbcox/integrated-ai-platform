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

## When this fails

If 3 keys don't unseal: keys are wrong/corrupt. Try other 2. If none work, Vault data is recoverable from Restic backup (see vault-restore-from-backup.md, scheduled for Phase 14).
