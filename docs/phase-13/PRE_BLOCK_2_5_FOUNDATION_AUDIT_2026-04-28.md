# Pre-Block 2.5 Foundation Audit

**Date:** 2026-04-28
**Branch:** `feat/block-2.5-control-plane`
**Author:** Claude Code (Phase 13 Block 2.5 Phase 1, read-only)
**Status:** PAUSE — awaiting user approval of architecture decisions before Phase 2

---

## 1. Scope and intent

Block 2.5 closes the control gap left by Block 2: operator can SEE
platform state via Homepage + Grafana + Topology API, but cannot ACT
on it from any web surface. SSH-and-CLI is the only current path for
container restart, manual backup trigger, credential rotation, queue
management, audit search, and similar operator actions.

Block 2.5 builds a hardened operator control plane web app on the
Mac Mini, deployed via the canonical Vault Agent sidecar pattern,
exposing scoped actions over an authenticated API and a frontend that
uses sensible defaults (visual polish deferred).

This document captures the foundation audit and surfaces architecture
decisions for user approval before Phase 2 begins.

---

## 2. Action surface inventory (A.1)

The actions an operator currently performs via SSH or CLI that this
control plane should expose. Each action is tagged with its proposed
permission tier (defined in §6).

### 2.1 Container actions
| Action | Tier | Notes |
|---|---|---|
| list (running + stopped, with status/image/uptime/mem/cpu) | T1 | from Docker socket proxy |
| inspect (full config + state JSON) | T1 | |
| logs (paginated + follow) | T1 | tail with byte/line limit |
| restart | T2 | |
| stop | T2 | |
| start | T2 | |
| exec | T3 | allowlisted commands per container label only |

### 2.2 Backup actions
| Action | Tier | Notes |
|---|---|---|
| list Restic snapshots | T1 | via control-plane AppRole reading `secret/restic/backup` |
| last-backup status (timestamp + result) | T1 | |
| trigger manual backup | T2 | execs `scripts/backup.sh` as subprocess via host launcher |
| restore-preview (dry run) | T3 | uses `restic restore --dry-run` |
| restore-execute | T4 | not exposed; CLI-only with explicit message in UI |

### 2.3 Credential actions
| Action | Tier | Notes |
|---|---|---|
| list KV paths (hash-only) | T1 | no value reads ever |
| rotation history (last N rotations across paths) | T1 | from a rotation-event log written by control-plane |
| rotate credential for named service | T3 | invokes per-service rotation script |
| read raw credential value | T4 | hard-coded refusal; doctrine violation |

### 2.4 Vault status
| Action | Tier | Notes |
|---|---|---|
| seal status, leader, version | T1 | `sys/seal-status`, `sys/health` |
| list policies | T1 | `sys/policies/acl` (names only) |
| list AppRoles | T1 | `auth/approle/role` |
| audit log search | T2 | reads `/vault/logs/audit.log` (mounted RO) |
| unseal, policy modify, approle modify | T4 | not exposed |

### 2.5 Service-specific actions (Sonarr / Radarr / Prowlarr)
| Action | Tier | Notes |
|---|---|---|
| Sonarr / Radarr queue list | T1 | `/api/v3/queue` |
| Sonarr / Radarr queue approve, blacklist, retry | T2 | `/api/v3/queue/{id}/...` |
| Sonarr / Radarr library refresh | T2 | `/api/v3/command` (RescanSeries / RescanMovie) |
| Prowlarr indexer health | T1 | `/api/v1/indexer/{id}/test` |
| Prowlarr "test all" | T2 | iterates all indexers |
| Plex active streams / recently added | — | already in Grafana; redundant — skip |

### 2.6 Audit + log search
| Action | Tier | Notes |
|---|---|---|
| Vault audit log search (timestamp / actor / op / path / outcome) | T2 | |
| Caddy access log search (site / time / status / path) | T1 | reads `/var/log/caddy/access.log` (mounted RO) |
| Container logs (with time + name filter) | T1 | proxied through Docker socket proxy |

### 2.7 Configuration diff
| Action | Tier | Notes |
|---|---|---|
| diff current rendered service config vs repo last-known-good | T1 | text diff of compose / Caddyfile / policy files |

