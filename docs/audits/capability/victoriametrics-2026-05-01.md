# Capability Audit — VictoriaMetrics

**Date:** 2026-05-01
**Auditor:** Claude session (operator-reviewed)
**Trigger:** 17.E observability role-clarification — peer audit to
the 17.B Zabbix audit, so the role-split doctrine has evidence on
both sides of the boundary.

---

## Section 1 — Tool identification

- **Name:** victoriametrics (canonical CMDB grouping)
- **Deployment location:** Docker on Mac Mini, 4 containers in the
  `control-center-net` stack:
  - `vm`            (victoriametrics/victoria-metrics:v1.99.0) —
    storage + query engine; `:8428`
  - `vmagent`       (victoriametrics/vmagent:v1.99.0) — scrape +
    forward; `:8429`
  - `node-exporter` (prom/node-exporter:v1.7.0) — host metrics
  - `cadvisor`      (zcube/cadvisor:latest) — container metrics
- **Version:** 1.99.0 series
- **Source:** `~/control-center-stack/stacks/observability/...`
  (out-of-repo per CLAUDE.md note)
- **First deployed:** Phase 7 (container hardening + monitoring
  baseline)
- **Current resource cost:** modest (single VM container is the
  largest; vmagent + node-exporter + cadvisor are small)

---

## Section 2 — Probed capabilities (NOT documented capabilities)

Probes against the running `vm` (`:8428`) and `vmagent` (`:8429`)
on 2026-05-01.

### 2.1 — Time-series storage

**Probe:** `curl :8428/api/v1/series/count`
**Output:** `170752`

That's the total series cardinality across all scraped jobs over the
retained window. Active `count({__name__!=""})` returns 10,102 —
the in-memory hot set.

### 2.2 — PromQL query engine

**Probe:** `curl ':8428/api/v1/query?query=count({__name__!=""})'`
**Output excerpt:**
```
{"status":"success","data":{"resultType":"vector","result":[
  {"value":[1777680334,"10102"]}]},"stats":{"seriesFetched":"10102"}}
```

VictoriaMetrics speaks PromQL; Grafana queries it as a Prometheus-
compatible source.

### 2.3 — Active scrape jobs (vmagent)

**Probe:** `curl :8429/api/v1/targets`
**Output excerpt:**
```
caddy:           1 target,  health=up
cadvisor:        1 target,  health=up
mcp-docs:        1 target,  health=down
node-exporter:   1 target,  health=up
zabbix-exporter: 1 target,  health=up
vmagent:         1 target,  health=up
```

Six scrape jobs. mcp-docs target is currently down — separate
follow-up (not 17.E scope). zabbix-exporter target is the bridge
audited in 17.B / decided in 17.E §below.

### 2.4 — What each scrape job collects

- **caddy**: reverse-proxy metrics — request rate, status codes,
  upstream health, TLS handshake duration. Backs the per-site
  dashboard set up in Phase 14 D-LOG.
- **cadvisor**: per-container CPU/memory/network/disk on Mac Mini
  Docker. Mac-side cgroup-mapping limitation (CLAUDE.md
  "Known Hardening Trade-offs") means container labels only carry
  hash IDs, not friendly names.
- **node-exporter**: host-level CPU, load, memory, disk, network on
  the Mac Mini (`node_*` metric set).
- **mcp-docs**: documentation MCP service exposition (down — separate
  follow-up).
- **zabbix-exporter**: Zabbix → Prometheus bridge (2 metrics:
  trigger counts by severity, host availability counts).
- **vmagent**: self-monitoring (vmagent's own scrape latencies,
  errors, queue depth).

### 2.5 — Available but not exercised

- **Remote-write** (vmagent → external long-term storage like
  Mimir/Cortex): not used; retention is local.
- **Multi-tenancy** (`vmselect`/`vmstorage` cluster mode): not
  deployed; single-node `vm` container is sufficient at current
  cardinality.
- **Alerting (`vmalert`)**: not deployed; Grafana alerting handles
  this for Prometheus-side rules.

These are noted but not counted as evidence for KEEP — they're
capabilities held in reserve.

---

## Section 3 — Stack-coverage check

For each load-bearing capability from Section 2:

### 3.1 — Time-series storage with PromQL

- **What other tool in the stack covers this?**
  - Zabbix has its own time-series store (TimescaleDB-backed) but
    speaks Zabbix's expression language, not PromQL.
  - Loki stores logs, not metrics; LogQL is for log lines.
  - Uptime-Kuma stores synthetic-probe state, not arbitrary
    time-series.
- **Verdict:** UNIQUE. PromQL-native time-series with Prometheus
  exposition compatibility has no other home in this stack.

### 3.2 — Container metrics (cAdvisor)

- **What other tool covers this?** Nothing else collects per-cgroup
  Docker container CPU/memory/network. Zabbix could in principle
  (with a docker template) but doesn't here.
- **Verdict:** UNIQUE in current configuration.

### 3.3 — Host metrics (node-exporter)

- **What other tool covers this?** Zabbix-agent on mac-mini collects
  ~706 type-0 items that overlap heavily (CPU load, swap, proc count,
  context switches, boot time, hostname — see 17.E
  observability-doctrine §"Narrow overlap").
- **Verdict:** OVERLAPPING. The 706 items are the queued cleanup
  from the 17.B Zabbix audit; this audit confirms node-exporter is
  the cleaner home for those items in this stack.

### 3.4 — PromQL exposition for arbitrary services

- **What other tool covers this?** Nothing. If a service emits
  Prometheus metrics, vmagent + vm is the only path that reaches
  Grafana via PromQL.
- **Verdict:** UNIQUE.

### 3.5 — Synthetic uptime probing

- **What other tool covers this?** Uptime-Kuma — and Uptime-Kuma is
  cleaner here (purpose-built UI, status pages, notification
  integrations). vm/vmagent CAN be used for blackbox-exporter style
  probing but isn't deployed that way.
- **Verdict:** Uptime-Kuma owns this; not a VictoriaMetrics role.

---

## Section 4 — Verdict

**KEEP** — unique role.

VictoriaMetrics owns the Prometheus-side metrics path: container
metrics, host metrics, service-exposed `/metrics` endpoints, ad-hoc
PromQL query, time-series retention. No other tool in the stack
covers PromQL-native time-series storage. The role is durable.

The role split between VictoriaMetrics and Zabbix is codified in
`docs/runbooks/observability-doctrine.md` (17.E output).

---

## Section 5 — Migration plan

N/A — verdict is KEEP.

---

## Section 6 — Decision log

- **Auditor:** Claude session
- **Date:** 2026-05-01
- **Verdict reviewed by operator:** yes (17.E parent deliverable)
- **Source of capabilities probed:**
  - `curl :8428/api/v1/series/count` (cardinality)
  - `curl :8428/api/v1/query?query=count({__name__!=""})` (active set)
  - `curl :8429/api/v1/targets` (scrape jobs + health)
  - `docker ps` for container set
- **Linked artifacts:**
  - D#20 (capability evidence requirement) — peer audit to
    `docs/audits/capability/zabbix-2026-05-01.md`
  - D#21 (three-plane audits) — capability plane evidence
  - 17.B (template + Zabbix worked example)
  - 17.E (observability doctrine consuming this audit)
  - `docs/runbooks/observability-doctrine.md` (canonical role-split)
