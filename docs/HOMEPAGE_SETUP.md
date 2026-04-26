# Homepage Setup Guide

Homepage is the Master Control Panel top tier. It aggregates all services into a single portal.

## Quick Start

```bash
# 1. Create environment file
cp docker/.env.example docker/.env
# Edit docker/.env — fill in DOMAIN, API keys, etc.

# 2. Deploy (includes Homepage + AI dashboard + Traefik)
docker compose -f docker/docker-compose-dashboards.yml up -d

# 3. Open
open http://localhost:3000
```

## Configuration Files

All Homepage config lives in `config/homepage/`:

| File | Purpose |
|------|---------|
| `services.yaml` | Service groups, links, and widgets |
| `widgets.yaml` | Top-bar system widgets (CPU, time, search) |
| `docker.yaml` | Docker integration for auto-discovery |
| `settings.yaml` | Theme, layout, global options |
| `custom.css` | Matches AI Platform design system |

These files are volume-mounted into the Homepage container — edit them and the UI refreshes without restart.

## Adding a New Service

Edit `config/homepage/services.yaml`:

```yaml
- My Group:
    - My Service:
        href: "http://mac-mini.local:PORT"
        description: "What it does"
        icon: "icon-name.png"   # from https://github.com/walkxcode/dashboard-icons
        # Optional widget — shows live stats
        widget:
          type: customapi
          url: "http://service-host:PORT/api/status"
          method: GET
          mappings:
            - field: my_metric
              label: My Metric
              format: number
```

## AI Platform Widget

The AI Platform dashboard exposes `/api/embed/widget` for the Homepage widget:

```json
{
  "completions": 42,
  "accepted": 8,
  "in_progress": 3,
  "pending": 127,
  "total": 180,
  "success_rate": 28,
  "executor_running": true,
  "current_item": "RM-FLOW-001",
  "ollama_available": true,
  "cpu_pct": 45.2,
  "ram_used_pct": 62
}
```

Widget config in `services.yaml` (already included):
```yaml
widget:
  type: customapi
  url: "http://ai-platform-dashboard:8080/api/embed/widget"
  method: GET
  mappings:
    - field: completions
      label: Completed
      format: number
    - field: in_progress
      label: In Progress
      format: number
    - field: success_rate
      label: Success
      format: percent
```

## API Keys / Secrets

Homepage uses environment variable injection. In `docker/.env`:
```
HOMEPAGE_VAR_HASS_TOKEN=your_token_here
HOMEPAGE_VAR_PLEX_TOKEN=your_token_here
```

In `services.yaml`, reference with:
```yaml
key: "{{HOMEPAGE_VAR_HASS_TOKEN}}"
```

These are never written to the config files — always pulled from the environment at runtime.

## Docker Auto-Discovery

Services with Homepage labels in their `docker-compose` files are automatically discovered. The AI Platform dashboard already has these labels:

```yaml
labels:
  homepage.group: "AI & Automation"
  homepage.name: "AI Platform"
  homepage.description: "Roadmap executor control plane"
  homepage.href: "http://mac-mini.local:8080"
  homepage.icon: "robot.png"
```

To use auto-discovery, set `config/homepage/docker.yaml` to point at the socket proxy.

## Custom Theme

The `config/homepage/custom.css` file applies the AI Platform design system (GitHub dark palette, Inter font, Atlassian blue accent) to Homepage. Add to `settings.yaml`:

```yaml
# This is loaded automatically when custom.css exists in config/
```

## Reverse Proxy (Traefik)

With Traefik deployed, access via:
- `https://dashboard.home.local` → Homepage
- `https://ai.home.local` → AI Platform dashboard

Update `DOMAIN=home.local` in `docker/.env` and add DNS entries (or `/etc/hosts`):
```
192.168.x.10  dashboard.home.local ai.home.local
```

## Troubleshooting

**Services show as unknown/offline:**
- Verify the URL is reachable from inside the Docker network
- Use container name (e.g., `ai-platform-dashboard`) instead of `localhost` for same-stack services

**Widget data not loading:**
- Check CORS: the dashboard sends `Access-Control-Allow-Origin: *` on all responses
- Verify `/api/embed/widget` returns 200: `curl http://localhost:8080/api/embed/widget`

**Custom CSS not applying:**
- Confirm `custom.css` is in `config/homepage/` (not a subdirectory)
- Hard-refresh browser (Cmd+Shift+R)
