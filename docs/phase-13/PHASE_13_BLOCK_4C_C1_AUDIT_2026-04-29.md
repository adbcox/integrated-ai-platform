# Phase 13 Block 4.C — C1 Architecture Audit

**Operator:** claude-opus-4-7
**Date:** 2026-04-29
**Phase:** Block 4.C / C1 (read-only architecture audit)
**Plan:** [PHASE_13_BLOCK_4C_PLAN_2026-04-29.md](PHASE_13_BLOCK_4C_PLAN_2026-04-29.md)

This document is the C1 deliverable. It enumerates the 70 registry
services, maps registry fields to NetBox stock schema vs custom
fields, surfaces topology decisions for user approval, and
re-verifies Block 4.B's prefix→label match with fresh data from
the live Plane DB.

The C1 gate is at the end of this document. C2 does not begin
until the user reviews the surfaced decisions and findings.

---

## C1.1 — Registry analysis (70 services)

### Categorization

`config/service-registry.yaml` defines 70 service entries across
15 categories and 4 hosts.

| Category | Count | Notes |
|---|---:|---|
| `mcp-shim` | 17 | Obot/Nanobot integration shims |
| `platform` | 14 | Vault, Caddy, control-plane, sidecars |
| `ai` | 9 | LiteLLM, Ollama, Open WebUI, OpenHands, Plex MCP, Sportarr, MCPO, AnythingLLM, Plane |
| `observability` | 7 | VictoriaMetrics, Grafana, Uptime Kuma, cAdvisor, Node Exporter, VMAgent, Zabbix Agent |
| `media` | 5 | Plex, Sonarr, Radarr, Prowlarr, NextCloud-DB |
| `mcp` | 3 | MCP Docker, MCP Docs, MCP Filesystem (Remote HTTP variants) |
| `monitoring` | 3 | Zabbix Server, Zabbix Web, Zabbix-Postgres |
| `infrastructure` | 2 | MinIO, Headscale |
| `data` | 2 | Plane PostgreSQL, Plane Redis |
| `automation` | 2 | Home Assistant (container + physical) |
| `control-center` | 2 | Topology API, Homepage |
| `network` | 1 | OPNsense |
| `visibility` | 1 | Uptime Kuma (duplicate ID — see finding A) |
| `home-automation` | 1 | Home Assistant (additional) |
| `integration` | 1 | Cast-All-The-Things controller |

| Host | Count |
|---|---:|
| `mac-mini` | 67 |
| `qnap` | 1 |
| `ha-device` | 1 |
| `opnsense` | 1 |

The `kind` discriminator is sparsely populated:
- `kind: sidecar` — 1 service (`docker-socket-proxy-control`,
  sidecar of `control-plane`)
- `kind: support-service` — 1 service (`seal-vault`, the Transit
  auto-unseal helper added in Block 4.A registry reconciliation)

68 of 70 entries leave `kind` unset. This is the existing reality;
C3 must tolerate or normalize.

### Registry field union (23 fields total)

Every field that appears at least once in the registry:

| Field | Type | Population |
|---|---|---|
| `id` | string | 70/70 (1 duplicate — finding A) |
| `name` | string | 70/70 |
| `category` | enum-ish string | 70/70 |
| `host` | string | 70/70 |
| `container` | string \| null | 65/70 (5 host-resident or external) |
| `image` | string \| null | 65/70 |
| `port` | int \| null | 41/70 |
| `internal_port` | int \| null | 65/70 |
| `health_url` | string \| null | 64/70 |
| `health_method` | string \| null | 64/70 |
| `health_expect` | int or [int] \| null | 64/70 |
| `purpose` | string (free text) | 70/70 |
| `depends_on` | [string] | 70/70 (41 non-empty) |
| `security` | object \| null | 60+/70 |
| `compose_file` | string \| null | 47/70 (rest are `null`) |
| `credentials_env` | [string] | 6/70 |
| `credentials` | [string] or `"none"` | 8/70 (typing-mixed — finding B) |
| `public_values` | object | 2/70 |
| `notes` | string (multiline) | ~30/70 |
| `kind` | enum string | 2/70 |
| `sidecar_of` | string | 1/70 |
| `deprecated` | bool | 1/70 |
| `superseded_by` | string | 1/70 |

### Findings (data-quality issues C3 must address)

**Finding A — Duplicate `uptime-kuma` ID.** Two registry entries
share `id: uptime-kuma`. Both point at the same container,
image, port, and host; one (`category: observability`) is the
older, less-complete entry; the other (`category: visibility`)
adds `credentials: none` and `public_values.status_page_slug:
platform`. This is accidental duplication from a prior import.
**Resolution options for C3:**

1. **De-dupe at migration time** (preferred) — script picks the
   more-complete record; logs the decision.
