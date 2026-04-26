# Migration Guide — Mac Mini + Mac Studio Split

This guide covers migrating from the current single-machine setup to the dual-machine architecture where Mac Mini hosts dashboards and Mac Studio hosts compute.

## Current State (single machine)

```
Mac Mini
├── Ollama :11434
├── Executor (local processes)
├── Dashboard :8080 (native Python process)
└── Training venv
```

## Target State (dual machine)

```
Mac Mini (control)          Mac Studio (compute)
├── Homepage :3000          ├── Ollama :11434
├── AI Dashboard :8080      ├── Executor (autonomous)
├── Traefik :80/443         ├── Training
└── docker-socket-proxy     └── Glances :61208
```

---

## Migration Steps

### Step 1: Set Up Mac Studio

Run on Mac Studio (or SSH from Mac Mini):

```bash
./bin/deploy_to_mac_studio.sh
```

This:
1. Verifies Ollama is running (starts it if not)
2. Pulls the default model (`qwen2.5-coder:14b`)
3. Syncs the repo
4. Installs and starts Glances (system metrics)

Verify Ollama is accessible from Mac Mini:
```bash
curl http://mac-studio.local:11434/api/tags
```

### Step 2: Set Up SSH Key Auth

The dashboard uses SSH to control the executor on Mac Studio. Set up key-based auth:

```bash
# On Mac Mini:
ssh-keygen -t ed25519 -C "mac-mini → mac-studio" -f ~/.ssh/id_ed25519_studio
ssh-copy-id -i ~/.ssh/id_ed25519_studio.pub mac-studio.local

# Test:
ssh mac-studio.local echo "auth works"
```

Pass the key path as a Docker secret if needed:
```bash
# In docker/.env:
SSH_KEY_PATH=~/.ssh/id_ed25519_studio
```

### Step 3: Configure Mac Mini Environment

```bash
cp docker/.env.example docker/.env
```

Edit `docker/.env`:
```bash
EXECUTOR_HOST=mac-studio.local
REMOTE_REPO_ROOT=~/repos/integrated-ai-platform
OLLAMA_HOST=mac-studio.local:11434
```

### Step 4: Stop Local Services on Mac Mini

Stop the existing native dashboard:
```bash
pkill -f "python3 web/dashboard/server.py" || true
```

Stop local Ollama (if you're moving it to Mac Studio only):
```bash
# Only do this AFTER confirming Mac Studio Ollama works
launchctl unload ~/Library/LaunchAgents/com.ollama.ollama.plist 2>/dev/null || true
pkill ollama || true
```

### Step 5: Deploy Docker Stack on Mac Mini

```bash
./bin/deploy_to_mac_mini.sh
```

Or manually:
```bash
docker compose -f docker/docker-compose-dashboards.yml up -d
```

### Step 6: Verify

```bash
# Dashboard health
curl http://localhost:8080/api/health

# Widget data
curl http://localhost:8080/api/embed/widget

# Check executor control (should SSH to Mac Studio)
curl -X POST http://localhost:8080/api/executor \
  -H "Content-Type: application/json" \
  -d '{"action":"status"}'

# Homepage
open http://localhost:3000
```

---

## Rollback

To revert to the native single-machine setup:

```bash
# Stop Docker stack
docker compose -f docker/docker-compose-dashboards.yml down

# Start native dashboard
python3 web/dashboard/server.py &

# Unset EXECUTOR_HOST (dashboard goes back to local mode)
unset EXECUTOR_HOST
```

---

## Networking Notes

### Firewall rules needed on Mac Studio

| Port | Service | Who accesses |
|------|---------|-------------|
| 22   | SSH     | Mac Mini (executor control) |
| 11434 | Ollama | Mac Mini (dashboard status) |
| 61208 | Glances | Mac Mini (Homepage widget) |

On macOS, go to **System Settings → Network → Firewall** and add exceptions, or use:
```bash
# On Mac Studio:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add $(which ollama)
```

### mDNS resolution

`mac-mini.local` and `mac-studio.local` resolve via Bonjour on a local network. If they don't resolve, use static IPs and update `docker/.env`:
```
EXECUTOR_HOST=192.168.1.20
OLLAMA_HOST=192.168.1.20:11434
```

---

## After Migration

Once both machines are running:

1. Open `http://mac-mini.local:3000` — Homepage shows all services
2. The AI Platform widget shows live roadmap stats from the dashboard API
3. Start/stop executor from the dashboard → SSH commands run on Mac Studio
4. Ollama status shown from Mac Studio's API

Future roadmap items that become relevant post-migration:
- **RM-SCALE-***: Scaling strategies now that compute is separate
- **RM-HOME-***: Home Assistant integrations visible in Homepage
- **RM-FLOW-***: Workflow automation across both machines
