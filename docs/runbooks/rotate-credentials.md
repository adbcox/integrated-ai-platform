# Runbook: Rotate Credentials

**Last updated:** 2026-04-29 (Phase 14 D-DOC rewrite)
**Supersedes:** pre-Phase-13 version that referenced `docker/.env` pattern.

All credentials live in Vault (`http://vault-server:8200`). They reach
containers via Vault Agent sidecars that render `/vault/secrets/credentials.env`
at startup. Rotating a credential means updating the Vault KV path and
triggering a sidecar re-auth cycle.

---

## General rotation procedure

```bash
# 1. Write new credential to Vault (hash-only verification — never echo the value)
VAULT_TOKEN=$(cat ~/.vault-token)
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault kv put secret/<service>/<type> <field>=<new-value>

# 2. Verify the write (hash only — never display the value)
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault kv get -field=<field> secret/<service>/<type> | sha256sum | cut -c1-12
# Compare against expected hash

# 3. Restart the service (sidecar re-renders credentials.env on startup)
cd ~/repos/integrated-ai-platform/docker
docker compose -f <stack>.yml up -d <service-name>

# 4. Verify service healthy with new credential
docker inspect <service-name> --format '{{.State.Health.Status}}'
```

---

## Vault root token rotation

The root token has a 30-day TTL. Rotate before expiry:

```bash
VAULT_TOKEN=$(cat ~/.vault-token)
# Generate new orphan token (orphan flag per Block 1.7 lesson)
NEW_TOKEN=$(docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault token create -orphan -ttl=720h -format=json | python3 -c "import json,sys; print(json.load(sys.stdin)['auth']['client_token'])")
echo "$NEW_TOKEN" > ~/.vault-token
chmod 600 ~/.vault-token

# Verify
docker exec -e VAULT_TOKEN="$NEW_TOKEN" vault-server vault token lookup -format=json | python3 -c "
import json,sys; d=json.load(sys.stdin)['data']
print('ttl:', d['ttl'], '| orphan:', d['orphan'])
"
```

See also: `docs/runbooks/vault-token-rotation.md` for the full orphan-token procedure.

---

## AppRole secret-id rotation (per-service)

Each service has an AppRole at `auth/approle/role/<service>`. Rotate secret-ids periodically:

```bash
VAULT_TOKEN=$(cat ~/.vault-token)
SERVICE=<service>  # e.g. netbox, inventree, plane-api

# Generate new secret-id
NEW_SECRET=$(docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault write -f auth/approle/role/$SERVICE/secret-id -format=json | \
  python3 -c "import json,sys; print(json.load(sys.stdin)['data']['secret_id'])")

# Write to approle directory
echo "$NEW_SECRET" > ~/.vault-approle/$SERVICE/secret-id
chmod 600 ~/.vault-approle/$SERVICE/secret-id

# Restart service to pick up new secret-id (sidecar re-auths)
cd ~/repos/integrated-ai-platform/docker
docker compose -f <stack>.yml up -d vault-agent-$SERVICE <service-name>
```

---

## Service-specific examples

### Grafana admin password

```bash
VAULT_TOKEN=$(cat ~/.vault-token)
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault kv put secret/grafana/admin password="<new-password>"

# Hash verify
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault kv get -field=password secret/grafana/admin | sha256sum | cut -c1-12

# Restart Grafana (sidecar re-renders GF_SECURITY_ADMIN_PASSWORD)
cd ~/repos/integrated-ai-platform/docker
docker compose -f observability-stack.yml up -d grafana
```

### NetBox API token

```bash
# 1. In NetBox UI: Admin → API Tokens → revoke old, create new
# 2. Write new token to Vault
VAULT_TOKEN=$(cat ~/.vault-token)
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault kv put secret/netbox/api token="<new-token>"

# 3. Restart NetBox services
cd ~/repos/integrated-ai-platform/docker
docker compose -f docker-compose-netbox.yml up -d netbox netbox-worker
```

### Nextcloud DB password

```bash
# NOTE: DB password rotation requires coordinated update of Postgres + Nextcloud.
# 1. Generate new password (use openssl or similar, avoid URL-unsafe chars — use hex)
NEW_PASS=$(openssl rand -hex 32)

# 2. Write to Vault
VAULT_TOKEN=$(cat ~/.vault-token)
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault kv put secret/nextcloud/postgres password="$NEW_PASS"

# 3. Update Postgres (ALTER USER)
docker exec nextcloud-db psql -U nextcloud -c "ALTER USER nextcloud PASSWORD '$NEW_PASS';"

# 4. Restart sidecars + services (they re-render credentials.env)
cd ~/repos/integrated-ai-platform/docker
docker compose -f docker/nextcloud/docker-compose.yml up -d
```

---

## Strava token (expires every ~6h)

Strava tokens are short-lived and not managed by Vault Agent at runtime
(they require OAuth redirect). Manual refresh:

```bash
# Get new token via refresh
VAULT_TOKEN=$(cat ~/.vault-token)
REFRESH=$(docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault kv get -field=refresh_token secret/strava/oauth)
NEW=$(curl -s -X POST https://www.strava.com/oauth/token \
  -d "client_id=$(docker exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server vault kv get -field=client_id secret/strava/oauth)" \
  -d "client_secret=$(docker exec -e VAULT_TOKEN=$VAULT_TOKEN vault-server vault kv get -field=client_secret secret/strava/oauth)" \
  -d "grant_type=refresh_token" \
  -d "refresh_token=$REFRESH" | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault kv put secret/strava/oauth access_token="$NEW"
```

---

## Best practices

- Rotate quarterly (database passwords) or on personnel change.
- Always hash-verify after write — never display credential values.
- Keep the rotation atomic: write to Vault first, verify hash, then restart service.
- If a service is customer-facing, prefer blue/green (restart the standby first).
- Log the rotation event: `# rotated $(date -u +%Y-%m-%dT%H:%M:%SZ)` in the Vault KV metadata or Plane issue.
- Credentials in Vault audit log are hashed automatically by Vault — no manual scrubbing needed.
