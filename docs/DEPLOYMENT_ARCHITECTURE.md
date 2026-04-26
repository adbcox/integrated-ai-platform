# Deployment Architecture

## Overview

The platform is split across two machines:

| Role | Host | Responsibilities |
|------|------|-----------------|
| **Control / Dashboard** | Mac Mini | Homepage portal, AI dashboard, Docker stack, monitoring |
| **Compute / Model** | Mac Studio | Ollama, executor workers, training, heavy inference |

Both machines share the same git repository. The Mac Mini polls Mac Studio's APIs for status and uses SSH to start/stop the executor.

---

## Mac Mini — Control Plane

**Services (Docker Compose):**

```
docker/docker-compose-dashboards.yml
├── homepage            (port 3000) — Master Control Panel portal
├── ai-platform-dashboard (port 8080) — Roadmap executor control
├── docker-socket-proxy              — Read-only Docker API proxy
└── traefik             (port 80/443) — Reverse proxy + HTTPS
```

**Volume mounts:**
- `../docs/roadmap/ITEMS` → `/app/docs/roadmap/ITEMS` (read-only)
- `../.git` → `/app/.git` (read-only, for git log)
- `/tmp` → `/app/logs` (executor log files, read-write)

**Key environment variables** (set in `docker/.env`):
```
EXECUTOR_HOST=mac-studio.local     # SSH target for remote executor
OLLAMA_HOST=mac-studio.local:11434 # Ollama on Mac Studio
REMOTE_REPO_ROOT=~/repos/integrated-ai-platform
```

---

## Mac Studio — Compute Plane

**Native services (not containerized):**

```
Ollama              (port 11434) — LLM inference server
bin/auto_execute_roadmap.py      — Autonomous executor
bin/run_training_cycle.py        — LoRA training
Glances             (port 61208) — System metrics for Homepage widget
```

**Why not containerized?**
- Ollama needs direct GPU/Neural Engine access (Docker GPU passthrough on macOS is unreliable)
- Training environment has custom venv dependencies (see docs/TRAINING.md)

---

## Network Topology

```
Internet
    │
  Router
    │
  ┌─────────────────────┐         ┌──────────────────────┐
  │     Mac Mini        │         │     Mac Studio       │
  │  (192.168.x.10)     │◄──SSH───│  (192.168.x.20)      │
  │                     │         │                      │
  │  Homepage :3000     │         │  Ollama    :11434    │
  │  AI Dashboard :8080 │         │  Executor  (proc)    │
  │  Traefik   :80/443  │         │  Glances   :61208    │
  └─────────────────────┘         └──────────────────────┘
```

---

## Communication Paths

### Dashboard → Mac Studio (status polling)
```
http://mac-studio.local:11434/api/tags    → Ollama model list
http://mac-studio.local:11434/api/ps      → Running models
http://mac-studio.local:61208             → CPU/RAM via Glances
```

### Dashboard → Mac Studio (executor control)
```
ssh mac-studio.local 'nohup python3 .../auto_execute_roadmap.py ...'  # start
ssh mac-studio.local 'pkill -TERM -f auto_execute_roadmap'             # stop
ssh mac-studio.local 'tail -200 /tmp/executor_longrun.log'             # logs
```

The SSH connection uses key-based auth — no passwords. Set up with:
```bash
ssh-copy-id mac-studio.local
```

---

## Shared Data

| Data | Location | Access |
|------|----------|--------|
| Roadmap ITEMS | `docs/roadmap/ITEMS/` in repo | Both machines read via git |
| Executor logs | `/tmp/executor_*.log` on Mac Studio | Dashboard reads via SSH |
| Training data | `artifacts/training_data/` in repo | Mac Studio writes, git syncs |
| LoRA adapter | `artifacts/lora_adapter/` in repo | Mac Studio writes, Ollama loads |
| Git history | `.git/` | Both machines read locally |

---

## Deployment Steps

### Initial setup

1. **Mac Studio** (run once):
   ```bash
   ./bin/deploy_to_mac_studio.sh
   ```

2. **Mac Mini** — set SSH key auth:
   ```bash
   ssh-keygen -t ed25519       # if no key exists
   ssh-copy-id mac-studio.local
   ```

3. **Mac Mini** — configure and deploy:
   ```bash
   cp docker/.env.example docker/.env
   # Edit docker/.env — set EXECUTOR_HOST=mac-studio.local
   ./bin/deploy_to_mac_mini.sh
   ```

4. Open `http://mac-mini.local:3000` for the Master Control Panel.

### Updating

```bash
git pull
./bin/deploy_to_mac_mini.sh          # rebuilds dashboard container
./bin/deploy_to_mac_studio.sh        # re-syncs and restarts Ollama if needed
```

---

## Portability

All services are configured via environment variables. Moving to a new host:

1. Clone the repo on the new host
2. Copy `docker/.env` (update hostnames)
3. Run the appropriate deploy script
4. Update DNS/firewall rules

The Docker Compose files use no hardcoded IPs or paths — everything is parameterized.
