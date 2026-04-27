# Runbook: Add New MCP Server

## Prerequisites

- MCP server package identified (npm or GitHub repo)
- Credentials ready (if required)
- Port allocated (for remote HTTP servers: next available after 8093)

## Choosing a Deployment Model

| Scenario | Model | Why |
|----------|-------|-----|
| Stateless npx package, no host deps | NPX phat | Obot manages lifecycle |
| Needs filesystem access | Remote HTTP | Phat containers can't mount host volumes |
| Needs Docker socket | Remote HTTP | Colima socket not accessible in containers |
| Has native binaries (node-gyp) | Remote HTTP | Phat containers lack build tools at runtime |

## Option A: NPX Phat Container

### Step 1: Verify the package works

```bash
npx -y <package-name> --help 2>&1 | head -5
```

### Step 2: Add to `bin/register_obot_tools.py`

```python
{
    "id": "my-server",
    "manifest": {
        "name": "My Server",
        "shortDescription": "One-line description",
        "runtime": "npx",
        "npxConfig": {
            "package": "<package-name>",
            "args": [],
        },
        # Include if credentials needed:
        "env": [
            {
                "name": "API Key",
                "key": "MY_SERVER_API_KEY",
                "value": MY_SERVER_API_KEY,
                "description": "API key for my-server",
                "sensitive": True,
            }
        ],
    },
    # Include if credentials are optional:
    "skip_if": not MY_SERVER_API_KEY,
    "skip_reason": "MY_SERVER_API_KEY not set in docker/.env",
},
```

### Step 3: Add credentials to `docker/.env` (if needed)

```bash
echo "MY_SERVER_API_KEY=your_key_here" >> ~/repos/integrated-ai-platform/docker/.env
```

### Step 4: Register

```bash
cd ~/repos/integrated-ai-platform
python3 bin/register_obot_tools.py
```

## Option B: Remote HTTP Service

### Step 1: Add to `docker/obot-stack.yml`

```yaml
mcp-myserver-remote:
  image: node:22-slim
  container_name: mcp-myserver-remote
  restart: unless-stopped
  ports:
    - "8094:8094"
  networks:
    - obot-net
  command:
    - sh
    - -c
    - "npm install -g <package-name> && npx -y supergateway --stdio '<binary-name>' --outputTransport streamableHttp --port 8094 --cors --healthEndpoint /healthz"
  healthcheck:
    test: ["CMD-SHELL", "curl -sf http://localhost:8094/healthz || exit 1"]
    interval: 15s
    timeout: 10s
    retries: 5
    start_period: 180s
```

### Step 2: Start the container

```bash
cd ~/repos/integrated-ai-platform/docker
docker compose -f obot-stack.yml up -d mcp-myserver-remote
docker logs -f mcp-myserver-remote  # wait for "Listening on port 8094"
```

### Step 3: Add to `bin/register_obot_tools.py`

```python
{
    "id": "my-server",
    "manifest": {
        "name": "My Server",
        "shortDescription": "One-line description",
        "runtime": "remote",
        "remoteConfig": {
            "url": "http://host.docker.internal:8094/mcp",
        },
    },
},
```

### Step 4: Register

```bash
cd ~/repos/integrated-ai-platform
python3 bin/register_obot_tools.py
```

## Validation

```bash
# Get the server ID from the registration output, then:
curl -s http://localhost:8090/api/mcp-servers/<server-id>/tools | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} tools: {[t[\"name\"] for t in d[:5]]}')"
```
