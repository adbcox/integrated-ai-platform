# Vault Token Rotation — Runbook

**When to use**:
- Annual rotation
- Post-incident (token leak suspected)
- When current token's TTL drops below 7 days

## Background — Block 1.7 lesson

The Block 1.7 incident occurred when a non-orphan token was rotated; revoking the parent cascaded to the new child, leaving Vault inaccessible until recovery. Always use `-orphan` for root-replacement tokens.

## Procedure for the master root token (`~/.vault-token`)

### Step 1: Create new orphan token

```bash
docker exec -e VAULT_TOKEN="$(cat ~/.vault-token)" vault-server \
  vault token create -policy=root -orphan -period=720h \
    -display-name="root-rotation-$(date +%Y%m%d)" \
    -format=json | jq -r '.auth.client_token' > ~/.vault-token.new
chmod 600 ~/.vault-token.new
```

`-orphan` means the new token has no parent; revoking the OLD token won't cascade.
`-period=720h` makes it a periodic token (auto-renews to 720h every renewal); never expires under normal operation.

### Step 2: Verify new token works

```bash
docker exec -e VAULT_TOKEN="$(cat ~/.vault-token.new)" vault-server \
  vault token lookup -format=json | jq '{policies, ttl, period, orphan}'
```

Expected: `policies=["root"], orphan=true, period=2592000s, ttl=2592000s`.

### Step 3: Atomic swap

```bash
mv ~/.vault-token ~/.vault-token.old
mv ~/.vault-token.new ~/.vault-token
chmod 600 ~/.vault-token
```

### Step 4: Test ALL operations work with new token

```bash
docker exec -e VAULT_TOKEN="$(cat ~/.vault-token)" vault-server vault status
docker exec -e VAULT_TOKEN="$(cat ~/.vault-token)" vault-server vault list secret/
```

Expected: both succeed.

### Step 5: Revoke the old token

ONLY after Step 4 succeeds:

```bash
docker exec -e VAULT_TOKEN="$(cat ~/.vault-token)" vault-server \
  vault token revoke "$(cat ~/.vault-token.old)"
rm ~/.vault-token.old
```

### Step 6: Verify revocation

```bash
docker exec -e VAULT_TOKEN="$(cat ~/.vault-token.old 2>/dev/null || echo nope)" vault-server \
  vault token lookup 2>&1 | grep -q "permission denied\|invalid token"
# Expected: match (old token rejected)
```

## Per-service AppRole secret-id rotation

For services using Vault Agent sidecars, the AppRole's secret-id should rotate periodically:

```bash
# For each service with AppRole:
SVC=<service>
docker exec -e VAULT_TOKEN="$(cat ~/.vault-token)" vault-server \
  vault write -force -field=secret_id auth/approle/role/$SVC/secret-id > ~/.vault-approle/$SVC/secret-id
chmod 600 ~/.vault-approle/$SVC/secret-id

# Recreate the service so its sidecar picks up new secret-id:
docker compose up -d --force-recreate $SVC
```

## Anti-patterns

- **Never use `-no-default-policy=false` without `-orphan`** — produces a child token that gets revoked when its parent does.
- **Never store the root token unencrypted in scripts** — use AppRole for service auth; root token is for human emergency operations only.
- **Never leak the token to terminal scrollback** — pipe through stdin or files.