### 2.8 Regression probe
| Action | Tier | Notes |
|---|---|---|
| trigger `docs/phase-13/h1-regression-probe.sh [gate-id]` | T3 | host-side execution; see §8.5 architectural concern |

### 2.9 Service registry browser
| Action | Tier | Notes |
|---|---|---|
| browse parsed `service-registry.yaml` | T1 | already exposed by topology-api at `/api/topology` — control-plane consumes that JSON, no parser duplication |

**Open question for user**: any actions you'd add, drop, or re-tier?

---

## 3. Authentication architecture (A.2)

Three viable paths from the prompt; my recommendation follows.

### Path 1 — Vaultwarden-backed login (username/password)
User logs in with Vaultwarden creds → control-plane validates against
Vaultwarden's Bitwarden-compatible Identity API
(`/identity/connect/token`) → JWT or session cookie issued.

**Concern**: Bitwarden auth flow is multi-step (PreLogin → key
derivation → Identity token grant). Implementing it as a relying
party is non-trivial and brittle to Vaultwarden version changes.

### Path 2 — Headscale tailnet identity
Request from a tailnet IP → user identified by reverse-DNS or
Headscale node lookup → no login. Off-tailnet rejected.

**Concern**: Caddy currently doesn't extract or forward tailnet
identity. Need to add an `@tailnet remote_ip 100.64.0.0/10` matcher
and a header pass-through at Caddy. Workable but binds to Headscale's
specific CGNAT range.

### Path 3 — Hybrid (RECOMMENDED)
- Tailnet IP gates the **outer** door — off-tailnet requests are
  rejected at Caddy with 403 before reaching control-plane.
- Tailnet identity is treated as Tier 1+2 authorization (read +
  safe actions).
- For Tier 3 actions (sensitive), control-plane requires an
  **Argon2-hashed operator password** stored in Vault at
  `secret/control-plane/operator` to be re-entered. Sliding window:
  Tier 3 escalation lasts 5 min, then re-auth required.

**Why this rather than Vaultwarden integration:** Vaultwarden's auth
API is not designed for relying-party use. Hashing a password in
Vault and validating it directly is simpler, fewer moving parts, and
keeps Vaultwarden out of the control-plane's hot path. Vaultwarden
remains the operator's password manager, but is not part of the
control-plane auth chain.

**Open question for user**: approve Path 3 with Vault-stored Argon2
password for Tier 3, OR insist on Vaultwarden integration (will add
implementation cost and a dependency on Vaultwarden uptime for
sensitive actions)?

---

## 4. Backend stack decision (A.3)

| Option | Pros | Cons |
|---|---|---|
| Python FastAPI + uvicorn | matches existing platform Python tooling; rich service-API integrations; pydantic validation; fast iteration | runtime dependency on Python image; cold start ~1s |
| Go (Gin or stdlib) | single binary; smaller container; faster cold start | less consistent with platform; slower iteration; reduced ecosystem fit |

**Recommendation: Python FastAPI + uvicorn** — single-operator scale
makes the perf delta irrelevant, and consistency with the rest of
the Python tooling on the platform (vault-agent helper scripts,
topology-api, observability tooling) wins.

**Stack pinned to**:
- python:3.12-slim base
- fastapi==0.115.x (pinned at compose-build time)
- uvicorn[standard]==0.30.x
- httpx for service-API calls
- jinja2 for templates
- pydantic v2 for request/response validation
- argon2-cffi for password hashing

---

## 5. Frontend stack decision (A.4)

| Option | Pros | Cons |
|---|---|---|
| HTMX + Tailwind + Jinja2 | server-rendered; minimal JS; one deploy artifact; matches operator-tool ethos | constrained interactions; modal patterns are HTMX-shaped |
| React + Vite | full SPA flexibility; component reuse | separate deploy; bigger dependency surface |
| SvelteKit | middle ground | another runtime / build system to maintain |

**Recommendation: HTMX + Tailwind + Jinja2** — operator tool, not
consumer product. Speed to working prototype, single deploy artifact
(FastAPI serves the frontend), easy maintenance, and the
follow-the-server pattern matches our action-tier model cleanly
(server enforces auth tier on every request; no client-side state to
go stale).

---

## 6. Permission scoping tiers (A.5)