2. **Pre-fix in YAML** before C3 — single-purpose commit removing
   the `observability` entry, leaving the `visibility` one. Cleaner
   audit trail, but is an out-of-scope edit not anticipated by the
   plan.
3. Defer — let NetBox accept both as separate records.
   Discouraged: NetBox uniqueness constraints will reject.

Recommended: option 1 (in-script de-dup with log), but I will
surface this at the gate.

**Finding B — `credentials` field is type-mixed.** 5 services
have `credentials: none` (literal string), 3 have a list of
Vault key names. NetBox will not accept this hybrid in a single
custom field. **Resolution:** during C3, treat `"none"` as `[]`
(empty list), normalize to a list-of-strings field. No data
loss; simplifies downstream consumers.

**Finding C — Two parallel "credentials" patterns.** `credentials`
(Vault-pointer keys) and `credentials_env` (env-var names) are
different shapes for the same concept. Six services use
`credentials_env`, three use `credentials`-as-list. The audit
recommends consolidating these into a single NetBox custom field
later, but for the C3 import I'll preserve both shapes as-is to
avoid scope creep.

**Finding D — `host: ha-device` and `host: opnsense` are external.**
These two services are not on the Mac Mini and not Docker-managed.
Modeling them in NetBox as Devices (rather than virtualization
ServiceInstances) is more accurate to their nature. Surfaced for
C3 modeling decisions.

### Field → NetBox mapping (recommended)

NetBox 4.x stock schema can absorb most of the registry. The
recommended target object type per service is `dcim.device` for
the four physical/external devices and `ipam.service` (with
`virtualization.virtualmachine` parent) for the 66 containerized
services.

| Registry field | NetBox target | Notes |
|---|---|---|
| `id` | object `name` | unique key |
| `name` | `description` (or device `name` if device) | |
| `category` | tag (multi-tag set) | NetBox native tags work |
| `host` | parent `device` or `cluster` | Site/cluster modeling |
| `container` | custom field `container_name` | text |
| `image` | custom field `container_image` | text |
| `port` + `internal_port` | `ipam.service.ports` | NetBox native |
| `health_url`, `health_method`, `health_expect` | custom fields | text + integer |
| `purpose` | `comments` field | NetBox markdown-rendered |
| `depends_on` | NetBox `ipam.service` cross-references *or* custom field `service_dependencies` longtext | dependency-modeling decision below |
| `security` | custom field `security_profile` longtext (JSON-as-text) | preserves nested object shape |
| `compose_file` | custom field `compose_file` text | |
| `credentials_env` + `credentials` (normalized) | custom field `vault_paths` longtext | comma- or newline-separated |
| `public_values` | custom field `public_values` longtext (JSON) | |
| `notes` | append to `comments` | |
| `kind`, `sidecar_of` | tags + custom field `sidecar_of` text | |
| `deprecated`, `superseded_by` | tag `deprecated` + custom field `superseded_by` text | |

**Dependency-modeling decision (surfacing for user approval).**
`depends_on` is the most architecturally interesting field. Three
options:

1. **Custom-field-as-list** (`service_dependencies: longtext`).
   Simplest; lossy for graph queries; matches today's YAML.
2. **NetBox `ipam.service` cross-reference**. Native; supports
   graph traversal in NetBox UI; requires every dependency target
   to be modeled as `ipam.service` (it will be).
3. **Hybrid**: custom field for free-form notes, native cross-ref
   for code-loadable graph. More work.

Recommended: **option 2** (native cross-reference). It's the
reason for using NetBox over a flat YAML — the dependency graph
becomes queryable without re-parsing. Surfacing for confirmation.

---

## C1.2 — NetBox topology decisions

The plan listed 3 decisions to confirm with the user. Here is my
recommendation for each, with the trade-offs.

### Decision 1: Base image

**Recommend: `netbox-community/netbox-docker` (pinned tag).** This
is the upstream-maintained Docker packaging, used by the NetBox
project itself for development. Pinning a specific image tag
(rather than `latest`) is doctrine.

**Tag choice:** `docker.io/netboxcommunity/netbox:v4.1.x` (latest
stable 4.x line at time of audit) — concrete tag determined at
C2.5 against the upstream tag list. Pre-approved per the plan
prompt: "Pulling the netbox-community/netbox-docker pinned image
(tag selected per plan C1.2)."

Trade-off vs build-from-source: building from source gives full
control but adds CI overhead and patch-management cost.
netbox-docker is the canonical packaging; deviating without cause
is anti-doctrine.

### Decision 2: Postgres topology

**Recommend: dedicated `netbox-postgres` instance.**

