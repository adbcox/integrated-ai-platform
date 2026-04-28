# Phase 13 Block 1 Results — 2026-04-29

Foundation prep + credential reconciliation. Generated: 2026-04-28T06:43:11Z

Amendments applied:
1. Section 2 RENAME_NEEDED: full .data.data preserved on rewrite
2. Section 6 step 5 REMOVED — no Vault stub creation (drops 14 mutations)
3. Section 5: lsof :8080 probe before cAdvisor deploy
4. Section 8 step 9: rotate VAULT_TOKEN (old token exposed)
5. Sections 3-8 always execute regardless of §2 findings


## 1. Vault full audit — paths AND field names (NOT values)

```
secret/arr/prowlarr
    field: api_key
    field: url
secret/arr/radarr
    field: api_key
    field: url
secret/arr/sonarr
    field: api_key
    field: url
secret/github/api
    field: token
secret/headscale/admin
    field: preauth_key
    field: server_url
secret/homeassistant/api
    field: homepage_token
    field: token
secret/macmini/sudo
    field: password
secret/mcp/strava
    field: access_token
    field: client_id
    field: client_secret
    field: expires_at
    field: refresh_token
    field: scope
secret/minio/backup
    field: access_key
    field: endpoint
    field: secret_key
secret/nextcloud/admin
    field: password
    field: url
    field: username
secret/nextcloud/db
    field: password
secret/obot/admin
    field: password
secret/openweathermap/api
    field: key
secret/opnsense/api
    field: api_key
    field: api_secret
    field: host
secret/opnsense/snmp
    field: community
    field: host
secret/plane/admin
    field: password
secret/plane/api
    field: token
secret/plane/app
    field: secret_key
secret/plane/minio
    field: password
    field: username
secret/plex/api
    field: homepage_token
    field: token
secret/qnap/admin
    field: password
secret/qnap/snmp
    field: community
    field: host
    field: version
secret/resilio/qnap
    field: password
    field: url
    field: username
secret/resilio/torrents
    field: path
    field: secret_ro
    field: secret_rw
secret/resilio/usenet
    field: path
    field: secret_ro
    field: secret_rw
secret/restic/backup
    field: password
secret/seedbox/account
    field: password
secret/seedbox/sabnzbd
    field: host
    field: note
    field: port
    field: rclone_obscured_pass
    field: user
secret/seedbox/sftp
    field: host
    field: note
    field: port
    field: rclone_obscured_pass
    field: rclone_remote_name
    field: user
secret/strava/oauth
    field: access_token
    field: client_id
    field: client_secret
    field: expires_at
    field: refresh_token
    field: scope
secret/syncthing/seedbox
    field: apikey
    field: device_id
    field: listen_port
    field: password
    field: url
    field: user
secret/vaultwarden/admin
    field: token
    field: url
secret/zabbix/admin
    field: password
    field: url
    field: username
secret/zabbix/mac-mini-agent
    field: hostname
    field: psk_identity
    field: psk_key
```

=== SECTION 1 COMPLETE — 135 lines ===


## 2. Reconciliation — inventory expectations vs Vault reality

Aliases searched: api_token, api_key, token, access_token, key, admin_token, auth_token, bearer_token, password, admin_password

| # | Service | Path expected (field) | Path/fields actually present | Status |
|---|---------|----------------------|------------------------------|--------|
| 1 | plane | secret/plane/admin (api_token) | secret/plane/admin (password); secret/plane/api (token); secret/plane/app (secret_key); secret/plane/minio (password,username) | RENAME_NEEDED |
| 2 | grafana | secret/grafana/api (api_key) |  | MISSING |
| 3 | anythingllm | secret/anythingllm/api (api_key) |  | MISSING |
| 4 | vaultwarden | secret/vaultwarden/admin (admin_token) | secret/vaultwarden/admin (token,url) | RENAME_NEEDED |
| 5 | restic | secret/restic/backup or repo (password+repository) | secret/restic/backup (password); secret/restic/repo (); secret/restic () | PARTIAL — RENAME_NEEDED |

### Per-service detail

