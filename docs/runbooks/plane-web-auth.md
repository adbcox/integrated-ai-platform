# Plane CE Web Authentication

## Overview

Plane CE web UI authentication uses local email+password. No OIDC issuer required.

**Admin account:** `admin@local.dev`
**Password:** stored at `secret/plane/admin` in Vault (key: `password`)
**Last rotated:** 2026-04-28 (Block 2 P2.1)

## Root Cause of "No authentication methods available" (NF-14-2)

The Plane frontend (`makeplane/plane-frontend:stable`) is a Next.js SPA served
by nginx on port 3000. The stock nginx config (`/etc/nginx/nginx.conf`) only
serves static files with no proxy_pass rules. The SPA fetches
`/api/instances/` (relative URL, resolves to its own origin) to determine
which auth methods to display. Without proxy rules, nginx serves `index.html`
for that request, the SPA parses HTML as JSON, fails, and shows:

> "No authentication methods available. Please contact your administrator."

**Fix:** Override nginx.conf via bind mount to add `/api/` and `/auth/`
proxy rules pointing to `http://plane-api:8000`.

The fix is in `docker/docker-compose-plane.yml`:
```yaml
plane-web:
  volumes:
    - ./plane-nginx/nginx.conf:/etc/nginx/nginx.conf:ro
```

The nginx config is at `docker/plane-nginx/nginx.conf`.

## Verifying Auth Is Working

```bash
# Instance config should show is_email_password_enabled: true
curl -s http://localhost:3001/api/instances/ | python3 -m json.tool | grep email_password

# API login (form-encoded, not JSON)
CSRF=$(curl -sc /tmp/c.txt http://localhost:3001/auth/get-csrf-token/ | python3 -c "import sys,json; print(json.load(sys.stdin)['csrf_token'])")
curl -sv -X POST http://localhost:3001/auth/sign-in/ \
  -b /tmp/c.txt -c /tmp/c.txt \
  -H "X-CSRFToken: $CSRF" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "email=admin@local.dev" \
  --data-urlencode "password=$(vault kv get -field=password secret/plane/admin)"
# Should return: HTTP 302 Location: http://localhost:3001 (no error_code)
```

## DB Configuration State

`instance_configurations` table key/values for auth:

| Key | Expected Value |
|-----|---------------|
| `ENABLE_EMAIL_PASSWORD` | `1` |
| `ENABLE_MAGIC_LINK_LOGIN` | `0` |
| `ENABLE_GOOGLE_SYNC` | `0` |
| `ENABLE_GITHUB_SYNC` | `0` |
| `ENABLE_SIGNUP` | `0` (signup disabled; admin-managed users only) |

Verify:
```bash
docker exec docker-plane-db-1 psql -U plane -d plane \
  -c "SELECT key, value FROM instance_configurations WHERE key LIKE 'ENABLE%' ORDER BY key;"
```

## Password Rotation Procedure (NF-14-1)

1. Generate a new password:
   ```bash
   NEW_PASS=$(openssl rand -hex 16)  # 32-char hex; URL-safe
   ```

2. Set via Django shell:
   ```bash
   docker exec docker-plane-api-1 python3 -c "
   import os; os.environ['DJANGO_SETTINGS_MODULE']='plane.settings.production'
   import django; django.setup()
   from plane.db.models import User
   u = User.objects.get(email='admin@local.dev')
   u.set_password('$NEW_PASS')
   u.save()
   print('done')
   "
   ```

3. Write to Vault (hash-only verification):
   ```bash
   VAULT_TOKEN=$(cat ~/.vault-token)
   docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server vault kv put \
     secret/plane/admin \
     email=admin@local.dev \
     password="$NEW_PASS" \
     rotated=$(date +%Y-%m-%d) \
     reason="<reason>"
   # Immediately unset from shell
   unset NEW_PASS
   ```

4. Verify login works (see above).

5. Hash-verify Vault write:
   ```bash
   docker exec -e VAULT_TOKEN=$(cat ~/.vault-token) vault-server \
     vault kv get -field=password secret/plane/admin | sha256sum | cut -c1-12
   ```

## Troubleshooting

**"No authentication methods available":** Check that `docker/plane-nginx/nginx.conf`
is bind-mounted. If the container restarted without the volume, the baked-in
config replaces it. Verify with:
```bash
docker exec docker-plane-web-1 grep proxy_pass /etc/nginx/nginx.conf
```
If missing, run: `docker compose -f docker/docker-compose-plane.yml up -d --force-recreate plane-web`

**`AUTHENTICATION_FAILED_SIGN_IN`:** Wrong password. Retrieve from
`secret/plane/admin` in Vault and retry.

**`REQUIRED_EMAIL_PASSWORD_SIGN_IN`:** The sign-in endpoint expects
`application/x-www-form-urlencoded` (form POST), not JSON.
