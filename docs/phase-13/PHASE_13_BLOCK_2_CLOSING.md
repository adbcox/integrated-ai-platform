# Phase 13 — Block 2 Closing Report

**Block scope**: Mac Mini operator visualization (control plane)
**Block close**: 2026-04-28
**Operator**: claude-opus-4-7[1m] under autonomous large-prompt mode
**Gate decision**: P6 accepted; Block 2 closed at the operator-visualization deliverable. MacBook Pro M5 parity (formerly P7/P8) reclassified as Block 3.

---

## Section-by-section deliverables

### §P2 — Homepage on canonical pattern (P2.1–P2.6)

| Step | Deliverable |
|---|---|
| P2.1 | Vault path `secret/homepage/`, AppRole `homepage`, scoped policy |
| P2.2 | `docker/homepage/docker-compose.yml` with vault-agent sidecar (canonical) |
| P2.3 | `docker/homepage/config/{services,settings,kubernetes,docker}.yaml` |
| P2.4 | `homepage.internal` reachable via Caddy with HTTP 200 |
| P2.5 | `config/service-registry.yaml` updated with homepage entry |
| P2.6 | Gate close: regression probe clean, no .env files, sha256-12 hash-only verification |

Grafana service-account token also provisioned during P2.1 to feed the homepage Grafana widget.

### §P3 — Grafana datasources

`docker/grafana-provisioning/datasources/`:

- `victoriametrics.yaml` (existing, retained)
- `infinity.yaml` (NEW) — backend HTTP datasource for arbitrary JSON endpoints; allowed_hosts whitelist for `vault-server:8200` and `topology-api:8300`
- `topology-json.yaml` (NEW) — marcusolsson-json-datasource pointing at `http://topology-api:8300`. Health-check 500 (`plugin.unavailable`) is benign — plugin is frontend-only.

### §P4 — Five Grafana dashboards

| UID | Dashboard | Source |
|---|---|---|
| `platform-overview` | Platform Overview | retained from prior phase |
| `container-health` | Container Health | NEW |
| `network-caddy` | Network & Reverse Proxy | NEW |
| `vault-audit` | Vault — Health & Audit | NEW |
| `backup-status` | Backup Status (Restic) | NEW (placeholder until Phase 14) |

All dashboards provisioned via `docker/grafana-provisioning/dashboards/`, picked up automatically via `/api/admin/provisioning/dashboards/reload`.

**Container Health workaround**: cAdvisor on Docker Desktop Mac emits cgroup-only ids (`id="/docker/<sha>"`); all panels use `id=~"/docker/.+"` selectors with `label_replace(..., "id", "$1", "id", "/docker/(.{12}).*")` to truncate the hash to 12 chars in legends.

### §P5 — Topology API + Service Topology dashboard

| Component | Detail |
|---|---|
| `docker/topology-api/Dockerfile` | python:3.12-alpine + pyyaml==6.0.1, non-root user, port 8300 |
| `docker/topology-api/server.py` | stdlib http.server; `/health`, `/api/topology`, `/api/topology/nodes`, `/api/topology/edges` |
| `docker/topology-api/docker-compose.yml` | `iap/topology-api:1.0.0`; **mounts `config:/config:ro` as a directory (not single file)** to dodge Docker Desktop Mac inode-snapshot bug |
| Dashboard `topology.json` (uid `service-topology`) | Core Node Graph panel, two stat panels for service/edge counts, services inventory table |
| `config/service-registry.yaml` | topology-api entry added (64 services, 52 edges) |

### §P6 — Zabbix host registration + Caddy per-site logs/metrics

**Zabbix host**

| Field | Value |
|---|---|
| host / name | `mac-mini` / `Mac Mini M5 (control center)` |
| hostid | `10783` |
| group | `Linux servers` (groupid 2) |
| template | `Linux by Zabbix agent` (templateid 10001) |
| interface | DNS `zabbix-agent:10050`, type 1 |
| availability | `1` (reachable) |
| sample items | `vm.memory.size[available]` 9.4 GiB, `vm.memory.size[pavailable]` 56.20 % |

`docker/zabbix/docker-compose.yml`: `ZBX_HOSTNAME` aligned to `mac-mini` (was `Mac-Mini-M4-Pro`).

**Caddy logs + metrics**

`docker/caddy/Caddyfile`:

- Global `metrics` directive — exposes `caddy_http_request_*` series on admin `:2019/metrics`.
- Shared `(access_log)` snippet writing JSON entries to `/var/log/caddy/access.log` (rolled at 100 MiB / 7 keeps).
- `import access_log` added to all 36 `*.internal` site blocks.

