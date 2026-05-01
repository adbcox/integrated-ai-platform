# Runbook: Vault Restore from Backup

**When to use:** Vault data is corrupted or lost; Restic backup restore is required.
**Prerequisites:** This runbook requires `vault-recovery-from-shamir.md` for the
unseal step after restore. Always attempt `vault-unseal.md` first.

---

## Overview

Vault data lives at `/vault/data` inside the `vault-server` container, backed by
a named Docker volume (`vault-data` or `vault-server-data`). Restic backs this up
nightly via `scripts/backup.sh` using the `backup` AppRole.

**Backup source (D-16-04, ADR-A-017):** Restic snapshots contain a
warm-copy of `/vault/data` at the path
`/Users/admin/.vault-snapshot/current/`, **not** the raw volume.
`scripts/vault-snapshot-warm.sh` produces this copy as the first step
of every backup run via an atomic stage→rename. A restore reads the
tree from that path inside Restic and writes it into the live volume.

The warm copy is **crash-consistent**, not transaction-consistent —
on first start after restore Vault's BoltDB recovery semantics roll
forward/back any partial writes (same recovery path as a power loss).
No operator action is needed for that recovery; it happens
transparently.

Restore steps:
1. Stop vault-server (data must not be written during restore)
2. Identify the target Restic snapshot
3. Restore the Vault data directory **from `/Users/admin/.vault-snapshot/current/`** inside the snapshot
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

## Step 2: Get Restic credentials via backup AppRole (non-interactive)

The `backup` AppRole credentials are at `~/.vault-approle/backup/`.
Vault paths: `secret/restic/backup` (password, repository) and `secret/minio/backup` (access_key, secret_key).

```bash
# Non-interactive AppRole login (same pattern as scripts/backup.sh):
VAULT_ADDR="http://127.0.0.1:8200"
APPROLE_DIR="$HOME/.vault-approle/backup"
ROLE_ID=$(cat "$APPROLE_DIR/role-id")
SECRET_ID=$(cat "$APPROLE_DIR/secret-id")

LOGIN_RESP=$(curl -s -X POST \
  -d "{\"role_id\":\"$ROLE_ID\",\"secret_id\":\"$SECRET_ID\"}" \
  "$VAULT_ADDR/v1/auth/approle/login")
VAULT_TOKEN=$(echo "$LOGIN_RESP" | jq -r '.auth.client_token // empty')
[ -z "$VAULT_TOKEN" ] && echo "ERROR: Vault auth failed" && exit 1

vault_get() { curl -s -H "X-Vault-Token: $VAULT_TOKEN" "$VAULT_ADDR/v1/secret/data/$1" | jq -r ".data.data.$2 // empty"; }

export AWS_ACCESS_KEY_ID=$(vault_get minio/backup access_key)
export AWS_SECRET_ACCESS_KEY=$(vault_get minio/backup secret_key)
export RESTIC_PASSWORD=$(vault_get restic/backup password)
export RESTIC_REPOSITORY=$(vault_get restic/backup repository)
# Revoke token when done
curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" "$VAULT_ADDR/v1/auth/token/revoke-self" >/dev/null

# If Vault is completely down: retrieve from offline storage
# RESTIC_PASSWORD=<from USB/fire safe>
# RESTIC_REPOSITORY=s3:http://192.168.10.201:9000/backups
# AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY=<MinIO credentials from offline storage>
```

---

## Step 3: List available snapshots

```bash
export RESTIC_PASSWORD RESTIC_REPOSITORY
restic snapshots | head -20
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
# Restore to a temp directory first (verify before overwriting).
# Source path inside the snapshot is the warm-copy landing zone
# (D-16-04, ADR-A-017) — NOT the raw /vault/data tree, which Restic
# never sees from the host.
RESTORE_TMP=$(mktemp -d)
restic restore <snapshot-id> \
  --include /Users/admin/.vault-snapshot/current \
  --target "$RESTORE_TMP"
ls "$RESTORE_TMP/Users/admin/.vault-snapshot/current/"
# Expected: audit/ auth/ core/ logical/ sys/

# Copy restored data into the live Vault volume.
# On macOS/Colima: write via a temporary alpine container (admin can't
# touch /var/lib/docker/volumes/... directly — root-owned in Colima).
docker run --rm \
  -v vault_vault-data:/vault/data \
  -v "$RESTORE_TMP/Users/admin/.vault-snapshot/current":/restore-src \
  alpine sh -c "rm -rf /vault/data/* && cp -a /restore-src/. /vault/data/"

rm -rf "$RESTORE_TMP"
```

The restored tree is **crash-consistent**. When vault-server starts
in Step 6, BoltDB's recovery handles any partial writes from the
warm-copy moment. No operator action required.

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
1. Try the previous snapshot (`restic snapshots --latest 5`)
2. Try the QNAP secondary backup if primary repo is local
3. Escalate: Vault must be re-initialized from scratch, and all AppRole secrets
   re-provisioned via the individual service provisioning scripts
   (e.g., `scripts/provision-netbox.sh`, `scripts/provision-inventree.sh`).
   This is a multi-hour recovery; treat as R-CRITICAL.