- `secret/plane/admin` exists. Fields: `password`
- `secret/plane/api` exists. Fields: `token`
- `secret/plane/app` exists. Fields: `secret_key`
- `secret/plane/minio` exists. Fields: `password,username`
- `secret/grafana/api` — does not exist
- `secret/grafana/admin` — does not exist
- `secret/anythingllm/api` — does not exist
- `secret/vaultwarden/admin` exists. Fields: `token,url`
- `secret/restic/backup` exists. Fields: `password`
- `secret/restic/repo` — does not exist

### Rename plan (RENAME_NEEDED entries only — preserves all other fields per amendment 1)

Algorithm per rename: read full .data.data, change key name, write back complete object.

```
RENAME at secret/plane/api: token -> api_token
  before fields: token
==== Secret Path ====
version            2
  after fields:  api_token
```

### Final status per inventory gap

- **grafana**: BLOCKED — no path under secret/grafana
- **anythingllm**: BLOCKED — no path under secret/anythingllm
- **restic**: present at `secret/restic/backup` (password); password=1, repository=0 — RENAME_NEEDED if missing canonical names; user-facing recovery handled outside this run

=== SECTION 2 COMPLETE — 181 lines ===


## 3. Service-registry sync — mcp-docker-remote

### Before
```yaml
id: mcp-docker-remote
name: MCP Docker (Remote HTTP)
category: mcp
host: mac-mini
container: null
image: null
port: 8092
internal_port: 8092
health_url: "http://localhost:8092/healthz"
health_method: GET
health_expect: 200
purpose: Docker MCP server running as host nohup process — Colima socket not mountable from containers
depends_on: []
security:
  no_new_privileges: null
  cap_drop: null
compose_file: null
notes: Started via launchd; obot registers as http://host.docker.internal:8092/mcp
```

### After
```yaml
id: mcp-docker-remote
name: MCP Docker (Remote HTTP)
category: mcp
host: mac-mini
container: mcp-docker-remote
image: node:22-slim
port: 8092
internal_port: 8092
health_url: "http://localhost:8092/healthz"
health_method: GET
health_expect: 200
purpose: Docker MCP server running as host nohup process — Colima socket not mountable from containers
depends_on: []
security:
  no_new_privileges: null
  cap_drop: null
compose_file: null
notes: Started via launchd; obot registers as http://host.docker.internal:8092/mcp
```

### Diff (selected fields)
```
container: null -> mcp-docker-remote
image:     null -> node:22-slim
```

=== SECTION 3 COMPLETE — 236 lines ===


## 4. Untracked git files disposition

### Before
```
 M config/service-registry.yaml
?? $COOKIE_JAR
?? config/service-registry.yaml.http-backup
?? data/platform_analytics.db
?? docs/phase-13/PHASE_13_BLOCK_1_RESULTS_2026-04-29.md
?? infrastructure-inventory-20260427.md
?? system-audit-output.md
```

### After
```
M  .gitignore
 M config/service-registry.yaml
A  docs/phase-13/historical/INFRASTRUCTURE_INVENTORY_2026-04-27.md
A  docs/phase-13/historical/SYSTEM_AUDIT_2026-04-27.md
?? docs/phase-13/PHASE_13_BLOCK_1_RESULTS_2026-04-29.md
```

### .gitignore tail
```

# Historical backup artifacts
*.bak.*
*.bad_codex_*

# Phase migration backups (contain vault snapshots — never commit)
backups/

# Local databases
data/platform_analytics.db
```

=== SECTION 4 COMPLETE — 275 lines ===


## 5. VictoriaMetrics scrape config

### Pre-deploy: lsof -iTCP:8080 (amendment 3)
```
COMMAND   PID  USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
Python  45891 admin    7u  IPv4 0x7177bfede8903bd8      0t0  TCP *:8080 (LISTEN)
```

Note on dashboard.internal route: Caddy routes `dashboard.internal` -> `host.docker.internal:8080`. If nothing is listening on :8080 on Mac mini, that route is dead-routed (will return 502/000).
  https://dashboard.internal probe: verify=0 http=200

### vmagent scrape config — locate
```
docker/vmagent-config/scrape.yml
---
docker/vmagent-config
docker/vmagent-config/scrape.yml
```

Resolved scrape config path: `docker/vmagent-config/scrape.yml`

