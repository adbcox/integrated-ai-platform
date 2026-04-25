# RM-UI-006

- **ID:** `RM-UI-006`
- **Title:** Self-hosted responsive dashboard platform with Homepage/Homarr integration
- **Category:** `UI`
- **Type:** `System`
- **Status:** `In progress`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `TBD`
- **Target horizon:** `soon`
- **LOE:** `M`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `2`
- **Dependency burden:** `3`
- **Readiness:** `near`

## Description

Build the infrastructure-level self-hosted dashboard platform that provides unified service/app access across all devices (iPhone → MacBook → tablets → 55" displays) using Homepage (gethomepage.dev) as primary with Homarr as GUI alternative for non-technical users.

This item establishes the reusable dashboard substrate that underlies RM-UI-001 (master control center), RM-UI-002 (tile navigation), and RM-UI-003/004 (ambient tablet displays) but is not explicitly covered by any existing item.

## Why it matters

The platform currently lacks an infrastructure-level dashboard system that:
- unifies service/app access across heterogeneous device sizes and contexts,
- provides live status checking and widget integration with Docker/services/monitoring,
- serves as a single self-hosted surface accessible from any device,
- follows a reuse-first approach using mature external platforms rather than building custom dashboard infrastructure.

Without this foundation, each UI surface risks becoming a separate silo with duplicated service-integration logic and inconsistent presentation across devices.

## Reuse-first implementation approach

This item follows explicit reuse-first posture per `docs/architecture/OSS_REUSE_AND_ADOPTION_REGISTER.md`.

**Primary choice: Homepage (gethomepage.dev)**
- Reason: 100+ service integrations, YAML-based config-as-code, Docker auto-discovery, server-side rendered (fast), ~50MB RAM, 165k+ GitHub stars, mature and actively maintained
- Mode: Adopt as full product
- Config structure: `services.yaml`, `widgets.yaml`, `docker.yaml`, `settings.yaml`
- Deployment: Docker via `ghcr.io/gethomepage/homepage:latest`
- Security posture: Must sit behind reverse proxy (no built-in auth); Docker socket via docker-socket-proxy for security

**Secondary choice: Homarr**
- Reason: Drag-and-drop GUI config, no YAML required, media integrations (Sonarr/Radarr/Plex), calendar widget, heavier but beginner-friendly
- Mode: Adopt as full product selectively (for non-technical operator surfaces)
- Deployment: Docker via `ghcr.io/ajnart/homarr:latest`
- Use case: Operator surfaces where GUI config is preferred over YAML

**Not to rebuild:**
- generic dashboard framework,
- service status checking,
- widget system,
- Docker auto-discovery,
- responsive layouts,
- icon/theme management.

## Key requirements

### Core dashboard platform requirements
- Deploy Homepage as primary dashboard infrastructure
- Configure Docker socket access via docker-socket-proxy (security)
- Establish reverse proxy requirement with authentication (Traefik, Nginx Proxy Manager, or Authelia)
- Configure HOMEPAGE_ALLOWED_HOSTS environment variable properly
- Support responsive layouts from iPhone (narrow) → MacBook (standard) → tablets (ambient) → 55" displays (wall)
- Enable Docker auto-discovery via labels
- Configure service integrations for key platform services

### Widget and integration requirements
- Configure 100+ available service widgets where relevant:
  - Infrastructure: Proxmox, Docker, Portainer
  - Media: Plex, Jellyfin, Sonarr, Radarr, Overseerr
  - Home automation: Home Assistant
  - Monitoring: Pi-hole, Uptime Kuma, Grafana
  - System: CPU/RAM/disk widgets
- Establish widget configuration patterns in widgets.yaml
- Document API key/token management for service integrations
- Configure system resource widgets (CPU, memory, disk, network)

### Configuration-as-code requirements
- All primary config in YAML files under version control
- services.yaml: Service definitions, groups, links
- widgets.yaml: System widgets (resources, weather, time)
- docker.yaml: Docker instance connections
- settings.yaml: Global dashboard settings, themes
- Document config structure for future additions
- Validate config changes before deployment

### Docker and deployment requirements
- Docker Compose deployment pattern
- Volume mounts for persistent config
- docker-socket-proxy container for secure Docker socket access
- Network isolation between Homepage and socket proxy
- Health checks and restart policies
- Resource limits appropriate for dashboard workload (~50-100MB RAM)
- Log rotation and monitoring

### Security and access control requirements
- Homepage sits behind reverse proxy (Traefik recommended)
- Reverse proxy enforces authentication (Authelia, OAuth, or basic auth)
- TLS/SSL certificates via Let's Encrypt or internal CA
- Docker socket access only via docker-socket-proxy (read-only)
- API keys stored in environment variables or secrets
- Host header validation via HOMEPAGE_ALLOWED_HOSTS
- No direct internet exposure without auth layer

### Homarr secondary surface requirements (optional)
- Deploy Homarr as alternative for GUI-first users
- Share docker-socket-proxy with Homepage
- Separate port binding (Homepage: 3000, Homarr: 7575)
- Document when to use Homarr vs Homepage
- Both surfaces behind same auth layer
- Homarr for: drag-and-drop layout, media calendar, visual editing
- Homepage for: config-as-code, deepest integrations, lightest resources

### Device-specific optimization requirements
- Mobile (iPhone): Single-column layout, essential services only
- Tablet (ambient): Room-specific layouts with glanceable info
- Desktop (MacBook): Multi-column with detailed widgets
- Large display (55"): Wall-of-data with comprehensive monitoring
- Responsive breakpoints configured in settings.yaml
- Device-specific service groups where helpful

### Integration point requirements
- Expose dashboard to RM-UI-001 (master control center)
- Provide service list to RM-UI-002 (tile navigation)
- Support ambient themes from RM-UI-004 (kitchen/entertainment/hallway)
- Connect monitoring widgets to RM-OPS-005 (telemetry)
- Surface Docker stats for execution control (RM-UI-005)
- Integration with Home Assistant for RM-HOME-* items
- Media service widgets for RM-MEDIA-* items

## Affected systems

- Dashboard infrastructure layer
- All UI surfaces requiring service access
- Docker service discovery and status monitoring
- Reverse proxy and authentication layer
- System monitoring and telemetry display
- Home automation integration points
- Media service control surfaces

## Expected file families

- `config/homepage/` — Homepage YAML configs
  - `services.yaml`
  - `widgets.yaml`
  - `docker.yaml`
  - `settings.yaml`
- `config/homarr/` — Homarr configs (if deployed)
- `docker/docker-compose-dashboards.yml` — Dashboard stack deployment
- `docs/runbooks/HOMEPAGE_DEPLOYMENT.md` — Deployment and config guide
- `docs/runbooks/DASHBOARD_SERVICE_INTEGRATION.md` — Adding new services
- `config/traefik/` or `config/nginx/` — Reverse proxy configs
- `config/authelia/` — Authentication layer configs (if used)
- `.env.dashboards` — Environment variables and secrets

## Dependencies

- Docker and Docker Compose (infrastructure)
- Reverse proxy infrastructure (Traefik, Nginx Proxy Manager, or Caddy)
- Authentication layer (Authelia, OAuth provider, or VPN)
- `RM-OPS-004` — Docker monitoring and management
- `RM-OPS-005` — Telemetry and monitoring infrastructure
- docker-socket-proxy for secure Docker socket access

## Risks and issues

### Technical risks
- **Homepage auth gap:** Homepage has no built-in authentication, so reverse proxy layer is mandatory
  - **Mitigation:** Deployment runbook makes reverse proxy + auth a hard requirement; include validation checks
- **Docker socket security:** Direct Docker socket access is a major security risk
  - **Mitigation:** Mandatory docker-socket-proxy with minimal read-only permissions
- **API key sprawl:** Many widgets require service API keys that need secure management
  - **Mitigation:** Use .env.dashboards with gitignore, document secret management patterns
- **Config drift:** YAML configs can drift from deployed state
  - **Mitigation:** All configs in version control, restart required for changes creates checkpoint
- **Widget overload:** Too many widgets can impact performance