| Option | Pros | Cons |
|---|---|---|
| Dedicated `netbox-postgres` | blast-radius isolated; mirrors Plane / Nextcloud / Zabbix pattern; can independently tune `shared_buffers`; independently backed up by Restic | extra container, ~512 MB extra mem |
| Share Plane's DB | one less container | cross-contamination risk; couples NetBox availability to Plane DB lifecycle; mixes data ownership |

Dedicated is the conservative choice and aligns with every other
stateful service in the platform. Mem budget: 1g (per the plan's
hardening guidance).

### Decision 3: Caddy hostname

**Recommend: `netbox.internal`.**

| Option | Pros | Cons |
|---|---|---|
| `netbox.internal` | matches the tool name; lowest cognitive load for operators | none |
| `cmdb.internal` | role-named, future-proof if NetBox is ever swapped | abstract; operators need to remember the mapping |

`netbox.internal` is the recommendation. CMDB-as-role is a
documentation concern, not a hostname concern.

---

## C1.3 — Plane label back-fill methodology

This was Block 4.B's "44/47 prefix→label match". I re-verified
fresh against the live Plane DB on the Mac Mini.

### Reconciliation against Block 4.B's snapshot

| Metric | Block 4.B (2026-04-28) | C1 fresh (2026-04-29) | Δ |
|---|---:|---:|---|
| Active issues | 604 | 611 | +7 (likely roadmap additions) |
| Distinct prefix tokens (RM-only) | 47 | 48 | +1 (`AUTO-MECH` newly resolved — Block 4.B regex bucketed it as `<NO_PREFIX>`) |
| Issues with no `RM-` prefix | not reported separately | 8 | Plane onboarding placeholders + 1 standalone `[TEST]` issue |
| Configured labels (DB-authoritative) | 64 (via MCP) | 66 (DB) | +2 (`admin`, `concepts`) — MCP filters scope |
| Case-insensitive matched prefixes | 44/47 | 45/48 | unchanged conceptually |
| Unmatched prefixes | 3 | 3 | identical: `CI`, `DEPLOY`, `MON` |
| Issues currently labeled | 0 | 3 | 3 Plane onboarding placeholders carrying `concepts` label — none are RM-prefixed; **0 of 603 RM-prefixed issues have any label**, matching 4.B's intent |

### Per-prefix issue counts (current, sorted descending)

| Prefix | Issues | Label match (CI) |
|---|---:|---|
| TESTING | 60 | matches `testing` |
| DOCS | 43 | matches `docs` |
| DATA | 36 | matches `data` |
| CLI | 31 | matches `cli` |
| MONITOR | 31 | matches `MONITOR` |
| API | 30 | matches `api` |
| CONFIG | 30 | matches `CONFIG` |
| REFACTOR | 30 | matches `REFACTOR` |
| SECURITY | 30 | matches `security` |
| UTIL | 30 | matches `UTIL` |
| MEDIA | 21 | matches `media` |
| OPS | 18 | matches `OPS` |
| DEV | 11 | matches `DEV` |
| APIGW | 10 | matches `APIGW` |
| BACKUP | 10 | matches `BACKUP` |
| **CI** | **10** | **UNMATCHED** (near: `CI/CD`) |
| **DEPLOY** | **10** | **UNMATCHED** (near: `Deployment`) |
| FLOW | 10 | matches `FLOW` |
| INT | 10 | matches `INT` |
| **MON** | **10** | **UNMATCHED** (near: `MONITOR` / `Monitoring`) |
| PERF | 10 | matches `PERF` |
| SCALE | 10 | matches `SCALE` |
| USERMGMT | 10 | matches `USERMGMT` |
| UX | 10 | matches `UX` |
| UI | 8 | matches `UI` |
| GOV | 7 | matches `GOV` |
| AUTO | 6 | matches `AUTO` |
| HOME | 6 | matches `HOME` |
| SHOP | 6 | matches `SHOP` |
| A11Y | 5 | matches `A11Y` |
| I18N | 5 | matches `I18N` |
| MOBILE | 5 | matches `MOBILE` |
| OBS | 5 | matches `OBS` |
| PLUGIN | 5 | matches `PLUGIN` |
| QA | 5 | matches `QA` |
| REL | 5 | matches `REL` |
| SEC | 5 | matches `SEC` |
| INV | 3 | matches `INV` |
| LEARN | 3 | matches `LEARN` |
| AUTO-MECH | 2 | matches `AUTO-MECH` |
| CORE | 2 | matches `CORE` |
| DOCAPP | 2 | matches `DOCAPP` |
| HW | 2 | matches `HW` |
| AI | 1 | matches `AI` |
| INTEL | 1 | matches `INTEL` |
| KB | 1 | matches `KB` |
| LANG | 1 | matches `LANG` |
| PERIPH | 1 | matches `PERIPH` |
| (no `RM-` prefix) | 8 | n/a |