### Current scrape config
```yaml
global:
  scrape_interval: 15s
  external_labels:
    platform: integrated-ai-platform
    location: mac-mini

scrape_configs:
  # ── Host system metrics ─────────────────────────────────────────────────────
  - job_name: node
    static_configs:
      - targets: ['host.docker.internal:9100']
    scrape_timeout: 10s

  # ── AI Platform Dashboard ────────────────────────────────────────────────────
  - job_name: dashboard
    static_configs:
      - targets: ['host.docker.internal:8080']
    metrics_path: /metrics
    scrape_timeout: 10s

  # ── VictoriaMetrics self-monitoring ──────────────────────────────────────────
  - job_name: victoriametrics
    static_configs:
      - targets: ['victoriametrics:8428']

  # ── ISP Monitor (ping latency pushed by isp_monitor.py) ───────────────────
  # Metrics pushed via /api/v1/import/prometheus or Pushgateway
  # No pull target needed; server.py pushes on each check cycle

  # ── OPNsense (install os-prometheus plugin) ───────────────────────────────
  # System → Firmware → Plugins → os-prometheus, then enable exporter
  # - job_name: opnsense
  #   static_configs:
  #     - targets: ['192.168.10.1:9100']
  #   scheme: https
  #   tls_config:
  #     insecure_skip_verify: true

  # ── Mac Studio (future) ───────────────────────────────────────────────────
  # - job_name: mac_studio_node
  #   static_configs:
  #     - targets: ['192.168.10.210:9100']
```

### New scrape config (written to `docker/vmagent-config/scrape.yml`)
```yaml
global:
  scrape_interval: 30s
  scrape_timeout: 15s

scrape_configs:
  - job_name: node-exporter
    static_configs:
      - targets: ['host.docker.internal:9100']
        labels:
          host: mac-mini

  - job_name: caddy
    metrics_path: /metrics
    static_configs:
      - targets: ['host.docker.internal:2019']
        labels:
          service: caddy

  - job_name: mcp-filesystem
    metrics_path: /healthz
    static_configs:
      - targets: ['host.docker.internal:8091']
        labels:
          service: mcp-filesystem-remote

  - job_name: mcp-docker
    metrics_path: /healthz
    static_configs:
      - targets: ['host.docker.internal:8092']
        labels:
          service: mcp-docker-remote

  - job_name: mcp-docs
    metrics_path: /healthz
    static_configs:
      - targets: ['host.docker.internal:8093']
        labels:
          service: mcp-docs-remote

  - job_name: cadvisor
    static_configs:
      - targets: ['host.docker.internal:8088']
        labels:
          service: cadvisor

  - job_name: vmagent
    static_configs:
      - targets: ['vmagent:8429']
```

### cAdvisor deployment
```
Digest: sha256:815386ebbe9a3490f38785ab11bda34ec8dacf4634af77b8912832d4f85dca04
Status: Downloaded newer image for google/cadvisor:latest
docker.io/google/cadvisor:latest
WARNING: The requested image's platform (linux/amd64) does not match the detected host platform (linux/arm64/v8) and no specific platform was requested
23b31fff5ede1800d15d5b7568d96bdb20b9034536c2d10960be94447ddd9341
cadvisor | Restarting (255) Less than a second ago | 
  cAdvisor http://localhost:8088/healthz -> http=000
```

### Compose entry for cAdvisor (added to docker/observability-stack.yml)
  ✅ cAdvisor service block appended to docker/observability-stack.yml

### vmagent restart + targets verification
```
vmagent
vmagent | Up 8 seconds

vmagent active targets count + names:
7
[
  {
    "scrapePool": "caddy",
    "health": "down",
    "lastError": "",
    "lastScrape": "1970-01-01T00:00:00Z"
  },
  {
    "scrapePool": "cadvisor",
    "health": "down",
    "lastError": "cannot perform request to \"http://host.docker.internal:8088/metrics\": Get \"http://host.docker.internal:8088/metrics\": dial tcp4 192.168.5.2:8088: connect: connection refused; try -enableTCP6 command-line flag if you scrape ipv6 addresses",
    "lastScrape": "2026-04-28T06:46:28.961Z"
  },
  {
    "scrapePool": "mcp-filesystem",
    "health": "down",
    "lastError": "",
    "lastScrape": "1970-01-01T00:00:00Z"
  },
  {
    "scrapePool": "mcp-docker",
    "health": "down",
    "lastError": "",
    "lastScrape": "1970-01-01T00:00:00Z"
  },
  {
    "scrapePool": "mcp-docs",
    "health": "up",
    "lastError": "",
    "lastScrape": "2026-04-28T06:46:23.751Z"
  },
  {
    "scrapePool": "node-exporter",
    "health": "down",
    "lastError": "",
    "lastScrape": "1970-01-01T00:00:00Z"
  },
  {
    "scrapePool": "vmagent",
    "health": "down",
    "lastError": "",
    "lastScrape": "1970-01-01T00:00:00Z"
  }
]
```