| Tier | Scope | Auth requirement |
|---|---|---|
| **T1 — Read-only** | list, view, search, inspect, registry browse | tailnet identity (no login) |
| **T2 — Safe actions** | restart container, manual backup trigger, queue retry/blacklist, library refresh, audit log search | tailnet identity (no login) |
| **T3 — Sensitive actions** | credential rotation, container exec, regression probe trigger, restore-preview | tailnet + operator password re-auth (5-min sliding window) |
| **T4 — Forbidden via web** | Vault unseal, restore-execute, policy/approle modification, raw credential read | UI displays "Use CLI for this; see docs/runbooks/" |

**Tier-3 sliding-window mechanic**: control-plane stores a
`tier3_unlocked_until` timestamp in the session. A successful Tier 3
re-auth sets it to `now+5min`. Each Tier 3 action checks the
timestamp; if expired, the action returns 401 with a re-auth challenge
that the frontend surfaces as a modal.

**Audit log capture**: every action invocation (including failed
Tier 3 challenges) is written to a structured action log at
`/vault/secrets/control-plane-actions.log` (rotating JSON lines)
AND mirrors an entry into Vault's audit log via a no-op token
lookup on a control-plane-specific path (so the action shows up in
the existing audit search).

**Open question for user**: any tier reassignments? Specifically:
should "trigger manual backup" be T3 (since it consumes I/O on QNAP)
rather than T2?

---

## 7. Caddy + service-registry slot (A.6)

### 7.1 Caddy route
Append at end of `docker/caddy/Caddyfile`:

```
control.internal {
    import access_log

    @tailnet remote_ip 100.64.0.0/10
    handle @tailnet {
        reverse_proxy host.docker.internal:8086 {
            header_up X-Real-IP {remote_host}
            header_up X-Tailnet-Source "true"
        }
    }
    handle {
        respond "control-plane is tailnet-only" 403
    }
}
```

**Port note (P2.5 finding)**: original audit proposed 8094, but the
Caddyfile already routes `plex-mcp.internal → host.docker.internal:8094`
(a dead route per CLAUDE.md follow-up list). To avoid ambiguity,
control-plane switched to **port 8086** during P2.5 — clean, no
adjacent service, no Caddyfile collision. This is a port change only;
no downstream impact since no other service references control-plane.

DNS: add `control.internal → 192.168.10.145` to OPNsense Unbound.

### 7.2 service-registry entry
Append to `config/service-registry.yaml`:

```yaml
  - id: control-plane
    name: Operator Control Plane
    category: control-center
    host: mac-mini
    container: control-plane
    image: iap/control-plane:1.0.0
    port: 8086
    internal_port: 8086
    health_url: "http://localhost:8086/healthz"
    health_method: GET
    health_expect: 200
    purpose: |
      Operator control plane — exposes scoped actions
      (container ops, backup trigger, credential rotation, audit
      search, regression probe) over a tailnet-gated web UI.
      Tier 3 actions require operator re-auth.
    depends_on: [vault-server, caddy, docker-socket-proxy-control,
                 sonarr, radarr, prowlarr]
    security:
      no_new_privileges: true
      cap_drop: [ALL]
      cap_add: [NET_BIND_SERVICE]
      read_only: true
    compose_file: docker/control-plane/docker-compose.yml
    credentials: [operator_argon2_hash, sonarr_api_key, radarr_api_key,
                  prowlarr_api_key]
    public_values:
      port: 8086
      tailnet_cidr: 100.64.0.0/10
```

### 7.3 Health endpoint
- `GET /healthz` — returns 200 with `{"status":"ok","version":"1.0.0"}`
- `GET /metrics` — Prometheus format, scraped by VMAgent;
  exports `control_plane_actions_total{tier,action,outcome}`,
  `control_plane_auth_total{tier,outcome}`,
  `control_plane_request_duration_seconds`

### 7.4 Port choice rationale
8086 selected during P2.5 (see §7.1 port note). Free, no adjacent
service confusion, and no existing Caddyfile route consumes it.

---

## 8. Existing service API access (A.7) and architectural concerns

### 8.1 Docker socket access
**Recommendation**: deploy `linuxserver/socket-proxy` (or
equivalent) as a sibling container, not the control-plane itself
mounting `/var/run/docker.sock`. Allowlist:

