# Add New Service — Runbook

Canonical procedure for onboarding a new service to the platform with Vault Agent sidecar credential delivery and §7 hardening.

## Prerequisites

- Vault is unsealed and accepting AppRole logins
- Service has been chosen and its compose definition drafted
- You know what credentials the service needs (database password, API key, etc.)

## Step 1 — Create policy file

Path: `config/vault-policies/<service>-policy.hcl`

```hcl
# <service> — read-only access to its own secrets
# Generated <date>

path "secret/data/<service>/<purpose>" {
  capabilities = ["read"]
}
```

Add one `path` block per Vault path the service legitimately needs.

## Step 2 — Add to service-registry.yaml

Edit `config/service-registry.yaml`:

```yaml
- id: <service>
  name: <Service Display Name>
  category: <ai|platform|infrastructure|observability|misc>
  host: mac-mini
  container: <service-container-name>
  image: <upstream-image:tag>
  port: <host-port>
  internal_port: <container-port>
  health_url: "http://localhost:<port>/<healthcheck-endpoint>"
  health_method: GET
  health_expect: 200
  purpose: <one-sentence description>
  depends_on: [vault-server, caddy, ...]
  security:
    no_new_privileges: true
    cap_drop: [ALL]
  compose_file: <path/to/compose.yml>
  credentials_env: [<list of env var names>]
```

## Step 3 — Create Vault AppRole

```bash
VAULT_TOKEN=$(cat ~/.vault-token)

# Write policy
docker cp config/vault-policies/<service>-policy.hcl \
  vault-server:/tmp/<service>-policy.hcl
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault policy write <service> /tmp/<service>-policy.hcl

# Create AppRole
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault write auth/approle/role/<service> \
    token_policies=<service> \
    token_ttl=1h \
    token_max_ttl=4h \
    secret_id_ttl=0
```

## Step 4 — Capture role-id and secret-id

```bash
mkdir -p ~/.vault-approle/<service>
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault read -field=role_id auth/approle/role/<service>/role-id > ~/.vault-approle/<service>/role-id
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault write -force -field=secret_id auth/approle/role/<service>/secret-id > ~/.vault-approle/<service>/secret-id
chmod 600 ~/.vault-approle/<service>/{role-id,secret-id}
```

## Step 5 — Verify isolation

```bash
ROLE_ID=$(cat ~/.vault-approle/<service>/role-id)
SECRET_ID=$(cat ~/.vault-approle/<service>/secret-id)
TOKEN=$(docker exec vault-server vault write -field=token auth/approle/login \
  role_id="$ROLE_ID" secret_id="$SECRET_ID")

# In-policy read works:
docker exec -e VAULT_TOKEN="$TOKEN" vault-server vault kv get -format=json secret/<service>/<purpose>
# Expected: success

# Out-of-policy read denied:
docker exec -e VAULT_TOKEN="$TOKEN" vault-server vault kv get secret/some/unrelated/path
# Expected: 403 permission denied

docker exec -e VAULT_TOKEN="$TOKEN" vault-server vault token revoke -self
```

## Step 6 — Create vault-agent config

Path: `<service-stack-dir>/vault-agent-<service>/`

Copy `config/vault-agent-canonical-pattern/agent.hcl` and adapt the `credentials.env.tmpl` to render the fields the service needs.

## Step 7 — Create host secrets dir

```bash
mkdir -p /Users/admin/.vault-agent-secrets/<service>
chmod 0700 /Users/admin/.vault-agent-secrets/<service>
```

## Step 8 — Add Caddy route + DNS

In `config/caddy/Caddyfile`:

```
<service>.internal {
    reverse_proxy <service>:<port>
}
```

In OPNsense / DNS resolver: add `<service>.internal → 192.168.10.145`.

## Step 9 — Edit compose to apply canonical pattern

Add the sidecar service block + the entrypoint wrapper + §7 hardening to the main service block. See `config/vault-agent-canonical-pattern/README.md` for the full pattern.

## Step 10 — Commit

```bash
git add config/vault-policies/<service>-policy.hcl
git add config/service-registry.yaml
git add <service-stack-dir>/vault-agent-<service>/
git add <compose-file>
git commit -m "Add <service> with Vault Agent sidecar + §7 hardening"
```

## Step 11 — Deploy + verify

```bash
docker compose -f <compose-file> up -d <service>
sleep 30

# Sidecar exited cleanly:
docker inspect vault-agent-<service> --format '{{.State.ExitCode}}'   # 0

# Render hash matches Vault:
RENDERED=$(grep '^<FIELD>=' /Users/admin/.vault-agent-secrets/<service>/credentials.env | cut -d= -f2- | tr -d '\n' | shasum -a 256 | awk '{print substr($1,1,12)}')
VAULT=$(docker exec -e VAULT_TOKEN="$(cat ~/.vault-token)" vault-server vault kv get -field=<field> secret/<service>/<purpose> | tr -d '\n' | shasum -a 256 | awk '{print substr($1,1,12)}')
echo "rendered=$RENDERED vault=$VAULT"
test "$RENDERED" = "$VAULT" && echo "MATCH" || echo "MISMATCH"

# Health endpoint passes:
curl -s -o /dev/null -w '%{http_code}' http://localhost:<port>/<healthcheck>
# Expected: 200

# Audit log captured the AppRole login:
docker exec vault-server tail -50 /vault/logs/audit.log | jq -c "select(.auth.metadata.role_name == \"<service>\")" | head -3
```

## Step 12 — Update runbook list

If the service introduces new operational concerns (special restart procedure, dependency on a unique component), add a section to the appropriate runbook or create a new one in `docs/runbooks/`.