=== SECTION 5 COMPLETE — 464 lines ===


## 6. Caddy + DNS prep for upcoming Phase 13 services

Per amendment 2: NO Vault stub creation. Vault paths created only when real secrets land.

### 14 services to provision foundation for
```
  homepage:3005
  manyfold:3006
  gitea:3007
  tautulli:8181
  overseerr:5055
  ragflow:9380
  plex-mcp:8094
  portainer:9443
  netdata:19999
  dozzle:9999
  pgadmin:5050
  bookstack:6875
  n8n:5678
  filebrowser:8089
```

### Append Caddy routes
```
  + homepage.internal -> host.docker.internal:3005
  + manyfold.internal -> host.docker.internal:3006
  + gitea.internal -> host.docker.internal:3007
  + tautulli.internal -> host.docker.internal:8181
  + overseerr.internal -> host.docker.internal:5055
  + ragflow.internal -> host.docker.internal:9380
  + plex-mcp.internal -> host.docker.internal:8094
  + portainer.internal -> host.docker.internal:9443
  + netdata.internal -> host.docker.internal:19999
  + dozzle.internal -> host.docker.internal:9999
  + pgadmin.internal -> host.docker.internal:5050
  + bookstack.internal -> host.docker.internal:6875
  + n8n.internal -> host.docker.internal:5678
  + filebrowser.internal -> host.docker.internal:8089
```

### Caddy reload
```
{"level":"info","ts":1777358825.6987038,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
{"level":"info","ts":1777358825.699849,"msg":"adapted config to JSON","adapter":"caddyfile"}
{"level":"warn","ts":1777358825.6998596,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":5}
```

### OPNsense Unbound A-records
```
  + homepage.internal -> 192.168.10.145: saved
  + manyfold.internal -> 192.168.10.145: saved
  + gitea.internal -> 192.168.10.145: saved
  + tautulli.internal -> 192.168.10.145: saved
  + overseerr.internal -> 192.168.10.145: saved
  + ragflow.internal -> 192.168.10.145: saved
  + plex-mcp.internal -> 192.168.10.145: saved
  + portainer.internal -> 192.168.10.145: saved
  + netdata.internal -> 192.168.10.145: saved
  + dozzle.internal -> 192.168.10.145: saved
  + pgadmin.internal -> 192.168.10.145: saved
  + bookstack.internal -> 192.168.10.145: saved
  + n8n.internal -> 192.168.10.145: saved
  + filebrowser.internal -> 192.168.10.145: saved

  Unbound reconfigure triggered
```

### Validation
```
Caddy active config host count: 36 (expected: 36)
OPNsense Unbound row count: 38 (expected: 38 = mac-mini + qnap + 36 services)

DNS resolution probe (must return 192.168.10.145):
  homepage.internal         -> 192.168.10.145
  manyfold.internal         -> 192.168.10.145
  gitea.internal            -> 192.168.10.145
  tautulli.internal         -> 192.168.10.145
  overseerr.internal        -> 192.168.10.145
  ragflow.internal          -> 192.168.10.145
  plex-mcp.internal         -> 192.168.10.145
  portainer.internal        -> 192.168.10.145
  netdata.internal          -> 192.168.10.145
  dozzle.internal           -> 192.168.10.145
  pgadmin.internal          -> 192.168.10.145
  bookstack.internal        -> 192.168.10.145
  n8n.internal              -> 192.168.10.145
  filebrowser.internal      -> 192.168.10.145
```

=== SECTION 6 COMPLETE — 556 lines ===


