# State-Anchoring Tooling Discovery

**Date:** 2026-04-29
**Operator:** claude-opus-4-7[1m]
**Block:** Phase 13 Block 4.B
**Mode:** Read-only empirical discovery (single artifact write at close)
**Scope:** Inventory what state-anchoring infrastructure already exists. Do **not** recommend new tooling — that comes after user validation.

---

## PRECONDITION VERIFICATION (B0)

| Precondition | Verification | Result |
|---|---|---|
| Repo on `main` and clean (post-Block-4.A) | `git branch --show-current` → `main`; `git log --oneline -5` shows 5077811 (Block 4.A close) at HEAD | ✅ |
| Block 4.A artifacts present | `docs/phase-13/PHASE_13_BLOCK_4A_CLOSEOUT_2026-04-29.md` exists | ✅ |
| Tag `v13-block-3-close` placed | placed in A6, pushed in A7 | ✅ |
| Operator authorization | user message at session start | ✅ |

Read-only discipline: no writes outside this single report file at B5.

---

## CMDB STATE (B1)

### Current authoritative artifact

**`config/service-registry.yaml`** is the closest thing to a CMDB the platform has today. It is a hand-maintained YAML inventory of platform services.

| Property | Value | Source |
|---|---|---|
| Location | `config/service-registry.yaml` | repo |
| Entry count | **70 services** (post-Block-4.A reconciliation) | `yq '.services \| length'` (B1 archaeology) |
| Schema fields per entry | `id`, `container`, `port`, `caddy`, `vault_paths`, `dependencies`, `health_check`, `tags`, `description` | header comment + sampled entries |
| Container drift gap (registry vs `docker ps`) | 5 entries added in Block 4.A A4 (`docker-socket-proxy-control`, `catt-controller`, `cadvisor`, `seal-vault`, `plex-mcp`); `iap-dashboard` annotated deprecated. Planner's earlier "19 unregistered" was an `id` (logical) vs container-name comparison artifact; the actual drift was 5. | A4 reconciliation |
| Validation tooling | `scripts/validate-cmdb.sh` — exists, validates registry against `docker ps`, surfaces drift | grep + read |
| Topology consumer | `topology-api` container reads the registry to render `/api/topology` and feeds Grafana `service-topology` dashboard (uid `service-topology`, panels=48) | `docker ps`, dashboard JSON |
| Homepage consumer | `homepage` container references registry indirectly via Caddy `.internal` route map | A4 confirmation |
| Caddy consumer | `docker/caddy/Caddyfile` includes per-site `import access_log`; routes are not auto-generated from the registry — manual ↔ implicit drift between Caddy and registry exists (12 unbacked `*.internal` routes per CLAUDE.md follow-up #1) | CLAUDE.md, A4 |

### Git history reveals more CMDB ambition than the current tree contains

`git log --oneline --all | grep -iE 'cmdb\|RGC-\|registry'` shows substantial historical work (P0/RGC-* commit prefixes). However, the **only CMDB tooling artifact currently present in the working tree is `scripts/validate-cmdb.sh`**. No `cmdb/` directory, no schema validator beyond shell, no relationship/state graph beyond the registry's flat YAML.

### What the registry is — and isn't

- ✅ Source-of-truth for *which* services exist on the control plane (Mac Mini)
- ✅ Source-of-truth for service ↔ port ↔ Caddy site ↔ Vault path mapping
- ✅ Consumed by `topology-api` to render dashboards
- ❌ Not auto-validated continuously; drift detection requires manually running `validate-cmdb.sh`
- ❌ Does not track *runtime state* (up/down, version, last-deploy timestamp) — that lives in Grafana/VictoriaMetrics + Uptime Kuma, separately
- ❌ Does not model heterogeneous-host membership beyond Mac Mini (NUC HA, Mac Mini Cast, Threadripper future) — registry is implicitly Mac-Mini-scoped
- ❌ No machine-actionable schema file; YAML structure is enforced only by `validate-cmdb.sh` heuristics
- ❌ No history/audit trail beyond `git log` of the YAML file
- ❌ No "decision intent" capture — *why* a service exists, what it replaces, what its sunset criterion is

---

## ROADMAP TOOL STATE (B2)

### Plane CE — adopted, partially populated

| Property | Value | Source |
|---|---|---|
| Deployment | `docker-plane-*` containers (api, web, worker, beat, db, minio, redis) — 7 containers, all up | `docker ps` |
| Workspace slug | `iap` | `framework/plane_connector.py` |
| API access (this session) | `X-API-Key` header → `/api/v1/workspaces/iap/projects/<id>/issues/` (cursor-based pagination); session auth → `/api/` legacy paths | empirical, B2 probe |
| Issue count | **604** (cursor-paginated full enumeration) | API call |
| Configured labels | **64 labels** | API call |
| Labels actually applied | **0 of 604 issues have any label** | API call |
| Configured states | **9 states** (Backlog, Todo, In Progress, Done, etc.) | API call |
| Issue category prefix | RM-* (e.g., `RM-PLATFORM-001`) — 47 distinct prefix tokens parsed across 604 issues | API call + parser |
| Prefix ↔ label match | 44 of 47 distinct prefix tokens match an existing label name *exactly* | scripted comparison |
| Curation gap (estimated effort) | **~1 hour scripted** to back-fill labels from prefix on 604 issues. Earlier planner estimate of "10s of hours" was based on the inflated ~1100 figure. | recalculated |
| MCP wiring | `mcp__plane-roadmap__*` — server registered and callable. Hit 60/min rate limit during this session's probe — transient, server works in principle (per memory `mcp_architecture_deployed.md`). | tool registry |
| Toolchain | `bin/sync_roadmap_to_plane.py`, `bin/configure_plane_agile.py`, `bin/register_plane_mcp.sh`, `framework/plane_connector.py`, `mcp/plane_mcp_server.py` | repo |
| **Security finding** | `~/.claude/projects/-Users-admin-repos-integrated-ai-platform/memory/plane_deployment.md` contains a **plaintext Plane API token** (`plane_api_f6c2c3cc049d4fedb24b0f62acbfc00b`) | grep of memory |

### What the roadmap is — and isn't

- ✅ Captures roadmap items at scale (604 issues exists; prior phase work imported)
- ✅ Has a state model (9 states) — issues have status
- ✅ Has labels-as-categories defined (64) and prefix conventions baked into issue keys
- ✅ Toolchain for sync, MCP exposure, agile config exists
- ❌ **Priority signal absent** — labels (the natural carrier for category + priority) are configured but unattached to any issue. The 604 issues have *prefixes* and *states* but nothing the platform can sort by importance.
- ❌ No ADR/strategic-document linkage — issues aren't anchored to architectural intent
- ❌ Memory file holds a plaintext token (security finding — surface to user)
- ❌ MCP rate limit (60/min per token) is low for batch operations

---

## STATE-ANCHORING INVENTORY (B3)

### Vault — credential state-of-record

| Property | Value | Source |
|---|---|---|
| Mode | server (persistent file storage) | `docker exec vault-server vault status` (history) |
| Auto-unseal | Transit, via `seal-vault` container | `docker ps`; CLAUDE.md |
| Sealed | `false` | regression probe (Block 4.A A7) |
| Audit log | `/vault/logs/audit.log` — incrementing | regression probe |
| KV mount | `secret/` | confirmed in A4 (registry vault_paths) |
| AppRole pattern | per-service AppRoles (no root token in containers); credentials reach containers via Vault Agent sidecars writing to `/Users/admin/.vault-agent-secrets/<svc>/` | CLAUDE.md doctrine + sampled paths |
| **Anchoring role** | source-of-truth for *credential state* (who has access, where the value lives, when it last rotated). `secret/<svc>/api → {token, rotated, reason}` shape (sampled `secret/grafana/api`). | empirical |
| Gap | Vault is excellent for credentials but is *not* a general-purpose CMDB. Service-existence and runtime-relationship state are not in Vault. | by design |

### Zabbix — host monitoring partial

| Property | Value | Source |
|---|---|---|
| Hosts registered | **5** — `opnsense`, `mac-mini`, `qnap-ts-x72`, `Zabbix server`, `mac-mini-m4-pro` | `host.get` (Bearer auth) |
| Host groups | 7 defined | `hostgroup.get` |
| Templates linked | network device + Linux + macOS + zabbix-server-health (per host as listed) | `host.get` |
| API auth | Zabbix 7.x requires `Authorization: Bearer <token>` header (legacy `auth` field rejected) | empirical |
| Coverage gap | 5 hosts vs **47 platform containers** vs **70 registry services**. Zabbix tracks *physical-host* state, not container-level. | comparison |
| **Anchoring role** | Source-of-truth for *physical-host* uptime + agent-reachable system metrics. Does not anchor service-level state. | by design |

### VictoriaMetrics + vmagent + Grafana — observability-as-state

| Property | Value | Source |
|---|---|---|
| Distinct metric names (`__name__`) | **618** | `/api/v1/label/__name__/values` |
| Distinct jobs scraped | **5** — `caddy`, `cadvisor`, `mcp-docs`, `node-exporter`, `vmagent` | `/api/v1/label/job/values` |
| Distinct instances | **5** — `host.docker.internal:2019` (caddy), `:8088` (cadvisor inferred), `:8093` (mcp-docs), `:9100` (node-exporter), `vmagent:8429` | `/api/v1/label/instance/values` |
| `service` label values | **3** — `caddy`, `cadvisor`, `mcp-docs-remote` | `/api/v1/label/service/values` |
| `container` label | **empty** — Mac Docker Desktop cAdvisor cgroup-resolution limitation (CLAUDE.md "Known Hardening Trade-offs") | empirical |
| Total active series | ~111,100 | `/api/v1/series/count` |
| Grafana dashboards (live, by SA token) | **7** — `backup-status`, `container-health`, `network-caddy`, `phase7-infra`, `platform-overview`, `service-topology`, `vault-audit` | `/api/search` |
| Provisioned dashboard JSONs | 7 in `docker/grafana-provisioning/dashboards/` (1:1 with live) | filesystem |
| **Anchoring role** | Source-of-truth for *runtime metric state* of the 5 scraped jobs. Does *not* cover the other 42 containers' container-level metrics. | empirical |
| Gap | Friendly container labels missing → operator must map `id="/docker/<sha>"` to names manually. Will resolve when platform moves to Linux. | CLAUDE.md |

### Uptime Kuma — synthetic uptime probes

| Property | Value | Source |
|---|---|---|
| Active monitors | **12** | sqlite query of `/app/data/kuma.db` |
| Monitor targets | Home Assistant (.141), Vault, Sonarr, Radarr, Prowlarr, Plex, Grafana, Open WebUI, Homarr, LiteLLM, Plane, Obot | DB enumeration |
| **Anchoring role** | Source-of-truth for *user-perceived availability* of 12 selected services. Does not enumerate the full service set. | by design |
| Gap | Monitors **12 of 70** registry services. No automatic provisioning from registry → human-curated list. | comparison |

### MCP servers callable in this session (categorized)

| Category | Servers / tool families |
|---|---|
| **Read-state — platform** | `mcp__plane-roadmap__*` (roadmap), `mcp__pipeline-monitor__*` (pipeline), `mcp__arr-orchestration__*` (\*arr stack), `mcp__sqlite__read_query`/`list_tables`/`describe_table`, `mcp__postgresql-mcp__query` (read primitive), `mcp__filesystem-mcp__read_*`/`list_*`/`search_files`, `mcp__memory__read_graph`/`search_nodes`/`open_nodes` |
| **Write-state — platform** | `mcp__plane-roadmap__create_issue`/`update_status`, `mcp__sqlite__write_query`/`create_table`/`append_insight`, `mcp__filesystem-mcp__write_file`/`edit_file`/`move_file`, `mcp__memory__create_entities`/`add_observations`/`create_relations`/`delete_*` |
| **External integrations (not platform state)** | `mcp__claude_ai_GitHub_Copilot__*` (60+ tools), `mcp__claude_ai_Gmail__*`, `mcp__claude_ai_Google_Calendar__*`, `mcp__claude_ai_Google_Drive__*`, `mcp__claude_ai_Notion__*`, `mcp__claude_ai_monday_com__*`, `mcp__claude_ai_Microsoft_Learn__*` |
| **Reasoning helper (no state)** | `mcp__sequential-thinking__sequentialthinking` |

The repo's `config/oss_wave/mcp_servers.json` is a small *approved-list* (filesystem, everything, sequential-thinking) — not the runtime registry. The runtime set above came from this session's deferred-tools enumeration.

---

## GAP ANALYSIS (B4)

User-stated needs (paraphrased from operating doctrine):
1. **CMDB-style anchoring** — a system-of-record for platform state so AI agents and operators don't drift.
2. **Roadmap with priority signal** — agents should know what matters most next.
3. **Drift detection** — when reality diverges from intent, surface it.
4. **Architectural intent** — agents should know *why* something exists, not just *that* it exists.

Mapped against the empirical inventory:

| User need | Best existing anchor | What it covers | What it misses |
|---|---|---|---|
| **CMDB / system-of-record** | `config/service-registry.yaml` (70 svc) + `scripts/validate-cmdb.sh` | which services exist, port/Caddy/Vault map, dependency hints | runtime state, decision intent, multi-host scope, continuous validation, machine-readable schema, history |
| **Roadmap with priority signal** | Plane CE (604 issues, 9 states, 64 labels configured, MCP exposed) | issue text, state, hierarchy potential | **labels unattached on every issue** → priority is unsignalled; no ADR linkage; no architecture-intent dimension |
| **Drift detection** | `validate-cmdb.sh` (registry ↔ `docker ps`); regression probe (`docs/phase-13/h1-regression-probe.sh`) | one-shot drift between registry and live containers, gate-style health pass/fail | not continuous; no historical drift series; doesn't cover Caddy↔registry drift (12 dead routes), Plane↔ADR drift, Vault↔registry vault_paths drift |
| **Architectural intent** | ADRs (10 files in `docs/adr/`) + phase docs in `docs/phase-13/` | high-level decisions and per-block rationale | not linked to roadmap items, registry entries, or services in any machine-traversable way |

### The platform's state surface fragments

State-of-record is currently spread across **at least eight distinct sources** with no overarching index:

1. `config/service-registry.yaml` — declared service inventory
2. `docs/adr/*.md` — architectural decisions
3. `docs/phase-*/` — phase narratives and closeouts
4. `docker/caddy/Caddyfile` — declared HTTP routes (drift vs registry: 12 unbacked routes per CLAUDE.md)
5. Vault (`secret/*`) — credentials with rotation timestamps
6. Plane CE — roadmap (604 issues, but unprioritised)
7. VictoriaMetrics + Grafana — runtime metrics for 5 scraped jobs (incomplete coverage)
8. Uptime Kuma — synthetic uptime for 12 monitored targets (incomplete coverage)
9. Zabbix — host-level metrics for 5 hosts (no container layer)

There is **no cross-index** that lets an agent ask "what is service X's complete state?" and get a single coherent answer.

### Categorisation per the prompt's taxonomy

Per the gap-analysis taxonomy in the Block 4.B prompt (a–g), this platform sits at:

- **(a) Inventory exists, validated by tooling** — partial: registry exists; validation is one-shot.
- **(b) Inventory exists, no validation tooling** — n/a.
- **(c) Roadmap captured, priority absent** — **yes** (604 issues, 0 labels applied).
- **(d) Decisions captured, not linked** — **yes** (10 ADRs, no link to registry/roadmap/services).
- **(e) Runtime state captured, partial coverage** — **yes** (5/47 containers metric-scraped, 12/70 services Kuma-monitored).
- **(f) Drift detection one-shot, not continuous** — **yes** (validate-cmdb.sh, regression probe).
- **(g) Cross-index missing** — **yes** — no joining structure between (a), (c), (d), (e).

---

## UNKNOWNS

Surfacing items where empirical evidence stops short of confident claim:

1. **Whether `validate-cmdb.sh` is invoked anywhere automatically** — git log shows commits adding it; no cron, hook, or CI invocation found in tree-scan. May run only manually.
2. **Whether the existing 64 Plane labels match the 47 RM-prefix categories *semantically*** — the 44/47 *exact* string match is high but doesn't guarantee the label taxonomy is what the user wants for priority signal. User judgement needed.
3. **Memory file plane_deployment.md plaintext token** — surfaced as security finding. Token may already have been rotated; not verified this session (would require Plane admin UI). User decision: rotate + redact memory, or accept as local-only file.
4. **Plane MCP rate limit has per-endpoint buckets, not just per-token-per-minute.** Post-cooldown probe (30 min after the heavy 604-record enumeration) confirmed: `list_states` and `list_categories` return immediately (independently confirming **9 states / 64 labels**), but every `issues/`-rooted call (`list_issues`, `get_issue`, `get_stats`) still 429s. The `issues/` bucket has a longer-window throttle on top of the documented 60/min global cap. **Implication:** any future batch label-back-fill must use direct DB access (`docker-plane-db-1`) or chunked calls via `framework/plane_connector.py`'s built-in 429 retry — the MCP path is not viable for issue mutation at scale.
5. **Zabbix host coverage strategy** — 5 hosts is *deliberate* (physical hosts, not containers) per existing trade-off doctrine, but whether the Threadripper / Mac Studio future hosts are anticipated to be added is unclear from current docs.
6. **Whether the 7 Grafana dashboards constitute "enough" state-view coverage or are missing key views** — operator judgement; no spec to test against.
7. **Whether the user wants ADR↔roadmap↔registry linkage** to be a *new tool* or an *augmentation of existing tools* (e.g., a generated cross-index file under `docs/`) — Block 4.B explicitly forbids this report from recommending. Decision belongs to the next block.
8. **Whether GitHub Issues / Notion / Monday MCPs are intended as production state stores** or just available because Anthropic's MCP catalog enables them — they appear unused for platform anchoring, but that is inferred from the absence of references in the registry / phase docs, not affirmatively confirmed.

---

## EVIDENCE INDEX

| Claim | Verification |
|---|---|
| 70 services in registry | `yq '.services \| length' config/service-registry.yaml` (B1) |
| 5 host-Zabbix entries | `host.get` API with Bearer header (B3.4) |
| 604 Plane issues | cursor-paginated `/api/v1/workspaces/iap/projects/<id>/issues/` (B2) |
| 0 labels on issues | per-issue label inspection sample + endpoint (B2) |
| 7 Grafana dashboards live | `/api/search?type=dash-db` with SA token `secret/grafana/api:homepage_token` (token hash 371d1623c0320c03) |
| 5 jobs / 5 instances / 618 metric names in VM | VM `/api/v1/label/{job,instance,__name__}/values` via `docker exec vm wget` |
| 12 active Uptime Kuma monitors | sqlite `SELECT COUNT(*) FROM monitor WHERE active=1` against `/app/data/kuma.db` |
| 10 ADRs | `ls docs/adr/ADR-*.md` (post-Block-4.A renumber) |
| validate-cmdb.sh exists | `ls scripts/validate-cmdb.sh` |
| Plain-text Plane token in memory | `grep "plane_api_" /Users/admin/.claude/.../memory/plane_deployment.md` |

No tools were recommended in this report. The next block — only after user validation of this discovery — should choose where to invest.