VMAgent `caddy` job confirmed up; `caddy_http_requests_total` flowing into VictoriaMetrics. Access log captured 6 distinct site `host` fields during verification (`grafana.internal`, `homepage.internal`, `uptime.internal`, `victoria.internal`, `zabbix.internal`, plus admin endpoint hits).

---

## Final regression probe

```
PASS=15  FAIL=0  WARN=3
```

WARNs (all benign):
- `openhands.internal` not in macOS DNS cache (service exists, not exercised this run)
- restic snapshot recency unreachable without AppRole (probe runs unauthenticated)
- gate-specific dependency probes: probe invoked with `unspecified` gate

---

## Findings worth surfacing

1. **Zabbix 7.x API auth doctrine** — JSON-RPC `auth` field removed; all post-login API calls must use `Authorization: Bearer <token>` HTTP header. Documented in `PHASE_13_BLOCK_2_P6_RESULTS_2026-04-28.md`.

2. **Caddy per-host-label ceiling** — Caddy 2.11.2's default Prometheus output labels `caddy_http_request_*` series with `code/handler/method/server` only — **no `host` label**. Per-server (`server="srv0"`) is the finest aggregation available from metrics. Per-site analysis requires Loki-tailing the JSON access log (deferred to Phase 14). Documented in CLAUDE.md Known Hardening Trade-offs.

3. **Docker Desktop Mac single-file bind-mount inode snapshot** — recurred for the Caddyfile mount; resolved by `docker compose restart caddy`. Same workaround documented for topology-api (which dodged the issue by mounting the parent directory). Pattern preference going forward: bind-mount the parent directory, not the file, when atomic-replace edits must be visible without restart.

4. **TopologyJSON datasource health-check 500** — `plugin.unavailable` on `/health` is benign: marcusolsson-json-datasource is a frontend-only plugin (no backend). Queries route through frontend HTTP at panel-render time.

5. **cAdvisor friendly-name labels missing on Docker Desktop Mac** — no fix; documented as KNOWN-LIMITATION. Returns when the platform migrates to Linux/Threadripper.

---

## Block-2 working tree changeset (single coordinated commit)

| Path | Change |
|---|---|
| `CLAUDE.md` | Block 2 scope reflected; post-Block-2 follow-up list added; resolved Trade-offs entries updated |
| `config/service-registry.yaml` | topology-api added (64 services, 52 edges) |
| `config/vault-policies/grafana-obs-policy.hcl` | scoped policy update |
| `config/vault-policies/homepage-policy.hcl` | scoped policy for AppRole |
| `docker/caddy/Caddyfile` | global `metrics`, shared `(access_log)` snippet, 36 site `import access_log` directives |
| `docker/observability-stack.yml` | observability-stack adjustments |
| `docker/zabbix/docker-compose.yml` | `ZBX_HOSTNAME=mac-mini` |
| `docker/grafana-obs/` | new |
| `docker/grafana-provisioning/dashboards/{backup-status,container-health,network-caddy,topology,vault-audit}.json` | new |
| `docker/grafana-provisioning/datasources/{infinity,topology-json}.yaml` | new |
| `docker/homepage/` | new (canonical compose + sidecar + configs) |
| `docker/topology-api/` | new (Dockerfile, server.py, compose) |
| `docs/phase-13/PHASE_13_BLOCK_2_P6_RESULTS_2026-04-28.md` | P6 results |
| `docs/phase-13/PHASE_13_BLOCK_2_CLOSING.md` | this report |
| `docs/phase-13/PRE_BLOCK_2_FOUNDATION_AUDIT_2026-04-28.md` | pre-block audit |

---

## Post-Block-2 follow-up list

1. **Caddy route hygiene** — prune 12 dead `*.internal` routes (`manyfold`, `gitea`, `tautulli`, `overseerr`, `ragflow`, `portainer`, `netdata`, `dozzle`, `pgadmin`, `bookstack`, `n8n`, `filebrowser`). The `import access_log` snippet is harmless but inflates the Caddyfile.
2. **Homepage widget completion** — confirm Grafana SA token (provisioned in P2.1) and Uptime Kuma slug config render expected widgets on `homepage.internal`. Closes if no remaining gaps.
3. **Block 3** — MacBook Pro M5 parity: Ollama + LiteLLM + Open WebUI + Headscale client + smart routing. Executed as a separate block when user is ready.
4. **Phase 14** — Loki for log-based per-site Caddy analysis (unblocks per-host dashboards that Caddy 2.11.2 default Prometheus output cannot provide).

---

## Block 2 closed

Mac Mini control plane is feature-complete for operator visualization. Standing down from execution mode. User will inspect dashboards, then schedule Block 3 (MacBook parity) or visual polish session as separate work.