**Total**: 611 issues; 603 RM-prefixed; 8 non-RM. Of the 603,
**573 will be auto-labeled** (95.0%); **30 (`CI` + `DEPLOY` +
`MON`)** require the unmatched-prefix decision; **8 non-RM** are
out-of-scope by definition.

### Implementation choice

**Recommend: `framework/plane_connector.py`-based, conservative
pacing, hits the API.**

| Path | Pros | Cons |
|---|---|---|
| API via `plane_connector.py` | preserves audit trail (every edit logged at API layer); idempotent retries; respects 429 backoff already coded in connector | slow — at 1 req/sec the 573-issue back-fill takes ~10 min, plus retries |
| Direct DB write | fast (~10 sec) | bypasses Plane's audit/notification machinery; risk of FK constraint surprises; harder to roll back |

API path is doctrine-aligned. Block 4.B addendum confirmed
issues-rooted endpoint has a longer-window throttle on top of
60/min — the script will start at 1 req/sec and exponential-back
off to 1/min on 429. Estimated wall-clock 10–15 min if no 429s,
up to 30–60 min with backoff.

If the script projects >4 hours, the plan's risk-register entry
says stop and surface for direct-DB alternative. With the
current rate-limit posture I expect well under that.

### Unmatched-prefix decision (USER CHOICE at gate)

**The plan listed two options; I'm surfacing a third near-neighbor
mapping option that matches the data.**

| Option | Behavior | Effect |
|---|---|---|
| (a) Skip-and-surface | leave the 30 issues unlabeled; report them | keeps Plane label taxonomy clean; preserves user discretion; 30 issues stay un-prioritized |
| (b) Auto-create labels | create `CI`, `DEPLOY`, `MON` labels in Plane and apply | full coverage; introduces 3 new labels duplicating intent of existing ones |
| (c) **Map-to-near-neighbor** | `CI` → `CI/CD`; `DEPLOY` → `Deployment`; `MON` → `MONITOR` | full coverage; uses existing labels; one-time canonicalization decision |

My recommendation: **(c) map-to-near-neighbor**, because:
- All 3 unmatched prefixes have semantically obvious existing
  labels.
- Users who created `RM-CI-NNN` issues clearly meant CI (which is
  what `CI/CD` covers).
- Fewer labels ≈ better signal-to-noise.

But this is a one-way decision affecting taxonomy, so it warrants
explicit user choice.

---

## C1 — User-decision summary (the gate)

I need user approval on the following before C2 begins:

| # | Decision | Recommendation | Default if I proceeded blind (do not) |
|---|---|---|---|
| 1 | NetBox base image | `netbox-community/netbox-docker:v4.1.x` (latest stable 4.x — exact tag at C2.5) | recommended |
| 2 | NetBox Postgres topology | dedicated `netbox-postgres` (1g mem) | recommended |
| 3 | Caddy hostname | `netbox.internal` | recommended |
| 4 | Dependency modeling | NetBox native `ipam.service` cross-references | recommended |
| 5 | Duplicate `uptime-kuma` ID resolution | de-dupe at C3 migration time, log the decision | recommended |
| 6 | Plane back-fill execution path | `framework/plane_connector.py` with 1 req/sec floor | recommended |
| 7 | Unmatched-prefix policy (`CI`, `DEPLOY`, `MON`; 30 issues) | (c) map-to-near-neighbor: `CI`→`CI/CD`, `DEPLOY`→`Deployment`, `MON`→`MONITOR` | none — must choose |

**Architectural concerns surfaced from the audit**:
- The `credentials` field type-mixing (Finding B) is a pre-existing
  data-quality issue, not introduced by this block; C3 will
  normalize it.
- The two-pattern credentials modeling (`credentials` vs
  `credentials_env`, Finding C) is preserved as-is in C3 to keep
  scope tight; consolidating both into one NetBox field is a
  follow-up for a future block (likely 4.D or 4.E).
- `host: ha-device` and `host: opnsense` will be modeled as NetBox
  Devices, not Services. This is the cleanest representation but
  means the NetBox object-type is split: most services become
  `ipam.service` records hosted on the Mac Mini cluster; two
  become `dcim.device` records. The migration script handles this
  bifurcation explicitly.

**No findings exceed the plan's anticipated scope.** The Block 4.B
discrepancies in counts (47 vs 48 prefixes; 604 vs 611 issues; 64
vs 66 labels) are reconciled and explained above; the 3 unmatched
prefixes are the same `CI`/`DEPLOY`/`MON` set the plan called out.

🛑 **GATE C1 — awaiting user approval on the 7 decisions above.**

The audit doc, decision matrix, and full prefix table are now on
record. C2 (NetBox deployment) will not start until the user
approves.
