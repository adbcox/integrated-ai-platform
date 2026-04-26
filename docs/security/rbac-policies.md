# RBAC Policies — Control Center Stack

## Role Definitions

| Role | Description | Who Has It |
|------|-------------|------------|
| **platform-admin** | Full access to all services, secrets, and config | Admin (single user) |
| **ai-developer** | Read/write AI services; no secrets access | Local dev sessions |
| **agent-executor** | Execute tasks via MCP/Obot; no admin UI | Obot gateway agents |
| **read-only** | View dashboards and metrics; no write | Monitoring services |

## Service-Level Access Matrix

### LiteLLM Gateway (port 4000)

| Action | platform-admin | ai-developer | agent-executor | read-only |
|--------|---------------|--------------|----------------|-----------|
| Query models (`/v1/chat/completions`) | ✅ | ✅ | ✅ | ❌ |
| List models (`/v1/models`) | ✅ | ✅ | ✅ | ❌ |
| Admin dashboard (`/ui`) | ✅ | ❌ | ❌ | ❌ |
| Add/remove model routes | ✅ | ❌ | ❌ | ❌ |
| View spend/usage | ✅ | ✅ | ❌ | ❌ |

**Auth mechanism**: Bearer token (`LITELLM_MASTER_KEY` for admin, virtual keys for others).

To create a restricted virtual key:
```bash
curl -X POST http://localhost:4000/key/generate \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"key_alias":"agent-key","models":["qwen2.5-coder:14b"],"max_budget":null}'
```

### Vault (port 8200)

| Action | platform-admin | ai-developer | agent-executor | read-only |
|--------|---------------|--------------|----------------|-----------|
| Read secrets (`secret/*`) | ✅ | Scoped | ❌ | ❌ |
| Write secrets | ✅ | ❌ | ❌ | ❌ |
| List secret paths | ✅ | Scoped | ❌ | ❌ |
| Manage policies | ✅ | ❌ | ❌ | ❌ |
| Enable audit logging | ✅ | ❌ | ❌ | ❌ |

**Auth mechanism**: Token (root token for admin, policy-scoped tokens for others).

Developer scoped policy example:
```hcl
# vault-policy-developer.hcl
path "secret/data/plane/*" {
  capabilities = ["read", "list"]
}
path "secret/data/litellm/*" {
  capabilities = ["read"]
}
```

Apply:
```bash
vault policy write developer vault-policy-developer.hcl
vault token create -policy=developer -ttl=8h
```

### Obot Gateway (port 8090)

| Action | platform-admin | ai-developer | agent-executor | read-only |
|--------|---------------|--------------|----------------|-----------|
| Create/run agents | ✅ | ✅ | ✅ | ❌ |
| Configure tools | ✅ | ✅ | ❌ | ❌ |
| View audit logs | ✅ | ❌ | ❌ | ❌ |
| Manage OAuth apps | ✅ | ❌ | ❌ | ❌ |
| Admin bootstrap | ✅ | ❌ | ❌ | ❌ |

**Auth mechanism**: Browser OAuth (GitHub/Google) via Obot admin UI.

### MCPO Proxy (port 8081)

| Action | platform-admin | ai-developer | agent-executor | read-only |
|--------|---------------|--------------|----------------|-----------|
| Call filesystem tools | ✅ | ✅ | ✅ | ❌ |
| View OpenAPI schema | ✅ | ✅ | ✅ | ✅ |

**Auth mechanism**: None (localhost only; rely on network-level controls).

### Open WebUI (port 3002)

| Action | platform-admin | ai-developer | agent-executor | read-only |
|--------|---------------|--------------|----------------|-----------|
| Chat with models | ✅ | ✅ | ❌ | ❌ |
| Upload RAG documents | ✅ | ✅ | ❌ | ❌ |
| Manage model connections | ✅ | ❌ | ❌ | ❌ |
| User management | ✅ | ❌ | ❌ | ❌ |

**Auth mechanism**: Local account (admin created on first launch).

### Plane CE (port 8000 / 3001)

| Action | platform-admin | ai-developer | agent-executor | read-only |
|--------|---------------|--------------|----------------|-----------|
| Create/update issues | ✅ | ✅ | ✅ | ❌ |
| View roadmap | ✅ | ✅ | ✅ | ✅ |
| Manage workspace | ✅ | ❌ | ❌ | ❌ |
| Generate API keys | ✅ | ❌ | ❌ | ❌ |

**Auth mechanism**: Session cookie (UI) or `x-api-key` header (API).

---

## Network Access Control

| Service | Bound To | LAN Accessible | Rationale |
|---------|----------|----------------|-----------|
| LiteLLM :4000 | 0.0.0.0 | ✅ Yes | Cross-machine model routing |
| MCPO :8081 | 0.0.0.0 | ✅ Yes | Open WebUI tool integration |
| Open WebUI :3002 | 0.0.0.0 | ✅ Yes | Browser UI access |
| Homarr :7575 | 0.0.0.0 | ✅ Yes | Dashboard access |
| Vault :8200 | 0.0.0.0 | ✅ Yes | Dev mode only — migrate to localhost for prod |
| Plane DB :5433 | 127.0.0.1 | ❌ No | MCP server only, localhost binding |
| Obot :8090 | 0.0.0.0 | ✅ Yes | Agent gateway |

**OPNsense firewall rules** (recommended): Restrict :4000, :8200 to known device IPs only.

---

## Secret Rotation Schedule

| Secret | Location | Rotation Frequency | Last Rotated |
|--------|----------|--------------------|--------------|
| `PLANE_API_TOKEN` | `docker/.env` → Vault | Quarterly | On initial setup |
| `LITELLM_MASTER_KEY` | `gateways/.env` → Vault | Quarterly | On initial setup |
| `VAULT_ROOT_TOKEN` | `vault/.env` | On compromise only | On initial setup |
| `ANTHROPIC_API_KEY` | `gateways/.env` → Vault | Annually | Per Anthropic console |
| `OPENAI_API_KEY` | `gateways/.env` → Vault | Annually | Per OpenAI console |
| `GITHUB_TOKEN` | `docker/.env` | Annually | Not yet created |
| `BRAVE_API_KEY` | `docker/.env` | Annually | Not yet created |

To rotate a secret:
1. Generate new value in the source system (Anthropic console, Plane admin, etc.)
2. Update in Vault: `vault kv put secret/<path> value="<new>"`
3. Update `docker/.env` / `gateways/.env`
4. Restart affected services (see `docs/runbooks/service-restart-procedures.md`)
