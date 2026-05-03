# Capability Audit — topology-api

**Date:** 2026-05-01
**Auditor:** Claude session (operator-reviewed)
**Trigger:** Stack audit (D-17-01) flagged topology-api as a "quiet
duplicate" of NetBox + xindex_get_service. D-17-07 applies the D-17-02
template to render an evidence-based verdict.

---

## Section 1 — Tool identification

- **Name:** topology-api
- **Deployment location:** Docker on Mac Mini (control-center-net),
  in-repo compose at `docker/topology-api/docker-compose.yml`.
- **Version:** `iap/topology-api:1.1.0` (compose); xindex/NetBox
  service record claims `1.0.0` — small drift, separate cleanup.
- **Source:** `docker/topology-api/server.py` (~190 lines, stdlib
  HTTP server + `cmdb_source` shared module).
- **First deployed:** Phase 13 Block 4.C C5.2b (the YAML→NetBox
  registry transition). Origin commit traceable via
  `git log --grep="topology-api"`.
- **Current resource cost:** 11.12 MiB / 64 MiB limit (17%), 0.01% CPU,
  1 PID. Negligible.

---

## Section 2 — Probed capabilities

Probes against the running instance on 2026-05-01 against `:8300`.

### 2.1 — Endpoint surface

Probed by reading `server.py` and `curl`-ing each path:

```
GET /health                  → 200 {"ok": true, "source": "yaml",
                                    "registry": "/config/...DEPRECATED"}
GET /api/topology/nodes      → 200 [<node>, ...]
GET /api/topology/edges      → 200 [<edge>, ...]
GET /api/topology  (and /)   → 200 {"nodes": [...], "edges": [...],
                                    "service_count": 75,
                                    "edge_count": 72}
```

There is no OpenAPI document — the surface is small and hand-coded.

### 2.2 — Output shape (the load-bearing part)

Each node carries Grafana-Node-Graph-panel-shaped fields:

```json
{
  "id":            "anythingllm",
  "title":         "AnythingLLM",
  "subtitle":      "ai",                  # category
  "mainStat":      "3004",                # port (string!)
  "secondaryStat": "mac-mini",            # host
  "color":         "#7c3aed",             # category-mapped color
  "arc__primary":  1.0,                   # arc-segment for Node Graph
  "detail__purpose":   "...",
  "detail__container": "anythingllm",
  "detail__image":     "mintplexlabs/anythingllm:latest"
}
```

Each edge:

```json
{ "id": "src->dst", "source": "src", "target": "dst", "mainStat": "depends" }
```

### 2.3 — Capabilities, evidenced

1. **Service inventory projection** — reads NetBox or YAML, returns
   75 services. *Probe:* `curl :8300/api/topology | jq '.service_count'`
   → `75`.
2. **Dependency edge computation** — walks each service's
   `depends_on` list, emits edge objects only when the target id
   exists in the node set. *Probe:* `service_count=75`,
   `edge_count=72`. The edges are computed here, not stored in the
   CMDB.
3. **Grafana-Node-Graph adapter** — produces the exact field shape
   (`mainStat`, `secondaryStat`, `arc__primary`, `detail__*`) the
   Grafana Node Graph panel consumes via the JSON / Infinity data
   sources. *Probe:* `docker/grafana-provisioning/dashboards/topology.json`
   panels reference `urlPath: /api/topology` and
   `/api/topology/nodes`.
4. **Category → color mapping** — 13 category colors hard-coded in
   `CATEGORY_COLOR`. Not a CMDB field; an enrichment.
5. **Backend-agnostic source** — `cmdb_source.load_services()`
   speaks both `yaml` and `netbox` modes; output is byte-identical
   for the same data (per `scripts/cmdb-equivalence.sh`).

### 2.4 — Configuration drift (probed)

- **`CMDB_SOURCE=yaml`** is the live setting; the registry path is
  `/config/service-registry.yaml.DEPRECATED`. CLAUDE.md (Phase 14
  D-DOC) declares `CMDB_SOURCE` default is now `netbox`. Compose
  default `${CMDB_SOURCE:-yaml}` was missed in the D-DOC sweep.
- **Image tag drift:** running `iap/topology-api:1.1.0`, NetBox/xindex
  service record claims `1.0.0`. Tracked separately.

### 2.5 — Available but not exercised

- **`control-plane.app.config.topology_api_url`** is defined but not
  referenced anywhere in `docker/control-plane/`. Orphan config.
  Not a topology-api capability — a dead pointer in a consumer.

---

## Section 3 — Stack-coverage check

