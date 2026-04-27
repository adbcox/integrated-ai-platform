# Runbook: Rotate Credentials

All credentials live in `~/repos/integrated-ai-platform/docker/.env`. After updating any credential, restart Obot so the new value is injected into the registered server's phat container environment.

## GitHub Token

1. **Generate:** https://github.com/settings/tokens — scopes: `repo`, `read:org`

2. **Update:**
```bash
cd ~/repos/integrated-ai-platform/docker
sed -i '' 's/^GITHUB_TOKEN=.*/GITHUB_TOKEN=ghp_NEW_TOKEN/' .env
```

3. **Re-register** (token is passed at registration time, not runtime):
```bash
cd ~/repos/integrated-ai-platform
# Delete old registration in Obot UI, then:
python3 bin/register_obot_tools.py
```

## Strava Access Token

**Note:** Access tokens expire every ~6 hours. This is a manual process until refresh token automation is implemented.

1. **Get new token:** Complete OAuth flow at https://www.strava.com/settings/api or use:
```bash
curl -X POST https://www.strava.com/oauth/token \
  -d client_id=$STRAVA_CLIENT_ID \
  -d client_secret=$STRAVA_CLIENT_SECRET \
  -d grant_type=refresh_token \
  -d refresh_token=$STRAVA_REFRESH_TOKEN \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['access_token'])"
```

2. **Update:**
```bash
cd ~/repos/integrated-ai-platform/docker
NEW_TOKEN="<token from above>"
sed -i '' "s/^STRAVA_ACCESS_TOKEN=.*/STRAVA_ACCESS_TOKEN=$NEW_TOKEN/" .env
```

3. **Re-register:**
```bash
cd ~/repos/integrated-ai-platform
python3 bin/register_obot_tools.py
```

## Home Assistant Token

1. **Generate:** http://192.168.10.141:8123 → Profile → Security → Long-Lived Access Tokens

2. **Update:**
```bash
cd ~/repos/integrated-ai-platform/docker
sed -i '' 's/^HA_TOKEN=.*/HA_TOKEN=NEW_TOKEN/' .env
```

3. **Re-register:**
```bash
cd ~/repos/integrated-ai-platform
python3 bin/register_obot_tools.py
```

## PostgreSQL DSN

If Plane's database credentials change:

1. **Update:**
```bash
cd ~/repos/integrated-ai-platform/docker
sed -i '' 's|^POSTGRES_DSN=.*|POSTGRES_DSN=postgresql://newuser:newpass@host:5432/db|' .env
```

2. **Re-register:**
```bash
cd ~/repos/integrated-ai-platform
python3 bin/register_obot_tools.py
```

## Best Practices

- Rotate credentials quarterly (GitHub, HA) or as required (Strava: every 6h)
- Verify the server works after rotation before revoking old token
- Add a comment with rotation date: `GITHUB_TOKEN=ghp_... # rotated 2026-04-27`
- Never commit `.env` to git (it's in `.gitignore`)