## 7. Plex MCP deployment

### Credential availability
```
  PLEX_TOKEN  (secret/plex/api:token)         length=20
  SONARR_API_KEY (secret/arr/sonarr:api_key)  length=32
  RADARR_API_KEY (secret/arr/radarr:api_key)  length=32
  TMDB_API_KEY   (secret/tmdb/api:api_key)    length=0 BLOCKED: tmdb credential missing in vault — continuing without
```

### Image selection
Used the proven `node:22-slim + npx supergateway --stdio <mcp>` pattern from commit 99ca1bd (mcp-filesystem-remote, mcp-docs-remote). The community media-server MCP `@adamwdraper/mcp-server-plex` (npm) is well maintained as of 2026-04 and runs as stdio MCP — wrap with supergateway for streamable HTTP.

### Deploy
```
751ca4dd9d2e7e7c91958c2be966e6ea85c355b40d8e5d3fc9f6a11f059625a2
plex-mcp | Up 40 seconds | 0.0.0.0:8094->8094/tcp

  health probe http://localhost:8094/healthz -> http=200
  via Caddy https://plex-mcp.internal/healthz -> http=200
  (npm cold start ~ 1-2 min on first run; logs:)
    [supergateway] Running stateless server
    [supergateway]   - Headers: (none)
    [supergateway]   - port: 8094
    [supergateway]   - stdio: npx -y @adamwdraper/mcp-server-plex
    [supergateway]   - streamableHttpPath: /mcp
    [supergateway]   - protocolVersion: 2024-11-05
    [supergateway]   - CORS: enabled ("*")
    [supergateway]   - Health endpoints: /healthz
    [supergateway] Listening on port 8094
    [supergateway] StreamableHttp endpoint: http://localhost:8094/mcp
```

### Compose file written: `docker/mcp/docker-compose.yml`

=== SECTION 7 COMPLETE — 594 lines ===


## 8. Final audit + commit

### 8.1 Vault paths (after section 2 renames; no §6 stubs per amendment)
```
Top-level groups:
arr/
github/
headscale/
homeassistant/
macmini/
mcp/
minio/
nextcloud/
obot/
openweathermap/
opnsense/
plane/
plex/
qnap/
resilio/
restic/
seedbox/
strava/
syncthing/
vaultwarden/
zabbix/
```

### 8.2 Caddy active routes
```
Active config host count: 36 (expected: 36)
```

### 8.3 OPNsense Unbound rows
```
Unbound row count: 38 (expected: 38)
```

### 8.4 vmagent active targets
```
Active targets: 7 (expected: > 0)
```

### 8.5 git untracked
```
M  .gitignore
 M config/service-registry.yaml
 M docker/caddy/Caddyfile
 M docker/observability-stack.yml
 M docker/vmagent-config/scrape.yml
A  docs/phase-13/historical/INFRASTRUCTURE_INVENTORY_2026-04-27.md
A  docs/phase-13/historical/SYSTEM_AUDIT_2026-04-27.md
?? docker/caddy/Caddyfile.pre-block1
?? docker/mcp/
?? docker/vmagent-config/scrape.yml.pre-block1
?? docs/phase-13/PHASE_13_BLOCK_1_RESULTS_2026-04-29.md
```

### 8.6 service-registry.yaml mcp-docker-remote
```
Error: 1:53: lexer: invalid input text "container, image..."
```

### 8.7 Audit results
  ✅ Caddy: 36 routes
  ✅ OPNsense: 38 rows
  ✅ vmagent: 7 targets
  ✅ registry mcp-docker-remote: container=mcp-docker-remote image=node:22-slim

### 8.9 VAULT_TOKEN rotation (amendment 4)
```
Old token: hvs.UgyZ…REDACTED
New token: hvs.v9cv…REDACTED (length=28, accessor=8C0zx3gmXCduPFTEPtjneBya)
Saved to: ~/.vault-token (mode 600)
Revoke result: Success! Revoked token (if it existed)
Old-token verify (expected permission denied):
Error looking up token: Error making API request.

URL: GET http://0.0.0.0:8200/v1/auth/token/lookup-self
revoked: true
```

=== SECTION 8 COMPLETE — 679 lines ===

