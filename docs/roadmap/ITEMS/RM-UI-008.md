# RM-UI-008

- **ID:** `RM-UI-008`
- **Title:** Specialized context dashboards for media, home automation, and system monitoring
- **Category:** `UI`
- **Type:** `Feature`
- **Status:** `Planned`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P3`
- **Queue rank:** `TBD`
- **Target horizon:** `later`
- **LOE:** `M`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `3`
- **Readiness:** `later`

## Description

Build specialized context dashboards for media control, home automation, and system monitoring by extending RM-UI-006 dashboard platform with focused widget layouts per domain.

## Why it matters

Platform has ambient tablet themes (RM-UI-003/004 for rooms) but lacks function-specific dashboards:
- Media control (Plex/Jellyfin/*arr stack)
- Home automation (Home Assistant)
- System monitoring (Grafana/Uptime Kuma/Docker)

## Relationship to existing items

**vs RM-UI-003/004:** Room-specific (kitchen/hallway) vs function-specific (media/automation)
**vs RM-UI-001:** Operator overview vs deep service integration
**Reuses RM-UI-006:** Built on Homepage/Homarr, no custom framework

## Key requirements

### Media dashboard
**Services:** Plex/Jellyfin, Sonarr/Radarr/Lidarr, Overseerr, Tautulli, qBittorrent
**Features:** Poster display, media calendar, download progress, library stats
**Targets:** 55" media wall, tablet controls, mobile status

### Home automation dashboard
**Services:** Home Assistant Lovelace, MQTT status, automation triggers
**Features:** Room-based controls, scene triggers, energy monitoring
**Targets:** Wall-mounted tablets, mobile controls

### System monitoring dashboard
**Services:** Grafana, Uptime Kuma, Homepage resource widgets, Docker stats
**Features:** Multi-host metrics, GPU utilization, container health, alerts
**Targets:** 55" NOC wall, desktop troubleshooting, mobile alerts

### Cross-cutting
- All behind same auth as RM-UI-006
- Shared docker-socket-proxy
- Responsive per device
- Dark mode
- Config-as-code (YAML)

## Dependencies

- `RM-UI-006` - Dashboard platform
- `RM-MEDIA-*` - Media services
- `RM-HOME-*` - Home automation
- `RM-OPS-004/005` - Monitoring/telemetry
- Grafana, Uptime Kuma, Home Assistant

## Expected files

- `config/homepage/dashboards/media/services.yaml`
- `config/homepage/dashboards/home/services.yaml`
- `config/homepage/dashboards/monitoring/services.yaml`
- `config/grafana/*.json`
- `scripts/sys_monitor.py`
- `docs/runbooks/SPECIALIZED_DASHBOARDS.md`

## External dependencies

### Homepage service widgets
- Docs: https://gethomepage.dev/widgets/services/
- 100+ widgets: Plex, Sonarr, Radarr, Home Assistant, Grafana, Uptime Kuma, Docker
- Adoption: `adopt-now`

### Grafana
- Docs: https://grafana.com/docs/
- Time-series metrics, iframe embedding
- Adoption: `adopt-selective`

### Uptime Kuma
- Repo: https://github.com/louislam/uptime-kuma
- Service uptime monitoring
- Adoption: `adopt-selective`

### Home Assistant Lovelace
- Docs: https://www.home-assistant.io/lovelace/
- Primary home automation interface
- Adoption: `adopt-now`

## First milestone

Media dashboard with:
1. Config created (services.yaml variant)
2. Plex/Jellyfin + Sonarr/Radarr widgets
3. Download client widget
4. Layout optimized for 55" display
5. Responsive on tablet/mobile
6. Behind same auth as main dashboard
7. API rate limits validated

## Autonomous execution guidance

### Pre-implementation
1. Verify RM-UI-006 deployed and stable
2. Choose first dashboard (recommend media)
3. Confirm services deployed (Plex/*arr/HA/Grafana)
4. Check Homepage widget docs
5. Collect API keys/tokens

### Implementation (media dashboard example)
1. Create `config/homepage/dashboards/media/`
2. Copy baseline services.yaml
3. Configure media service groups:
   - Media Libraries (Plex/Jellyfin)
   - Content Management (Sonarr/Radarr/Lidarr)
   - Download Clients (qBittorrent)
   - Requests (Overseerr)
4. Add widgets with API tokens
5. Store tokens in `.env.dashboards` (not git)
6. Configure layout for device sizes
7. Deploy (separate instance or multi-config)
8. Validate: live data, no rate limits, responsive, authed

### Completion contract
- First specialized dashboard deployed (media recommended)
- Uses Homepage/Homarr widgets (no custom code)
- 3+ services with live data
- Layout optimized for primary device
- Responsive across sizes
- Behind authentication
- API tokens secured
- Documentation complete

## Status transition

- Next: `In Progress`
- Condition: RM-UI-006 stable, services deployed, first dashboard chosen
- Closeout: Dashboard deployed with 3+ widgets, responsive, authed, documented

## Notes

Implementation order:
1. **Media first** - High visual impact, clear service set
2. **Monitoring second** - Ops value, reuses Grafana/Uptime Kuma
3. **Home automation last** - Depends on RM-HOME-* maturity

Avoid dashboard sprawl: only create when RM-UI-006 generic dashboard insufficient.