For each capability from Section 2:

### 3.1 — Service inventory projection

- **What other tool covers this?** `xindex /service/{name}` returns
  the same service record (richer, in fact — adds `service_dependencies`,
  `health_url`, `security_profile`, `compose_file`).
- **Cleaner where?** Mixed. xindex covers single-service lookups
  cleanly. topology-api's `/api/topology` returns the *whole graph*
  in one request — xindex doesn't have a bulk endpoint of equivalent
  shape.

### 3.2 — Dependency edge computation

- **What other tool covers this?** None.
  - NetBox stores `service_dependencies` per service, but doesn't
    emit a graph-level edge list.
  - xindex `/links` covers ADR↔Plane↔runbook links, not service-to-
    service `depends_on` relationships.
  - There is no other place in the stack that turns the per-service
    `depends_on` lists into a graph edge set.
- **Verdict:** UNIQUE.

### 3.3 — Grafana-Node-Graph adapter

- **What other tool covers this?** None. The Node Graph panel needs
  exact field names (`mainStat`, `secondaryStat`, `arc__primary`,
  `detail__*`); no other service in the stack emits that shape.
- **Verdict:** UNIQUE. This is the load-bearing capability — the
  reason topology-api exists.

### 3.4 — Category → color mapping

- **What other tool covers this?** None. The mapping is
  visualization-policy, not CMDB data; would need to live somewhere.
- **Verdict:** Minor; could move to Grafana panel config, but trivial
  benefit.

### 3.5 — Backend-agnostic source loader (`cmdb_source.py`)

- **What other tool covers this?** N/A — this IS the shared loader,
  used by topology-api itself and by host-side CLI scripts. Not a
  duplicate of anything.

---

## Section 4 — Verdict

**KEEP WITH ROLE-CLARIFICATION + reconfig.**

The "quiet duplicate" framing in the D-17-01 audit was wrong. topology-
api is **not** a NetBox/xindex replicate — it's a **Grafana Node
Graph adapter** that sits on top of the same data. Its load-bearing
capabilities (dependency-edge computation, Node-Graph field shaping,
the `/api/topology` whole-graph endpoint) have no cleaner home in
the current stack.

### Role clarification

Going forward:
- **NetBox owns:** authoritative service inventory.
- **xindex owns:** single-service lookups + cross-source linking
  (ADR↔Plane↔runbook).
- **topology-api owns:** graph-shaped projection of the inventory
  for Grafana Node Graph dashboards. Reads NetBox; emits
  Node-Graph-panel JSON; computes service→service edges from each
  service's `depends_on`.

### Reconfig required

Two follow-up corrections, NOT in D-17-07's commit (separate cleanups):

1. **Flip `CMDB_SOURCE` default to `netbox`** (compose +
   redeploy). The current `${CMDB_SOURCE:-yaml}` was missed in the
   Phase 14 D-DOC default-flip sweep. Effort: trivial; needs
   container restart, surfaces immediately if the NetBox-mode path
   is broken.
2. **Reconcile image tag drift** (running `1.1.0`, NetBox record
   says `1.0.0`). Update NetBox custom field; or rebuild image at
   the recorded version. Operator decision; not load-bearing.

These are documented here as follow-ups but **not executed in D-17-07's
commit** because they're not "audit verdict" actions — they're
ordinary maintenance unblocked by the verdict.

---

## Section 5 — Migration plan

N/A — verdict is KEEP WITH ROLE-CLARIFICATION.

---

## Section 6 — Decision log

- **Auditor:** Claude session
- **Date:** 2026-05-01
- **Verdict reviewed by operator:** yes (D-17-07 surfaced verdict
  before any container action)
- **Source of capabilities probed:**
  - `docker stats topology-api --no-stream` (resource cost)
  - `curl :8300/health`, `:8300/api/topology`, `:8300/api/topology/nodes`,
    `:8300/api/topology/edges` (endpoint surface)
  - `docker/topology-api/server.py` (source-code reading for
    capability enumeration)
  - `grep -rE 'topology-api|:8300|/api/topology'` (consumer
    enumeration)
- **Linked artifacts:**
  - D-17-01 stack audit (the "quiet duplicate" claim this audit
    reverses)
  - D-17-02 (template)
  - D#20 (capability evidence)
  - `docker/grafana-provisioning/dashboards/topology.json` (the
    consumer that justifies KEEP)
- **Follow-ups (not in D-17-07 commit):**
  1. Flip compose `CMDB_SOURCE` default to `netbox`
  2. Reconcile `1.1.0` vs `1.0.0` image tag
