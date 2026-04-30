# Runbook: Vault Restore from Backup

**When to use:** Vault data is corrupted or lost; Restic backup restore is required.
**Prerequisites:** This runbook requires `vault-recovery-from-shamir.md` for the
unseal step after restore. Always attempt `vault-unseal.md` first.

---

## Overview

Vault data lives at `/vault/data` inside the `vault-server` container, backed by
a named Docker volume (`vault-data` or `vault-server-data`). Restic backs this up
nightly via `scripts/backup.sh` using the `backup` AppRole.

Restore steps:
1. Stop vault-server (data must not be written during restore)
2. Identify the target Restic snapshot
3. Restore the Vault data directory
4. Start vault-server
5. Unseal (auto-unseal via seal-vault, or Shamir if seal-vault is also unrecoverable)
6. Verify

---

## Step 1: Stop vault-server

```bash
docker stop vault-server
# Do NOT remove the container — just stop it to release file locks.
```

Confirm stopped:
```bash
docker inspect vault-server --format '{{.State.Status}}'
# Expected: exited
```

---

## Step 2: Get Restic credentials from Vault Agent secrets

The `backup` AppRole credentials are at `~/.vault-approle/backup/`.
If Vault is completely unrecoverable, the Restic repo password is stored
offline (USB drive, fire safe) alongside the Shamir keys.

```bash
# If Vault is partially accessible (can unseal and auth):
VAULT_TOKEN=$(cat ~/.vault-token)
RESTIC_PASSWORD=$(docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault kv get -field=repo_password secret/backup/restic)
RESTIC_REPOSITORY=$(docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault kv get -field=repository secret/backup/restic)

# If Vault is completely down: retrieve from offline storage
# RESTIC_PASSWORD=<from USB/fire safe>
# RESTIC_REPOSITORY=<QNAP path, e.g. sftp:backup@qnap.internal:/backup/iap>
```

---

## Step 3: List available snapshots

```bash
export RESTIC_PASSWORD RESTIC_REPOSITORY
restic snapshots --tag vault | head -20
```

Identify the target snapshot ID (latest clean backup before the incident).

---

## Step 4: Find the Vault data volume mount point

```bash
docker inspect vault-server --format '{{range .Mounts}}{{.Source}} {{.Destination}}{{println}}{{end}}' | grep vault/data
# Example output: /var/lib/docker/volumes/vault-server-data/_data  /vault/data
```

On macOS/Colima, volumes live inside the Colima VM:
```bash
# Get the volume path inside Colima
VOLUME_PATH=$(docker volume inspect vault-server-data --format '{{.Mountpoint}}')
```

---

## Step 5: Restore Vault data

```bash
# Restore to a temp directory first (verify before overwriting)
RESTORE_TMP=$(mktemp -d)
restic restore <snapshot-id> --include /vault/data --target "$RESTORE_TMP"
ls "$RESTORE_TMP/vault/data/"  # verify contents present

# Copy restored data into the volume
# On macOS/Colima: copy via docker cp into a temporary container
docker run --rm \
  -v vault-server-data:/vault/data \
  -v "$RESTORE_TMP/vault/data":/restore-src \
  alpine sh -c "rm -rf /vault/data/* && cp -a /restore-src/. /vault/data/"

rm -rf "$RESTORE_TMP"
```

---

## Step 6: Start vault-server

```bash
docker start vault-server
sleep 15
docker exec vault-server vault status -format=json | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print('sealed:', d['sealed'], '| initialized:', d['initialized'])"
```

---

## Step 7: Unseal

**If seal-vault is healthy** (auto-unseal):
```bash
# seal-vault should automatically unseal vault-server on startup
docker exec vault-server vault status | grep Sealed
# Expected: Sealed    false
```

**If seal-vault is also unrecoverable** (manual Shamir unseal):
See `docs/runbooks/vault-recovery-from-shamir.md`.

---

## Step 8: Verify post-restore

```bash
VAULT_TOKEN=$(cat ~/.vault-token)

# Confirm audit log alive
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server vault audit list

# Spot-check a known KV path (hash-only)
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault kv get -field=password secret/netbox/postgres | sha256sum | cut -c1-12

# Confirm AppRole list intact
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault list auth/approle/role | head -10

# Run regression probe
bash ~/repos/integrated-ai-platform/docs/phase-13/h1-regression-probe.sh
```

---

## Post-restore checklist

- [ ] vault-server unsealed and accepting requests
- [ ] All KV paths spot-checked (hash-only)
- [ ] All AppRoles present in `vault list auth/approle/role`
- [ ] Audit log capturing (new entries after restore timestamp)
- [ ] All Vault Agent sidecars re-authenticated (restart services if needed)
- [ ] Regression probe: FAIL=0
- [ ] Incident documented in `docs/runbooks/rewire-log/`
- [ ] Restic snapshot post-restore taken (`restic backup /vault/data --tag vault-post-restore`)

---

## If restore fails

If the Restic repo is inaccessible or the snapshot is corrupted:
1. Try the previous snapshot (`restic snapshots --tag vault --last 5`)
2. Try the QNAP secondary backup if primary repo is local
3. Escalate: Vault must be re-initialized from scratch, and all AppRole secrets
   re-provisioned via the individual service provisioning scripts
   (e.g., `scripts/provision-netbox.sh`, `scripts/provision-inventree.sh`).
   This is a multi-hour recovery; treat as R-CRITICAL.
