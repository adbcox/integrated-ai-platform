# Runbook: Add New MCP Server

**Last updated:** 2026-04-29 (Phase 14 D-DOC rewrite)
**Supersedes:** pre-Phase-13 version referencing `docker/.env` credentials pattern.

---

## Classify the new server first

| Question | If yes → |
|---|---|
| Does it consume credentials (API keys, tokens)? | Vault Agent sidecar required |
| Does it need the Docker socket? | Remote HTTP (host-side or separate container) |
| Does it need host filesystem access? | Remote HTTP (`mcp-filesystem-remote` pattern) |
| Is it a pure HTTP proxy with no host deps? | Remote HTTP container in `obot-stack.yml` |
| Is it truly stateless with no credentials and no host deps? | Obot-managed (rare) |

**Credential-bearing MCP servers always use the Vault Agent sidecar pattern.**
See `docs/runbooks/add-new-service.md` for the canonical provisioning procedure.

---

## Option A: Credential-bearing remote HTTP server (canonical pattern)

Use this path for any MCP server with secrets (API keys, tokens, passwords).

### Step 1: Provision Vault paths and AppRole

```bash
VAULT_TOKEN=$(cat ~/.vault-token)

# Write credentials (hash-only log)
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault kv put secret/<service>/api key="<api-key>"

# Write policy (create config/vault-policies/<service>-policy.hcl first)
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault policy write <service> config/vault-policies/<service>-policy.hcl

# Create AppRole
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault write auth/approle/role/<service> \
    token_policies="<service>" \
    token_ttl=1h token_max_ttl=4h \
    secret_id_ttl=0

# Save role-id and secret-id
mkdir -p ~/.vault-approle/<service>
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault read -field=role_id auth/approle/role/<service>/role-id \
  > ~/.vault-approle/<service>/role-id
docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server \
  vault write -f -field=secret_id auth/approle/role/<service>/secret-id \
  > ~/.vault-approle/<service>/secret-id
chmod 600 ~/.vault-approle/<service>/role-id ~/.vault-approle/<service>/secret-id
mkdir -p ~/.vault-agent-secrets/<service>
```

### Step 2: Create Vault Agent sidecar template files

```
docker/vault-agent-<service>/
  agent.hcl              — auth config (copy from config/vault-agent-canonical-pattern/agent.hcl, change service name)
  credentials.env.tmpl   — renders env vars from Vault KV paths
```

Example `credentials.env.tmpl`:
```
{{ with secret "secret/data/<service>/api" -}}
<SERVICE>_API_KEY={{ .Data.data.key }}
{{- end }}
```

### Step 3: Add to compose file

```yaml
# Sidecar
vault-agent-<service>:
  <<: *vault-agent-base          # reuse the x-vault-agent-base anchor
  container_name: vault-agent-<service>
  volumes:
    - /Users/admin/.vault-approle/<service>:/vault/approle:ro
    - /Users/admin/.vault-agent-secrets/<service>:/vault/secrets
    - ./vault-agent-<service>/agent.hcl:/vault/config/agent.hcl:ro
    - ./vault-agent-<service>/credentials.env.tmpl:/vault/agent-config/credentials.env.tmpl:ro

# Service
mcp-<service>-remote:
  image: node:22-slim
  container_name: mcp-<service>-remote
  restart: unless-stopped
  depends_on:
    vault-agent-<service>:
      condition: service_completed_successfully
  ports:
    - "80NN:80NN"
  volumes:
    - /Users/admin/.vault-agent-secrets/<service>:/vault/secrets:ro
  networks:
    - obot-net
  entrypoint:
    - sh
    - -c
    - "set -a && . /vault/secrets/credentials.env && set +a && exec npx -y supergateway --stdio 'npx -y <package>' --outputTransport streamableHttp --port 80NN --cors --healthEndpoint /healthz"
  cap_drop:
    - ALL
  security_opt:
    - no-new-privileges:true
  healthcheck:
    test: ["CMD-SHELL", "curl -sf http://localhost:80NN/healthz || exit 1"]
    interval: 15s
    timeout: 10s
    retries: 5
    start_period: 90s
```

### Step 4: Register with Obot (no credentials in registration)

```python
# In bin/register_obot_tools.py — remote runtime only; credentials arrive via env
{
    "id": "<service>",
    "manifest": {
        "name": "<Service Name>",
        "shortDescription": "One-line description",
        "runtime": "remote",
        "remoteConfig": {"url": "http://mcp-<service>-remote:80NN/mcp"},
    },
},
```

### Step 5: Verify IV&V

```bash
# Sidecar rendered credentials
ls ~/.vault-agent-secrets/<service>/
cat ~/.vault-agent-secrets/<service>/credentials.env | sha256sum  # non-empty

# Service healthy
docker inspect mcp-<service>-remote --format '{{.State.Health.Status}}'
curl -sf http://localhost:80NN/healthz && echo "OK"

# Tool count
curl -s http://localhost:8090/api/mcp-servers/<service>/tools | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} tools available')"
```

---

## Option B: Credential-free remote HTTP server

For servers with no secrets (filesystem access, public APIs):

```yaml
mcp-<service>-remote:
  image: node:22-slim
  container_name: mcp-<service>-remote
  restart: unless-stopped
  ports:
    - "80NN:80NN"
  networks:
    - obot-net
  cap_drop:
    - ALL
  security_opt:
    - no-new-privileges:true
  command:
    - sh
    - -c
    - "npx -y supergateway --stdio 'npx -y <package>' --outputTransport streamableHttp --port 80NN --cors --healthEndpoint /healthz"
  healthcheck:
    test: ["CMD-SHELL", "curl -sf http://localhost:80NN/healthz || exit 1"]
    interval: 15s
    timeout: 10s
    retries: 5
    start_period: 90s
```

No Vault provisioning needed. No sidecar. No credentials in env vars.

---

## Port allocation

| Port | Service |
|---|---|
| 8091 | mcp-filesystem-remote |
| 8092 | mcp-docker-remote |
| 8093 | mcp-docs-remote |
| 8094 | plex-mcp |
| 8095+ | next available |

---

## Non-negotiables

- **No credentials in `environment:` blocks.** Use Vault Agent sidecar.
- **No credentials in `.env` files.** Pre-commit hook (`detect-secrets`) enforces this.
- **`cap_drop:[ALL]`** on every new MCP server container.
- **`no-new-privileges:true`** universally.
- **Hash-only verification** at every Vault operation — never display credential values.