| Capability | Allowed? | Reason |
|---|---|---|
| CONTAINERS | ✅ | list/inspect/logs |
| POST | ✅ (filtered) | restart/stop/start only; no create/exec without explicit allowlist |
| EXEC | ✅ (label-gated) | container must have `iap.exec.allowed=<cmd1>,<cmd2>` label |
| IMAGES, BUILD, VOLUMES, NETWORKS | ❌ | not needed |

The control-plane itself does not see the host's Docker socket; it
talks to `docker-socket-proxy-control:2375` over a private bridge
network (`control-plane-net`).

### 8.2 Sonarr / Radarr / Prowlarr API keys
Already in Vault under `secret/arr/sonarr`, `secret/arr/radarr`,
`secret/arr/prowlarr` (per existing homepage policy). The
`control-plane` policy will get `read` on those same paths. Vault
Agent renders the keys into `/vault/secrets/credentials.env`,
control-plane sources them at start. No env-var injection in the
compose file.

**FINDING (out of Block 2.5 scope, doctrine concern)**: The Sonarr
and Radarr API keys are pasted in plaintext into the `notes` field of
`config/service-registry.yaml` (lines 363, 382). This is a
doctrine violation per CLAUDE.md ("Credential values in tool output,
commit messages, or transcripts"). Recommend rotating those keys and
scrubbing the registry in a separate session — should NOT be folded
into Block 2.5.

### 8.3 Restic / backup access
Control-plane gets its own AppRole `control-plane-backup-reader`
with policy:
```hcl
path "secret/data/restic/backup"  { capabilities = ["read"] }
path "secret/data/minio/backup"   { capabilities = ["read"] }
```

For listing snapshots, control-plane uses these creds directly to
shell out to `restic snapshots --json` (read-only).

For triggering a manual backup, control-plane DOES NOT execute
`scripts/backup.sh` itself (would require Docker access plus the
existing `backup` AppRole's secret-id). Instead:
- A host-side launcher at `/usr/local/bin/iap-backup-trigger` is
  installed (one-line wrapper that runs `scripts/backup.sh` and
  appends the result to a status file).
- control-plane writes a trigger file (e.g.,
  `/var/run/iap/backup-trigger`) which a launchd-watched job picks
  up and runs the launcher.
- This keeps the existing `backup` AppRole isolated to its own
  identity and avoids leaking Docker exec privileges into the
  control-plane container.

(See §8.5 for the same pattern applied to the regression probe.)

### 8.4 Vault read access for the control-plane itself
`control-plane-policy.hcl`:
```hcl
# Hash-only listing — no value reads
path "secret/metadata/*"      { capabilities = ["list", "read"] }

# Operator password and Sonarr/Radarr/Prowlarr keys
path "secret/data/control-plane/operator"  { capabilities = ["read"] }
path "secret/data/arr/sonarr"              { capabilities = ["read"] }
path "secret/data/arr/radarr"              { capabilities = ["read"] }
path "secret/data/arr/prowlarr"            { capabilities = ["read"] }

# Status (no policy mod, no approle mod)
path "sys/health"                          { capabilities = ["read"] }
path "sys/seal-status"                     { capabilities = ["read"] }
path "sys/policies/acl"                    { capabilities = ["list"] }
path "sys/policies/acl/+"                  { capabilities = ["read"] }
path "auth/approle/role"                   { capabilities = ["list"] }

# Explicit deny on policy / approle modification
path "sys/policies/acl/*"                  { capabilities = ["deny"] }
path "auth/approle/role/*"                 { capabilities = ["deny"] }
```

Note: `secret/metadata/*` lets us enumerate paths for the credentials
view but does NOT permit reading values (those live at `secret/data/`).

### 8.5 Architectural concern: regression probe execution
The H1 regression probe (`docs/phase-13/h1-regression-probe.sh`)
uses `$(/bin/cat ~/.vault-token)` (root token) and `docker exec`
into multiple containers including `vault-server`. We **cannot**
hand the control-plane container that level of access — it would
collapse the entire trust model.

**Recommendation**: same host-launcher pattern as backup trigger.
A host-side `/usr/local/bin/iap-regression-probe-trigger` script
runs the probe and writes structured output to
`/var/run/iap/probe-results/<gate-id>-<ts>.json`. control-plane
writes a trigger file, watches the results directory, and surfaces
the JSON to the frontend.

This keeps root-token-bearing scripts on the host, never inside
the control-plane container.

### 8.6 Architectural concern: audit log access
Vault audit log lives at `/vault/logs/audit.log` inside the
vault-server container. Three options:

(a) Mount the underlying host volume read-only into control-plane
(b) Stream via `docker exec vault-server tail -f`
(c) Phase-14 Loki shipper

Recommend **(a)** — the audit log is already a JSON-lines file on
disk; mounting it RO into control-plane is one extra volume mount
and the simplest workable path. Defer (c) to Phase 14 when Loki
arrives.

### 8.7 Architectural concern: Block 3 collision surface
Block 3 (HA + voice platform) is running in a separate session and
will commit to this same repo. Likely conflict points and mitigation:

| File | Likely Block 3 change | Block 2.5 change | Conflict risk |
|---|---|---|---|
| `config/service-registry.yaml` | append HA / voice / wyoming entries | append `control-plane` entry | LOW — both append to end |
| `docker/caddy/Caddyfile` | append `ha.internal`, `voice.internal` routes | append `control.internal` route | LOW — both append |
| `config/vault-policies/` | new files: `ha-bridge-policy.hcl`, etc. | new file: `control-plane-policy.hcl` | NONE — disjoint files |
| `scripts/` | possibly new HA helper scripts | none | NONE |
| `docker/` | new `docker/ha-*` or `docker/voice-*` dirs | new `docker/control-plane/` | NONE |
| `CLAUDE.md` | possibly Block 3 doctrine additions | possibly Block 2.5 doctrine additions | MEDIUM — same file, different sections |

**Mitigation**: keep all Block 2.5 changes append-only in shared
files. Coordinate the CLAUDE.md update at merge time (rebase will
likely auto-resolve since changes are in different sections).

### 8.8 Architectural concern: Sonarr/Radarr API key leak
See §8.2. Flagged here as a Block 2.5-discovered finding.

---

## 9. Compose pattern preview

The control-plane stack will follow canonical pattern with one
addition (the docker-socket-proxy sibling). Skeleton:

```yaml
version: "3.9"

services:
  # Sidecar 1: Vault Agent renders creds at startup, exits 0
  vault-agent-control-plane:
    image: hashicorp/vault:2.0.0
    container_name: vault-agent-control-plane
    restart: "no"
    environment:
      VAULT_ADDR: "http://vault-server:8200"
      SKIP_SETCAP: "true"
    volumes:
      - /Users/admin/.vault-approle/control-plane:/vault/approle:ro
      - /Users/admin/.vault-agent-secrets/control-plane:/vault/secrets
      - ./vault-agent/agent.hcl:/vault/config/agent.hcl:ro
      - ./vault-agent/credentials.env.tmpl:/vault/agent-config/credentials.env.tmpl:ro
    command: agent -config=/vault/config/agent.hcl
    networks: [control-center-net]
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]

  # Sibling: Docker socket proxy with allowlist
  docker-socket-proxy-control:
    image: lscr.io/linuxserver/socket-proxy:latest
    container_name: docker-socket-proxy-control
    restart: unless-stopped
    environment:
      CONTAINERS: "1"
      INFO: "1"
      POST: "1"        # restart/stop/start
      EXEC: "1"        # gated by container label in app code
      IMAGES: "0"
      BUILD: "0"
      VOLUMES: "0"
      NETWORKS: "0"
      SYSTEM: "0"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks: [control-plane-net]
    cap_drop: [ALL]
    cap_add: [CHOWN, SETGID, SETUID]
    security_opt: [no-new-privileges:true]
    read_only: true
    tmpfs: ["/run"]

  # Main service
  control-plane:
    image: iap/control-plane:1.0.0
    container_name: control-plane
    restart: unless-stopped
    depends_on:
      vault-agent-control-plane:
        condition: service_completed_successfully
      docker-socket-proxy-control:
        condition: service_started
    ports:
      - "127.0.0.1:8094:8094"   # bound to localhost; Caddy proxies
    environment:
      DOCKER_HOST: "tcp://docker-socket-proxy-control:2375"
      VAULT_ADDR: "http://vault-server:8200"
      AUDIT_LOG_PATH: "/vault/logs/audit.log"
      CADDY_ACCESS_LOG_PATH: "/var/log/caddy/access.log"
    volumes:
      - /Users/admin/.vault-agent-secrets/control-plane:/vault/secrets:ro
      - vault-audit-log-ro:/vault/logs:ro      # mounted from vault-server's host bind
      - caddy-access-log-ro:/var/log/caddy:ro  # mounted from caddy's host bind
      - /var/run/iap:/var/run/iap              # trigger files for host launchers
    entrypoint: ["sh", "-c", "set -a && . /vault/secrets/credentials.env && set +a && exec uvicorn app.main:app --host 0.0.0.0 --port 8094"]
    networks: [control-plane-net, control-center-net]
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
    security_opt: [no-new-privileges:true]
    read_only: true
    tmpfs: ["/tmp"]
    mem_limit: 256m
    cpus: 0.5
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:8094/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    labels:
      com.iap.service: "control-plane"
      com.iap.tier: "control-center"

volumes:
  vault-audit-log-ro:
    name: vault-audit-log-ro
    external: true   # provisioned in P2.1
  caddy-access-log-ro:
    name: caddy-access-log-ro
    external: true   # provisioned in P2.1

networks:
  control-plane-net:
    name: control-plane-net
    driver: bridge
  control-center-net:
    external: true
```

(Final compose written in P2.4; this skeleton is for review only.)

---

## 10. Architectural concerns summary

For convenience, the concerns surfaced in §8:

1. **Audit log access**: mount `/vault/logs/audit.log` RO into
   control-plane (option a in §8.6). Defer log shipping to Phase 14.
2. **Docker socket access**: dedicated `linuxserver/socket-proxy`
   sibling container with allowlist; control-plane never sees the
   host socket directly.
3. **Vaultwarden auth**: skip — use Vault-stored Argon2 password
   for Tier 3 re-auth (Path 3 with simplified backend).
4. **Tailnet IP detection**: handled at Caddy layer with
   `@tailnet remote_ip 100.64.0.0/10` matcher; off-tailnet 403'd
   before reaching control-plane.
5. **Regression probe execution**: trigger-file pattern; root-token
   scripts stay on host, control-plane never holds elevated creds.
6. **Backup trigger**: trigger-file pattern (same shape as #5).
7. **Sonarr/Radarr API key leak in service-registry.yaml**: out of
   Block 2.5 scope; flagged for separate remediation session.
8. **Block 3 collision surface**: append-only changes in shared
   files; merge-time coordination on CLAUDE.md additions.

---

## 11. Decisions to confirm before Phase 2

| # | Decision | Recommendation | Confirm? |
|---|---|---|---|
| D1 | Action surface inventory (§2) | as listed | y/n + edits |
| D2 | Auth path | Path 3 hybrid with Vault-stored Argon2 (NOT Vaultwarden integration) | y/n |
| D3 | Backend stack | Python FastAPI + uvicorn | y/n |
| D4 | Frontend stack | HTMX + Tailwind + Jinja2 | y/n |
| D5 | Tier assignments (§6) | as listed (consider re-tiering "trigger manual backup" to T3?) | y/n + edits |
| D6 | Caddy route + service-registry slot (§7) | port 8094, append-only entries | y/n |
| D7 | Docker socket proxy | dedicated linuxserver/socket-proxy sibling container | y/n |
| D8 | Regression probe + backup trigger via host-launcher pattern (§8.3, §8.5) | yes — keeps elevated creds on host | y/n |
| D9 | Audit log access via RO volume mount (§8.6 option a) | yes | y/n |
| D10 | Defer Sonarr/Radarr API key scrub to separate session | yes — out of Block 2.5 scope | y/n |

---

## 12. Phase 1 deliverable status

- ✅ Branch `feat/block-2.5-control-plane` created
- ✅ Action surface enumerated (§2)
- ✅ Auth architecture surfaced with recommendation (§3)
- ✅ Backend stack surfaced with recommendation (§4)
- ✅ Frontend stack surfaced with recommendation (§5)
- ✅ Permission tier assignments drafted (§6)
- ✅ Caddy + service-registry slot drafted (§7)
- ✅ Service API access plan + 8 architectural concerns documented (§8)
- ✅ Compose skeleton previewed (§9)
- ⏸ **PAUSE — awaiting user approval of D1–D10 in §11**

After approval, Phase 2 begins with Vault path / AppRole / policy
creation (P2.1) and proceeds through the gated phases per the Block
2.5 prompt.
