# Obot Gateway — Setup Guide

## Status: Running, needs browser-based admin configuration

Obot is deployed and healthy at `http://192.168.10.145:8090`. The initial admin
setup requires browser access — the API requires OAuth/bootstrap authentication
that cannot be configured programmatically.

## Why Obot?

Obot acts as a central MCP hub:
- **RBAC**: Per-tool permissions (Admin/Dev/Agent roles)
- **Audit logging**: All tool calls logged to `/data/audit.log` (90-day retention)
- **Single endpoint**: Claude Code connects once; Obot routes to all backend MCPs
- **GitHub MCP**: Required to expose GitHub tools through the gateway

## Initial Admin Setup (Do This Once)

### Step 1 — Open browser
Navigate to: http://192.168.10.145:8090

### Step 2 — Bootstrap setup
Obot will present a setup wizard. Use:
- Email: your preferred admin email
- Follow the bootstrap flow shown

### Step 3 — Configure authentication (optional for LAN-only)
For local homelab use, authentication is currently disabled
(`OBOT_SERVER_ENABLE_AUTHENTICATION=false`). To enable GitHub OAuth:
1. Create GitHub OAuth App at github.com/settings/developers
2. Callback URL: `http://192.168.10.145:8090/oauth2/callback`
3. Add to `docker/.env`:
   ```
   OBOT_GITHUB_CLIENT_ID=your_client_id
   OBOT_GITHUB_CLIENT_SECRET=your_secret
   ```
4. Add admin email: `OBOT_SERVER_AUTH_ADMIN_EMAILS=adbcox@gmail.com`
5. Recreate: `docker compose -f docker/obot-stack.yml up -d --force-recreate`

### Step 4 — Generate API key
In Obot admin UI: Profile → API Keys → Create key → Copy value

### Step 5 — Register Obot in Claude Code
```bash
# Add OBOT_API_KEY to docker/.env first:
echo "OBOT_API_KEY=your_key_here" >> docker/.env

# Then run the registration script:
python3 bin/register_obot_tools.py --register-claude
```

This adds `obot-gateway` to `~/.claude.json`:
```json
{
  "obot-gateway": {
    "type": "http",
    "url": "http://localhost:8090/api/mcp",
    "headers": {"Authorization": "Bearer your_key_here"}
  }
}
```

## GitHub MCP (P0-1, blocked on token)

Once Obot admin is set up:
1. Add your GitHub PAT to `docker/.env`:
   ```
   GITHUB_TOKEN=ghp_your_personal_access_token
   ```
   Required scopes: `repo`, `read:org`, `workflow`

2. Recreate Obot: `docker compose -f docker/obot-stack.yml up -d --force-recreate`

3. In Obot UI → Tools → Add GitHub MCP server with the token

## Verifying Obot Health

```bash
# Health check
curl http://localhost:8090/api/healthz   # → "ok"

# Container status
docker ps --filter name=obot --format "{{.Names}}: {{.Status}}"

# Audit log (once tools are active)
docker exec obot tail -f /data/audit.log
```

## Container Configuration

| Variable | Value | Notes |
|----------|-------|-------|
| `OBOT_SERVER_ENABLE_AUTHENTICATION` | false | LAN-only; enable for internet exposure |
| `OBOT_DEV_MODE` | true | Relaxes some restrictions |
| `OBOT_SERVER_FORCE_ENABLE_BOOTSTRAP` | true | Keeps bootstrap user active |
| `OBOT_AUDIT_LOG` | true | Logs all tool calls |
| `OBOT_AUDIT_LOG_PATH` | /data/audit.log | Inside container |
| Port | 8090:8080 | Host:Container |
| Volume | obot-data:/data | Persists config + audit log |
