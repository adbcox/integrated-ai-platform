# Vault Rekey — Runbook

**When to use**:
- Annual rotation (calendar)
- Post-incident (key compromise suspected)
- After offline storage location change
- After staff/access changes

## Main Vault Shamir rekey

### Step 1: Initiate rekey

```bash
docker exec -e VAULT_TOKEN="$(cat ~/.vault-token)" vault-server \
  vault operator rekey -init -key-shares=5 -key-threshold=3
# Save the returned nonce.
```

### Step 2: Provide 3 of 5 OLD keys with nonce

Retrieve 3 OLD keys from offline storage:

```bash
# For each key:
echo "<old-key-1>" | docker exec -i -e VAULT_TOKEN="$(cat ~/.vault-token)" vault-server \
  vault operator rekey -nonce=<NONCE> -
# Repeat 3 times with each old key.
```

After 3rd OLD key, Vault returns 5 NEW keys.

### Step 3: Save NEW keys to offline storage

- Encrypt the 5 new keys (PGP, password manager, etc.)
- Write to USB drive in fire safe
- Print backup copy to fire safe
- Update encrypted password manager entry
- DO NOT keep new keys on Mac Mini disk

### Step 4: Securely destroy OLD keys

- Shred USB drive containing old keys (or wipe and reuse)
- Burn or shred printed copies
- Delete password manager entries (history check)

### Step 5: Test new keys

```bash
docker exec vault-server vault status -format=json | jq '.sealed'
# Should still be false (rekey doesn't seal)

# Test by sealing and providing new keys:
docker exec -e VAULT_TOKEN="$(cat ~/.vault-token)" vault-server vault operator seal
sleep 2
docker exec vault-server vault status -format=json | jq '.sealed'   # true
echo "<new-key-1>" | docker exec -i vault-server vault operator unseal -
echo "<new-key-2>" | docker exec -i vault-server vault operator unseal -
echo "<new-key-3>" | docker exec -i vault-server vault operator unseal -
docker exec vault-server vault status -format=json | jq '.sealed'   # false
```

## Seal-Vault rekey

Seal-vault uses Shamir 1-of-1 (single key + threshold). Rekey procedure:

```bash
docker exec -e VAULT_TOKEN="<seal-vault-root-token>" seal-vault \
  vault operator rekey -init -key-shares=1 -key-threshold=1
# Note nonce.

echo "<old-seal-vault-key>" | docker exec -i seal-vault \
  vault operator rekey -nonce=<NONCE> -
# Returns new key.
```

Save new key offline; destroy old.

## Documentation

After every rekey, update:
- Date of rekey
- Where keys are stored (without disclosing values)
- Who performed the rekey

In: `docs/operations/vault-rekey-log.md` (create if needed; one line per event).
