# Network Architecture

Three-node homelab: Mac Mini (orchestrator/dashboards), Mac Studio (compute/AI), QNAP NAS (media/storage).

## Node Inventory

| Host | mDNS | IP | Role |
|------|------|----|------|
| Mac Mini | `mac-mini.local` | DHCP | Orchestrator, dashboards, Homepage portal |
| Mac Studio | `mac-studio.local` | DHCP | Ollama inference, aider execution, model training |
| QNAP NAS | — | `192.168.10.201` | *Arr media stack, file storage, Plex (future) |

## Port Allocation

### Mac Mini (`mac-mini.local`)

| Port | Service | Notes |
|------|---------|-------|
| 3000 | Homepage portal | Docker container |
| 8080 | AI Platform Dashboard | Docker container (dashboard API + UI) |
| 8090 | Traefik dashboard | Reverse proxy control plane |
| 9000 | Portainer | Container management UI |
| 9443 | Portainer HTTPS | — |
| 32400 | Plex Media Server | Direct install (future migration) |
| 61208 | Glances API | System metrics for Homepage widget |

### Mac Studio (`mac-studio.local`)

| Port | Service | Notes |
|------|---------|-------|
| 11434 | Ollama | LLM inference (qwen2.5-coder, deepseek-coder-v2, etc.) |
| 8080 | (reserved) | May host executor dashboard mirror |
| 61208 | Glances API | System metrics for Homepage widget |

### QNAP NAS (`192.168.10.201`)

| Port | Service | Notes |
|------|---------|-------|
| 8989 | Sonarr | TV series automation |
| 7878 | Radarr | Movie automation |
| 9696 | Prowlarr | Indexer management |

## Docker Runtime

Mac Mini uses **colima** (not Docker Desktop) for headless Docker:

```bash
# Check status
colima status

# Start manually if needed
colima start --runtime docker --cpu 2 --memory 4

# Socket path (set DOCKER_HOST to use docker CLI)
export DOCKER_HOST="unix://${HOME}/.colima/default/docker.sock"
```

Auto-start: `~/Library/LaunchAgents/com.colima.docker.plist` loads colima at login.

## Deployed Docker Stacks

### Mac Mini — Full dashboard stack

```bash
cd ~/repos/integrated-ai-platform
export DOCKER_HOST="unix://${HOME}/.colima/default/docker.sock"
docker compose -f docker/docker-compose-dashboards.yml up -d
```

Services: Homepage (3000), AI Dashboard (8080), Traefik (80/443/8090), docker-socket-proxy (internal).

### Mac Mini — Dashboard only (lightweight)

```bash
docker compose -f docker/docker-compose-ai-dashboard.yml up -d
```

## Service Discovery

Homepage auto-discovers Docker containers via Docker socket proxy. Services not in Docker
(like the *Arr stack on QNAP) are configured statically in `config/homepage/services.yaml`.

Media services use the AI Dashboard's `/api/media/status` endpoint for live stats aggregation:
- Sonarr series/episode counts + queue depth
- Radarr movie counts + download status
- Prowlarr indexer health
- Plex active streams + library counts

## Key Environment Variables

Managed in `docker/.env` (gitignored, copy from `docker/.env.example`):

| Variable | Used by | Description |
|----------|---------|-------------|
| `EXECUTOR_HOST` | Dashboard | SSH target for remote executor (Mac Studio) |
| `OLLAMA_HOST` | Dashboard | Ollama API host:port |
| `SONARR_API_KEY` | MediaDomain | Sonarr authentication |
| `RADARR_API_KEY` | MediaDomain | Radarr authentication |
| `PROWLARR_API_KEY` | MediaDomain | Prowlarr authentication |
| `PLEX_TOKEN` | MediaDomain | Plex authentication token |

## mDNS Addressing

All services use `.local` mDNS names for LAN addressing. If mDNS resolution fails,
use direct IPs or add entries to `/etc/hosts`.

## Mac Studio Integration

When executor runs on Mac Studio:

1. Set `EXECUTOR_HOST=mac-studio.local` in `docker/.env`
2. Ensure SSH key auth is set up: `ssh-copy-id mac-studio.local`
3. Mac Studio needs the repo cloned at `REMOTE_REPO_ROOT` path
4. Dashboard start/stop buttons will SSH to Mac Studio to manage the executor process

Deploy to Mac Mini: `./bin/deploy_to_mac_mini.sh`
Deploy compute to Mac Studio: `./bin/deploy_to_mac_studio.sh`
