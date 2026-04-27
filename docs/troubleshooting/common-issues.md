# Troubleshooting Guide

## Issue: Phat Container Returns 503

**Symptoms:** Server returns HTTP 503, tools list empty, "service unavailable"

**Causes:**
1. Cold start — phat containers need 20-30s on first call after Obot restart
2. Missing or wrong credentials
3. Package not found / install failure

**Diagnosis:**
```bash
docker logs obot --tail 100 | grep -i "error\|warn\|fail"
```

**Solutions:**
```bash
# Wait and retry (cold start)
sleep 30 && curl -s http://localhost:8090/api/mcp-servers/<id>/tools | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(len(d),'tools')"

# Restart Obot to clear stale phat containers
cd ~/repos/integrated-ai-platform/docker
docker compose -f obot-stack.yml restart obot
```

## Issue: Strava Token Expired

**Symptoms:** "Unauthorized" or 401 errors from Strava tools

**Solution:**
```bash
# Use refresh token to get new access token
source ~/repos/integrated-ai-platform/docker/.env
curl -s -X POST https://www.strava.com/oauth/token \
  -d "client_id=$STRAVA_CLIENT_ID&client_secret=$STRAVA_CLIENT_SECRET&grant_type=refresh_token&refresh_token=$STRAVA_REFRESH_TOKEN" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('access_token','ERROR:',d))"

# Update .env with new token, then re-register:
cd ~/repos/integrated-ai-platform
python3 bin/register_obot_tools.py
```

## Issue: Remote HTTP Service Not Responding

**Symptoms:** Filesystem, Docker, or Docs returns connection refused or HTTP 500

**Diagnosis:**
```bash
curl -sf http://localhost:8091/healthz && echo "Filesystem OK" || echo "Filesystem DOWN"
curl -sf http://localhost:8092/healthz && echo "Docker OK"     || echo "Docker DOWN"
curl -sf http://localhost:8093/healthz && echo "Docs OK"       || echo "Docs DOWN"
```

**Filesystem/Docs (Docker containers):**
```bash
docker ps | grep mcp-  # check containers are running
docker logs mcp-filesystem-remote --tail 20
docker logs mcp-docs-remote --tail 20

# Restart
cd ~/repos/integrated-ai-platform/docker
docker compose -f obot-stack.yml restart mcp-filesystem-remote mcp-docs-remote
```

**Docker MCP (macOS host nohup process):**
```bash
# Check if running
cat ~/mcp-servers/remote/docker.pid | xargs ps -p 2>/dev/null || echo "Process dead"
tail -20 ~/mcp-servers/remote/logs/docker.log

# Restart
kill $(cat ~/mcp-servers/remote/docker.pid) 2>/dev/null
nohup /bin/bash ~/mcp-servers/remote/mcp-docker.sh \
  > ~/mcp-servers/remote/logs/docker.log 2>&1 &
echo $! > ~/mcp-servers/remote/docker.pid
```

## Issue: Tool Cache Cross-Wired

**Symptoms:** Server shows wrong tool list (e.g., PostgreSQL tools appearing under GitHub)

**Root cause:** Obot's in-memory tool cache not invalidated after server re-registration

**Solution:**
```bash
cd ~/repos/integrated-ai-platform/docker
docker compose -f obot-stack.yml restart obot
# Wait ~30s, then re-verify
curl -s http://localhost:8090/api/mcp-servers/<id>/tools | python3 -c \
  "import json,sys; [print(t['name']) for t in json.load(sys.stdin)]"
```

## Issue: GitHub Rate Limit Exceeded

**Symptoms:** "API rate limit exceeded", 429 errors from GitHub tools

```bash
# Check remaining rate limit
source ~/repos/integrated-ai-platform/docker/.env
curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit \
  | python3 -c "import json,sys; d=json.load(sys.stdin); r=d['rate']; print(f'Remaining: {r[\"remaining\"]}/{r[\"limit\"]}, resets at {r[\"reset\"]}')"
```

Wait for reset or rotate to a new token (see `rotate-credentials.md`).

## Issue: Docs Server tree-sitter Missing

**Symptoms:** `mcp-docs-remote` container exits immediately, logs show "No native build was found"

**Root cause:** `@arabold/docs-mcp-server` uses `tree-sitter` (native binary), no prebuilt binary for linux/arm64 ABI 127 (Node 22)

**Solution:** The `obot-stack.yml` command uses `npm install -g` to trigger node-gyp compilation. If this fails:
```bash
docker logs mcp-docs-remote 2>&1 | grep -i "error\|gyp\|tree-sitter"

# Check build tools are installed in container
docker exec mcp-docs-remote which python3 make g++

# Force rebuild
cd ~/repos/integrated-ai-platform/docker
docker compose -f obot-stack.yml up -d --force-recreate mcp-docs-remote
docker logs -f mcp-docs-remote  # wait for "Listening on port 8093"
```

## Issue: Obot Won't Start

**Symptoms:** Container exits, port conflict, or health check fails

```bash
# Check port conflict
lsof -i :8090
# Check logs
docker logs obot --tail 50

# Clean restart
cd ~/repos/integrated-ai-platform/docker
docker compose -f obot-stack.yml down obot
docker compose -f obot-stack.yml up -d obot
```

## Issue: `register_obot_tools.py` Fails with HTTP Error

**Symptoms:** Script shows `FAILED — HTTP 4xx: ...`

```bash
# Check Obot is healthy
curl -s http://localhost:8090/api/healthz

# Check what's already registered (to avoid duplicate errors)
python3 bin/register_obot_tools.py --check

# Re-run registration (skips already-registered by name)
python3 bin/register_obot_tools.py
```

## Diagnostic Quick-Reference

```bash
# Check all remote endpoints
for port in 8091 8092 8093; do
  curl -sf http://localhost:$port/healthz && echo ":$port OK" || echo ":$port DOWN"
done
curl -sf http://localhost:8090/api/healthz && echo "Obot OK" || echo "Obot DOWN"

# List all registered servers
curl -s http://localhost:8090/api/mcp-servers | python3 -c "
import json,sys
for s in json.load(sys.stdin).get('items',[]):
    print(s['manifest']['runtime'].ljust(8), s['manifest']['name'])
"

# Count tools per server
curl -s http://localhost:8090/api/mcp-servers | python3 -c "
import json,sys,urllib.request
for s in json.load(sys.stdin).get('items',[]):
    try:
        r=urllib.request.urlopen(f'http://localhost:8090/api/mcp-servers/{s[\"id\"]}/tools',timeout=20)
        n=len(json.loads(r.read()))
    except: n='?'
    print(f'{str(n).rjust(3)} tools  {s[\"manifest\"][\"name\"]}')
"
```
