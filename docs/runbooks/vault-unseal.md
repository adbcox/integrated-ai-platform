# Vault Unseal — Runbook

**When to use**: Vault is sealed and the platform is degraded (every service that depends on Vault is failing AppRole logins).

## 1. Check current state (always start here)

```bash
docker exec vault-server vault status -format=json | jq '{type, sealed, initialized}'
```

Expected when healthy: `{"type":"transit","sealed":false,"initialized":true}`.

## 2. If `sealed: true`, try auto-unseal first

Auto-unseal happens automatically via the seal-vault container. If main Vault is sealed but auto-unseal hasn't engaged, restart it:

```bash
docker restart vault-server
sleep 15
docker exec vault-server vault status -format=json | jq '.sealed'
```

Expected: `false` within 15s. If `true`, seal-vault is dead — see Step 3.

## 3. If seal-vault is dead, restart it first

```bash
docker ps -a --filter name=seal-vault --format 'table {{.Names}}\t{{.Status}}'
# If exited or unhealthy:
docker compose -f /Users/admin/control-center-stack/stacks/seal-vault/docker-compose.yml up -d
sleep 10
docker exec seal-vault vault status -format=json | jq '.sealed'
```

If seal-vault itself is sealed, unseal it manually using its Shamir 1-of-1 key:

```bash
# Get key from offline storage (USB / fire safe / password manager)
# DO NOT echo to terminal; pipe directly:
KEY=$(<your offline retrieval method>)
echo "$KEY" | docker exec -i seal-vault vault operator unseal -
unset KEY
```

After seal-vault is healthy, retry Step 2 to auto-unseal main Vault.

## 4. If auto-unseal still fails — manual Shamir unseal of main Vault

See `docs/runbooks/vault-recovery-from-shamir.md` for full Shamir recovery.

## 5. Post-unseal verification

```bash
# Vault accepting requests:
curl -s http://localhost:8200/v1/sys/health | jq

# AppRole login works:
ROLE_ID=$(cat ~/.vault-approle/backup/role-id)
SECRET_ID=$(cat ~/.vault-approle/backup/secret-id)
curl -s -X POST -d "{\"role_id\":\"$ROLE_ID\",\"secret_id\":\"$SECRET_ID\"}" \
  http://localhost:8200/v1/auth/approle/login | jq '.auth.client_token | length'
# Expected: non-zero length
```

## 6. Audit log capture restored

```bash
docker exec vault-server tail -3 /vault/logs/audit.log | jq -r '.time'
```

Expected: timestamps within last few seconds.
