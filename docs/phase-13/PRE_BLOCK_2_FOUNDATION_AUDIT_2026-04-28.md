# Pre-Block-2 Foundation Audit

**Date**: 2026-04-28
**Mode**: Read-only investigation. No mutations.
**Purpose**: Establish actual baseline before Block 2 control-center +
mobile-parity work begins. Surface gaps and architectural surprises for
master review before deployment phases start.

---

## A.1 — Homepage state on Mac Mini

**Result**: NOT DEPLOYED.

```
docker ps -a | grep homepage  →  (empty)
```

There is **no `homepage` container** of any kind on the Mac Mini.
Existing `homarr` container (separate dashboarding product) is unrelated.

A `homepage.internal` route is *already declared* in the Caddyfile
pointing at `host.docker.internal:3005`. Hitting it returns HTTP 502
(no backend). The route is forward-leaning detritus, not blocking.

**Implication**: Phase 2 deploys Homepage from scratch. The :3005 port
declared in the route matches the spec; no port collision concern (Open
WebUI is on :3002, not :3000 as the prompt's parenthetical suggested).

**Mac Mini bandwidth**: 42 containers running, 0 restarting, all healthy.
Adding Homepage + sidecar is safe.

---

## A.2 — Grafana state

**Container**: `grafana-obs` (Grafana 10.4.2). Running 20 hours, healthy.
Compose source: `docker/observability-stack.yml`.
Provisioning bind-mount: `docker/grafana-provisioning/` →
`/etc/grafana/provisioning` (rw).

### Plugins

Currently installed:
```
alexanderzobnin-zabbix-app @ 4.4.5
```

**Required by spec, GAPS (5/5 missing)**:

| Plugin | Purpose | Status |
|---|---|---|
| `yesoreyeram-infinity-datasource` | REST API queries (Sonarr/Radarr/Plex/Ollama) | MISSING |
| `marcusolsson-json-datasource` | JSON parsing | MISSING |
| `hamedkarbasi93-nodegraph-panel` | Network topology | MISSING |
| `grafana-image-renderer` | Panel screenshots | MISSING |
| `natel-discrete-panel` | Event timeline | MISSING |

`GF_INSTALL_PLUGINS` not set anywhere in the active compose. Install
path: edit `docker/observability-stack.yml`, add env var, recreate.

### Data sources

Configured (via `/api/datasources`):

| Name | Type | URL | Status |
|---|---|---|---|
| VictoriaMetrics | prometheus | http://victoriametrics:8428 | working, default |

**Required by spec, GAPS**:

- Infinity datasource (Sonarr, Radarr, Prowlarr, Plex, Ollama) — MISSING
- PostgreSQL datasource for Plane (`secret/plane/db`) — MISSING
- (Docker metrics: already covered via cAdvisor → VictoriaMetrics, so no
  separate Docker datasource needed — matches spec preference for not
  exposing socket directly)

Provisioning directory has only `victoriametrics.yaml` (10 lines). All
other datasource provisioning files must be added in P3.2/P3.3.

### Dashboards

Provisioned (in repo):
- `platform-overview.json`
- `phase7-infrastructure.json`

**Required by spec — 6 target dashboards**:

| # | Name | Status |
|---|---|---|
| 1 | Overview | partial (`platform-overview.json` exists; needs spec-aligned redesign) |
| 2 | Network Topology | MISSING — depends on Topology API (Phase 5) |
| 3 | Media Automation | MISSING |
| 4 | AI & Coding | MISSING |
| 5 | Infrastructure | partial (`phase7-infrastructure.json` exists) |
| 6 | Media Enhancement | MISSING |

**Decision surface**: do Phase 4 dashboards (1) replace `platform-overview.json`
or (2) build alongside it as `overview-v2`? Recommend replace — single
source of truth, but preserve old JSON in `docs/phase-13/` for diffing.

---

## A.3 — Service registry currency

**Total services**: 61 entries, 39 with containers, 22 host/null.

### 3 untracked running containers

| Container | Notes |
|---|---|
| `seal-vault` | Vault auto-unseal Transit sidecar (deployed H1 §4). Should be in registry under `category: platform`. |
| `cadvisor` | Container resource metrics → VictoriaMetrics. Privileged per doctrine exception. Should be in registry under `category: observability`. |
| `plex-mcp` | Plex MCP server. Not in registry. Should be `category: mcp`. |

All three pre-existed before Block 2. Registry-update task added to P2.5
or absorbed into P9.4 closure work.

### 26 services with empty `depends_on`

Concrete list (auto-discovered):

```
litellm-gateway, ollama, mcpo-proxy, iap-dashboard, vault, plane-db,
plane-minio, homarr, victoriametrics, uptime-kuma, node-exporter,
prowlarr, sportarr, plex, homeassistant-container, homeassistant-physical,
plane-redis, opnsense, zabbix-postgres, mcp-filesystem-remote,
mcp-docker-remote, mcp-docs-remote, caddy, headscale, vaultwarden,
nextcloud-db
```

Most are leaf services or have implicit dependencies. Concrete
deps to add (not exhaustive):
- `litellm-gateway` → `ollama` (host process, but logical dep)
- `vmagent` → `victoriametrics`
- `caddy` → all services it proxies (probably impractical to enumerate;
  `depends_on` is an availability hint, not a hard order; reasonable to
  leave caddy with empty deps)
- `vault` → `seal-vault` (auto-unseal)

Recommend treating depends_on population as background work in P2.5,
P3.5, P4.7, P9.4 rather than a discrete sub-phase — populate as services
are touched.

### MCP server actual list

Running MCPs (7 containers):

| Container | Likely category | Registered? |
|---|---|---|
| `mcp-filesystem-remote` | mcp | ✅ |
| `mcp-docker-remote` | mcp | ✅ |
| `mcp-docs-remote` | mcp | ✅ |
| `mcpo-proxy` | ai (gateway) | ✅ (under ai) |
| `plex-mcp` | mcp | ❌ MISSING |
| `sms1obot-mcp-server` | ai (obot tool) | ✅ (as `obot-mcp-server`) |
| `sms1obot-mcp-server-shim` | ai (obot tool) | ✅ (as `obot-mcp-shim`) |

**The spec says "10 MCP servers"** — actual count is 7 running. The
discrepancy is real: the registry's 14 `mcp-shim` entries are
*configuration-level* obot shim definitions, not running containers.
Per Block 2 spec language, Dashboard 4 (AI & Coding) "MCP server health
(10 servers per actual registry)" should be re-interpreted as **MCP
server health (actual running count, currently 7)** — the dashboard
queries running containers, not aspirational entries.

**Surface decision**: confirm Dashboard 4 enumerates the 7 running MCP
containers (treating `mcpo-proxy`/`obot-shim-*` separately or together
per design preference).

---

## A.4 — Caddy + DNS state

Caddy 2-alpine, healthy. Currently serves **36 `.internal` hosts**.

### Routes already declared but pointing at non-running services

| Host | Backend | HTTP probe | Backing service exists? |
|---|---|---|---|
| `homepage.internal` | :3005 | 502 | NO — to be deployed in Phase 2 |
| `topology.internal` | (no route) | 000 (no route) | NO — to be deployed in Phase 5 |
| `manyfold.internal` | unknown | 502 | NO compose found |
| `gitea.internal` | unknown | 502 | NO compose found |
| `tautulli.internal` | unknown | 502 | NO compose found |
| `overseerr.internal` | unknown | 502 | NO compose found |
| `ragflow.internal` | unknown | 502 | NO compose found |
| `portainer.internal` | unknown | 502 | NO compose found |
| `netdata.internal` | unknown | 502 | NO compose found |
| `dozzle.internal` | unknown | 502 | NO compose found |
| `pgadmin.internal` | unknown | 502 | NO compose found |
| `bookstack.internal` | unknown | 502 | NO compose found |
| `n8n.internal` | unknown | 502 | NO compose found |
| `filebrowser.internal` | unknown | 502 | NO compose found |
| `mcp-docker.internal` | unknown | 404 | partially (container running but route may need updating) |
| `mcp-docs.internal` | unknown | 404 | partially (same) |

**Architectural surprise — surface to user**: the Caddyfile contains 12
forward-looking `.internal` routes for services that have **no compose
files** anywhere on the platform. They are returning 502 today.
Explanation candidates:

1. Aspirational routes added by a prior session before the services
   were deployed; never cleaned up
2. Services deployed elsewhere (out-of-repo, on a different host) and
   the Caddyfile has stale local proxies

Either way, these 12 routes pollute the platform's surface. **Recommend
P9.4 closure work**: prune unused Caddy routes (separate, focused PR)
unless user has plans to deploy these services in the near term. Not
blocking Block 2.

### Per-site logs

Caddyfile has **0** `log {` directives. Volume `caddy-logs` exists.
Pre-block-2 fix-pass infrastructure (volume) is in place; Caddyfile
syntax was reverted after a bulk-sed misadventure. P4.7 will properly
add per-site logs.

### Routes needing addition for Block 2

| Host | For | Phase |
|---|---|---|
| `homepage.internal` | already declared (:3005) — verify backend works | P2.4 |
| `topology.internal` | for Topology API service | P5.1 |

---

## A.5 — MacBook Pro M5 current state

**Cannot be probed from this session.** Mac Mini cannot reach the
MacBook over the network from here without SSH config (none documented).

**Surface to user — please run on MacBook and report back**:

```bash
# Hardware
sysctl machdep.cpu.brand_string hw.memsize | awk -F': ' '{print $1": "$2}'

# Tools
sw_vers | head -2
which ollama && ollama --version
which docker && docker version --format 'client={{.Client.Version}} server={{.Server.Version}}' 2>/dev/null
which tailscale
which claude && claude --version
brew list tailscale 2>/dev/null
brew list ollama 2>/dev/null

# Models
ollama list 2>/dev/null

# Disk
df -h /Users/admin | tail -1

# Power
pmset -g batt | head -2
```

Items needed for plan refinement:
- Confirm M5 chip + 32 GB RAM
- Whether Ollama already installed; which models pulled
- Docker Desktop installed?
- Tailscale CLI installed?
- Claude Code installed?
- Free disk on `/Users/<username>`
- Battery vs AC at audit time

---

## A.6 — Headscale infrastructure

**Container**: `headscale:latest`, healthy, 20 hours uptime.

**Endpoint**:
- Container port `8080` → host port `8082` (HTTP, fronted by Caddy at
  `headscale.internal`)
- Container port `50443` → host port `50443` (gRPC/TLS direct)
- Caddy reverse proxy: `https://headscale.internal/` → `:8082`

**State**:
- 1 user: `admin` (created 2026-04-27)
- 0 nodes registered (Mac Mini is **not** a node in its own VPN — that
  matches expectation; Mac Mini IS the control plane, not a tailnet
  member)

**Pre-auth key generation procedure** (verified via `--help`):

```bash
docker exec headscale headscale preauthkeys create \
  --user 1 \
  --reusable \
  --expiration 24h \
  --output json
```

Returns JSON with `key` field. Single-use, time-limited; reusable flag
for multi-device or development.

**Server URL for `tailscale up --login-server`**:
- For LAN access: `http://192.168.10.145:8082` or
  `https://headscale.internal/` (Caddy + internal-CA TLS)
- For non-LAN devices reaching Mac Mini: depends on network topology
  the user has configured. Likely needs port-forward on home router or
  the public-internet form of the Headscale endpoint. **Surface to user
  for Phase 8.**

---

## A.7 — Threadripper / Mac Studio status

**Registry**: no entries for `threadripper`, `mac-studio`, or `m3-ultra`.
Currently the registry has these non-mac-mini hosts:
- `qnap` (plex)
- `ha-device` (homeassistant-physical)
- `opnsense`

**For Block 2 dashboards**: P5.1 Topology API must include synthesized
nodes for Threadripper and Mac Studio with `status: "offline"` so they
appear in the topology graph as future/intended nodes, not as
unmonitored gaps. P4.5 (Dashboard 6: Media Enhancement, ComfyUI/Video2X)
will show "currently offline" placeholder text.

Recommend adding to registry as host-only entries in P5.1 work:

```yaml
- id: threadripper
  host: threadripper
  status_override: offline
  notes: Future Linux node; hardware issue at audit; canonical pattern
    will apply when online.
- id: mac-studio
  host: mac-studio-m3-ultra
  status_override: offline
  notes: Future ML/inference node; not yet acquired.
```

The `status_override` key is a new schema field; document in registry
header or in `docs/phase-13/PHASE_13_5_LOCAL_ORCHESTRATION_RESULTS_2026-04-28.md`
(actually: phase-2 closure doc, since 13.5 is closed).

---

## Cross-cutting findings & architectural notes

### F1 — Pre-block-2 deferred items still pending

From the readiness audit / pre-block-2 fix pass, three items were noted
deferred:

| Item | Status | Where it lands in Block 2 |
|---|---|---|
| zabbix-prometheus-exporter | not deployed | P3.4 |
| Caddy per-site logs (volume in place; Caddyfile reverted) | volume exists, syntax pending | P4.7 |
| Mac Mini Zabbix host registration | not registered | P6.1 |

All three are explicit tasks in this prompt — no surprise.

### F2 — `OPNsense API` for Dashboard 5

P4.4 mentions "OPNsense if API available". OPNsense entry exists in
registry (host=opnsense). API availability not verified in this audit.
Recommend P4.4 attempts the API; if unauthenticated metrics endpoint
unavailable, omit panel and document in Block 2 closure as a
known-limitation.

### F3 — Open-WebUI activity metrics for Dashboard 4

The spec calls for "Open WebUI activity and total messages". Open-WebUI
exposes `/api/v1/users/active` and similar but those require admin
session auth, not API keys. **Likely requires per-session reverse-proxy
work** or accepting that this panel shows only "container up + memory
usage" rather than message counts. Surface to user before P4.3 if Phase
4 actually needs it.

### F4 — Plane PostgreSQL access role

P3.3 prefers "read-only role" for the Plane datasource. The Plane stack
has only the application's superuser role today (per H1 §6 BP2 work).
P3.3 will document as known privilege issue and use read-only queries
from the superuser, OR create a read-only role ad-hoc. Recommend the
latter only if P3.3 scope is small; otherwise document and use
SELECT-only queries via dashboard panel guards.

### F5 — `topology.internal` route not yet in Caddyfile

Currently 000 (no route). Phase 5 must add this route in P5.1.

### F6 — Audit log path for Block 2 verification

H1 audit log is at `/vault/logs/audit.log` inside the vault-server
container. P2.6, P3.5, etc. should verify each new AppRole appears in
audit log via `tail -200 | jq` filtering on the new role's path.

### F7 — Visual-polish boundary

Multiple phases (P2.3 dark mode, P4.x panel layouts) include "sensible
default" choices. Per the prompt, visual decisions beyond defaults are
deferred. Concrete "sensible defaults" interpretation:

- Homepage: dark mode, default service-card layout, no custom CSS
- Grafana: default Grafana 10.4 dark theme, default panel sizes (8x8 or
  12x8 grid units), no `panels[].fieldConfig.overrides` beyond what the
  data type requires
- No custom Grafana CSS, no theme customization, no widget styling
  beyond plugin defaults

Anything beyond → STOP and surface.

---

## Scope refinement & gate impact

Based on this audit, no Block 2 phase is invalidated. Phase 1 finishes
clean here. Concrete phase deltas:

- **P2.3 (Homepage config)**: 6 service widgets needed; verify API keys
  available in current credential state (Sonarr, Radarr, Prowlarr, Plex,
  Grafana, Uptime Kuma). Phase 2 will gather/verify these; user should
  be ready to provide keys via stdin if they aren't already in Vault.
- **P3.1 (Grafana plugins)**: 5 plugins to install (all 5 missing).
- **P3.2 (Infinity datasources)**: 5 to provision (Sonarr/Radarr/Prowlarr/Plex/Ollama).
- **P4.1 (Dashboard 1)**: replace existing `platform-overview.json`,
  preserve copy in docs/phase-13/.
- **P4.5 (Dashboard 6)**: degraded-state placeholders for
  Threadripper/Mac Studio; ComfyUI/Video2X panels show offline notice.
- **P5.1 (Topology API)**: include synthesized Threadripper/Mac Studio
  offline nodes; add `topology.internal` route to Caddyfile.
- **P9.4 closure**: optionally prune 12 dead Caddy routes (separate
  decision).

Time estimate (18-22h) holds. No phase needs to be split.

---

## Surfaced decision points (await master review)

1. **MacBook Pro state inventory** — needed before P7 plan finalization.
   See A.5 command list above.
2. **Headscale public endpoint** — needed before P8.1 if MacBook will
   ever connect from outside the LAN.
3. **Dashboard 1 strategy** — replace `platform-overview.json` or build
   alongside?
4. **MCP server count for Dashboard 4** — 7 running vs the spec's "10";
   confirm dashboard targets the running roster.
5. **OPNsense API panel** for Dashboard 5 — accept best-effort with
   known-limitation fallback?
6. **Open-WebUI message-count metric** — if API requires admin session,
   accept reduced panel scope?
7. **Plane PostgreSQL read-only role** — create new role in P3.3 or use
   SELECT-only queries from existing superuser?
8. **Dead Caddy routes** (12) — prune in P9.4 or leave for separate
   cleanup pass?

Awaiting master review. Phase 2 deployment work will not begin until
these are answered.
