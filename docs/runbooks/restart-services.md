# Runbook: Restart MCP Services

## Restart Obot Gateway

```bash
cd ~/repos/integrated-ai-platform/docker
docker compose -f obot-stack.yml restart obot

# Verify
curl -f http://localhost:8090/api/healthz
```

**Expected:** 200 OK within 10 seconds. Phat containers need 20-30s cold start after Obot restarts.

## Restart Remote HTTP Services

### Filesystem & Docs (Docker Compose)

```bash
cd ~/repos/integrated-ai-platform/docker
docker compose -f obot-stack.yml restart mcp-filesystem-remote mcp-docs-remote

# Verify
curl -sf http://localhost:8091/healthz && echo "✅ Filesystem"
curl -sf http://localhost:8093/healthz && echo "✅ Docs"
```

### Docker MCP (macOS host process)

The Docker MCP server runs as a nohup process on the macOS host:

```bash
# Check if running
cat ~/mcp-servers/remote/docker.pid | xargs ps -p 2>/dev/null || echo "Not running"

# Restart
kill $(cat ~/mcp-servers/remote/docker.pid) 2>/dev/null
nohup /bin/bash ~/mcp-servers/remote/mcp-docker.sh \
  > ~/mcp-servers/remote/logs/docker.log 2>&1 &
echo $! > ~/mcp-servers/remote/docker.pid

# Verify
curl -sf http://localhost:8092/healthz && echo "✅ Docker"
```

**For persistence across reboots:** Load the launchd agent from a terminal (GUI session required):
```bash
launchctl load ~/Library/LaunchAgents/com.iap.mcp.docker.plist
launchctl load ~/Library/LaunchAgents/com.iap.mcp.docs.plist
```

## Restart All NPX Services

NPX services are managed by Obot phat containers — restart Obot to restart all:

```bash
cd ~/repos/integrated-ai-platform/docker
docker compose -f obot-stack.yml restart obot
```

**Note:** 20-30s cold start for phat containers on first tool call after restart.

## Restart Everything

```bash
cd ~/repos/integrated-ai-platform/docker
docker compose -f obot-stack.yml restart

# Check all remote endpoints are up
curl -sf http://localhost:8091/healthz && echo "✅ Filesystem"
curl -sf http://localhost:8092/healthz && echo "✅ Docker MCP"
curl -sf http://localhost:8093/healthz && echo "✅ Docs"
curl -sf http://localhost:8090/api/healthz && echo "✅ Obot"
```
