# Stack Architecture Audit — 2026-05-01

**Audit type:** Stack-level (NOT tool-by-tool)
**Trigger:** Operator skepticism after Plane misfit discovery; concern that prior individual-tool evaluations created overlap and gaps invisible at the stack level
**Status:** Promoted to repo 2026-05-01 as deliverable 17.A. Layer 8 verdict revised under D#20 (capability evidence) — original "retire Zabbix" recommendation reversed.

---

## 0. Audit framework (fixed before findings)

### Job-to-be-done

The platform is a self-hosted, AI-queryable, integrated life platform where any agent (current or future) can answer questions about state, history, and capabilities through unified interfaces — and where automating a new domain (fitness, media, home, code) means adding services that participate in this knowledge layer, not building parallel islands.

### Stack-level questions

For each layer:
1. Does this layer have ONE authoritative source, or multiple?
2. Is this layer queryable by agents (MCP/API), or human-UI-only?
3. Does this layer feed cross-cutting glue (xindex/MCP)?
4. Does this layer participate in repo→operational sync (ADR-A-006)?
5. Does this layer have a formal name in the PMP+ITIL framework?
6. **The big one: if I built a new agent tomorrow, could it answer "what is the state of X" through ONE call, or does it need to know which of N tools to ask?**

### Layers

1. Identity and secrets
2. Network and TLS
3. CMDB and inventory
4. Knowledge and decisions
5. Project and change management
6. Component inventory
7. Personal cloud
8. Observability
9. AI inference
10. Backup and recovery
11. Media
12. Smart home
13. Agent / chat UIs
14. Cross-cutting glue

---

## 1. Findings by layer

### Layer 1 — Identity and secrets

**Tools:** vault-server, seal-vault, vault-test, vaultwarden

**Verdict: HEALTHY, well-architected.**

Vault for infra secrets, Vaultwarden for user passwords. Clean role separation. seal-vault provides transit auto-unseal. vault-test is the rehearsal instance from D-15-06. AppRole-per-service pattern across the platform. No alternative consideration warranted.

**Gap:** none significant.

---

### Layer 2 — Network and TLS

**Tools:** Caddy, Headscale, OPNsense (separate hardware)

**Verdict: HEALTHY core, ONE persistent gap.**

Caddy auto-internal-TLS with 31 .internal sites. Headscale VPN. OPNsense firewall hardware-isolated.

**Gap (recurring across deliverables):** Caddy ↔ OPNsense Unbound DNS parity. xindex.internal, mcp-xindex.internal, netbox.internal all have Caddy site blocks but no Unbound A-record. D-16-06 nightly check is advisory-only because CI runner cannot query OPNsense.

**Recommendation:** Phase 17 should include OPNsense API integration (17.I). Makes the parity check enforced rather than advisory.

---

### Layer 3 — CMDB and inventory

**Tools:** NetBox + 5 supporting containers

**Verdict: RIGHT TOOL, but layer has a quiet duplicate.**

NetBox is correct: agent-queryable, ADR-A-014 ratified, GraphQL+REST, custom fields, mature.

**Quiet overlap with topology-api (port 8090):** topology-api is a separate FastAPI service that ALSO exposes service inventory. It predates xindex's NetBox ingestion (D-16-02.1) which now provides the same data via xindex_get_service. Risk: agent does not know which to query. Drift between topology-api and NetBox is silent.

**Recommendation:** Phase 17 deliverable to evaluate topology-api's remaining role (17.G). Likely retire or merge with xindex.

---

### Layer 4 — Knowledge and decisions

**Tools:** Repo (canonical, ADR-A-006), xindex, mkdocs, structurizr

**Verdict: STRONG core, distinct audiences.**

Repo + xindex + xindex-mcp = the knowledge surface. Working as intended after Phase 16 cross-index work. ADR-A-006 makes repo authoritative; xindex is the projection.

**Apparent redundancy of mkdocs + structurizr + xindex** — actually distinct audiences:
- mkdocs = humans browsing
- xindex = agents querying
- structurizr = architecture visualization
- NOT a real duplication.

**Concerning observation:** Structurizr cloud service has EOL of 2026-09-30 per startup logs. Self-hosted Structurizr OnPremises is the right path; verify the deployment is not cloud-tethered before Phase 17 17.R work depends on it.

---

### Layer 5 — Project and change management

**Tools:** Plane (7 containers, 1.5GB RAM)

**Verdict: WRONG TOOL FOR THIS STACK.**

Migration to OpenProject scoped at ~13-15h.

**Stack-level reasons (beyond original tool-vs-tool analysis):**

- **AI-queryability:** Plane API rate limits (60/min) are already a known operational pain point in the cross-index work. OpenProject API is more permissive.
- **Work-package native:** OpenProject has "work packages" as a first-class concept (matching your WP-NN-MM-XX framework). Plane has "issues" as the only primitive.
- **Change records:** OpenProject has built-in change management workflow. Plane does not. Your CR-NN-NNN framework is currently un-modeled in Plane.
- **xindex integration:** D-16-02.2 (Plane source) works but the schema mapping is constrained by Plane's flat issue model. OpenProject's richer model would let xindex expose deliverables, work packages, and change records as distinct queryable kinds.

**The OpenProject migration is not just a tooling preference — it is a stack-level correctness fix.** Scoped as Phase 17 deliverable 17.D.

---

### Layer 6 — Component inventory

**Tools:** InvenTree (4 containers)

**Verdict: RIGHT TOOL, deployment incomplete (D-16-01 known gap).**

InvenTree purpose-built for parts/components/3D models. Has API; xindex integration possible. D-16-01 closes the deployment closeout doc; real-data population is Phase 17+.

No alternative considered worthwhile. InvenTree is the open-source standard for this category.

---

### Layer 7 — Personal cloud

**Tools:** Nextcloud + nextcloud-db

**Verdict: RIGHT TOOL.**

Files, calendar (CalDAV master per locked architecture), contacts. Mature, agent-API-queryable. No alternative consideration warranted.

---

### Layer 8 — Observability

**Tools running:** Grafana, VictoriaMetrics (vm + vmagent), Loki + Promtail, Zabbix (5 containers + TimescaleDB), Uptime-Kuma, cAdvisor, node-exporter

**Verdict: ROLE-CLARIFICATION NEEDED — NOT over-provisioned (verdict revised under D#20).**

The first draft of this audit recommended retiring Zabbix as redundant
with VictoriaMetrics. Under D#20 (capability evidence required for
retirement recommendations), that recommendation was probed against
the running Zabbix instance and reversed:

| Capability | Zabbix evidence | VM/Prom equivalent |
|---|---|---|
| SNMP polling | 4,593 SNMP items active across network gear | None native (snmp_exporter is per-target manual config) |
| JMX polling | 510 JMX items active on Java services | None native |
| Host coverage | 55 distinct hosts monitored | node-exporter requires per-host install |
| Trigger expressions | Native multi-condition trigger DSL | Promql + Alertmanager (different model) |

**Zabbix and VictoriaMetrics serve different jobs.** Zabbix is the
agent/SNMP/JMX network-and-device monitor (its historical strength);
VictoriaMetrics is the container/host metrics + Grafana time-series
backend. The Phase 14 D-ZBX bridge correctly brings Zabbix data into
the VM/Grafana surface — that is integration, not duplication.

**Recommendation 17.E (revised):** Document the role split, fix any
broken bridge state, audit narrow overlap on host metrics where both
stacks may scrape the same node. **Not a retirement deliverable.**

Loki + Promtail and Uptime-Kuma have distinct roles (logs and uptime probing). Not duplicated.

---

### Layer 9 — AI inference

**Tools:** Ollama (host), LiteLLM Gateway, AnythingLLM, Open WebUI

**Verdict: HEALTHY. Roles are distinct when read carefully.**

- Ollama = inference runtime
- LiteLLM = router/gateway
- AnythingLLM = RAG + document workspace (per RM-KB-001 role matrix)
- Open WebUI = primary chat UI (per LLM Access Doctrine)

No duplication. Phase 17 work (Gemma 4, Qwen3-Coder evaluation, Cisco Provenance Kit) operates within this layer cleanly.

NOTE: AnythingLLM appears in BOTH this layer (RAG role) and Layer 13 (chat UI surface). Verify usage data before retiring it as part of 17.F — its role here is real if used.

---

### Layer 10 — Backup and recovery

**Tools:** Restic, MinIO@QNAP, MinIO (in Plane stack), backup AppRole

**Verdict: HEALTHY core.**

Restic + MinIO@QNAP correct. ADR-A-017 just ratified warm-copy. D-16-04 just landed.

**Quiet overlap:** Plane stack ships its OWN MinIO container (`docker-plane-minio-1`) for issue attachments. Total platform now has TWO MinIO instances. The Plane MinIO retires when Plane is replaced (17.D). Symptom of Plane being wrong tool, not real architectural duplication.

---

### Layer 11 — Media

**Tools:** Sonarr, Radarr, Prowlarr, Plex (external), plex-mcp, Sportarr

**Verdict: HEALTHY, with one orphan.**

*arr stack standard pattern. plex-mcp is the agent integration.

**Orphan:** Sportarr logs show "Maximum retries... URL Fetching failed" continuously — actively broken. Per memory: "config issue not removable" — but it is clearly malfunctioning. Phase 17 deliverable (17.H) to fix or retire — apply 17.B capability template before deciding.

---

### Layer 12 — Smart home

**Tools:** Home Assistant (separate hardware)

**Verdict: HEALTHY.** Correctly isolated.

---

### Layer 13 — Agent / chat UIs (THE BIGGEST FINDING AFTER PLANE)

**Tools running:** Open WebUI, AnythingLLM, obot, openhands-app, mcpo-proxy, sms1obot-mcp-server, sms1obot-mcp-server-shim, structurizr (also a UI), homarr, homepage, ai-platform-dashboard, mkdocs

**Verdict: SEVERE OVERLAP. The layer with most accumulated cruft.**

**Three dashboards:**
- homarr (specialized arr-stack dashboard)
- homepage (services + bookmarks + docker + widgets)
- ai-platform-dashboard (self-healing platform monitor with healing cycles in logs)

Each is fine alone; together they create operator cognitive load.

**Multiple agent UIs:**
- Open WebUI — primary chat (locked decision)
- AnythingLLM — RAG / document workspace
- obot — additional agent platform; OBOT_DEV_MODE=false suggests production but role overlaps Open WebUI
- openhands-app — coding agent; LLM_MODEL=openai/qwen2.5-coder:32b
- sms1obot-mcp-server + shim — appears obot-related; presence suggests obot integration not fully retired

**Recommendation:** Phase 17 deliverable (17.F) for "agent surface consolidation." Apply 17.B capability template per tool:
1. Audit obot's actual usage. If overlaps Open WebUI, retire.
2. Audit openhands-app — if Claude Code + xindex-mcp serves the same use case, retire.
3. Reduce dashboards to ONE (homepage seems most general; homarr is specific to *arr stack — fold into homepage).
4. AnythingLLM — verify RAG usage; if nobody queries it, retire.

This is the layer with the most "kept around because it was installed" decisions.
**Audit actual usage data (last login, last query) before retiring anything — D#20.**

---

### Layer 14 — Cross-cutting glue (THE LAYER THAT MATTERS MOST)

**Tools:** xindex, xindex-mcp, mcp-docker-remote, mcp-docs-remote, mcp-filesystem-remote, mcpo-proxy

**Verdict: HEALTHY, BUILT RIGHT — Phase 16 work delivered exactly what the stack needed.**

xindex aggregates ADRs, runbooks, decision register, NetBox services, NetBox nodes, Plane issues. xindex-mcp wraps for native agent calls. MCP-* containers expose Docker, filesystem, docs operations.

**This layer is the answer to "the AI knowledge layer needs to be queryable."** The cross-index work (D-16-02 chain) was correctly prioritized. 17.Q and 17.R extend cleanly.

---

## 2. Stack-level findings (cross-cutting)

### Finding 1 — TWO categories of "evaluated individually" damage

- **Plane (Layer 5):** Migration to OpenProject ~13-15h (17.D).
- **Agent UIs (Layer 13):** ~10-15h to audit usage and retire surfaces (17.F). Lower urgency than Plane.

### Finding 2 — Observability role-clarification (REVISED under D#20)

The first draft called Zabbix + VictoriaMetrics "one stack too many."
That recommendation was reversed after capability probing — see Layer 8.
The actual deliverable (17.E) is role documentation + bridge fix +
narrow-overlap audit, not retirement. ~3-5h.

### Finding 3 — Knowledge layer is the SUCCESS pattern

The cross-index work is the right model. Future deliverables ASK:
"does this participate in xindex?" before adding any new service —
codified as D#18.

### Finding 4 — No silent gaps

After auditing, no layers are missing critical capabilities. The 66 containers cover the full integrated-life platform scope. **The problem is overlap, not gaps.**

---

## 3. Recommendations (by Phase 17 deliverable)

| ID | Scope | Effort |
|---|---|---|
| 17.D | Replace Plane with OpenProject (Layer 5) | ~13-15h |
| 17.E | Observability role-clarification (Layer 8 — NOT retirement) | ~3-5h |
| 17.F | Agent surface consolidation (Layer 13) | ~10-15h |
| 17.G | topology-api evaluation (Layer 3) | ~3-5h |
| 17.H | Sportarr fix-or-retire (Layer 11) | ~2-4h |
| 17.I | OPNsense API integration (Layer 2) | ~6-8h |

Doctrine codification (D#18, D#19, D#20, D#21) lives in PROJECT_FRAMEWORK.md §3.5 — see 17.T.

---

## 4. Summary table

| Layer | Tools | Verdict | Action |
|---|---|---|---|
| 1 Identity | Vault + Vaultwarden | HEALTHY | none |
| 2 Network | Caddy + Headscale | HEALTHY core | 17.I |
| 3 CMDB | NetBox | HEALTHY | 17.G |
| 4 Knowledge | Repo + xindex + mkdocs + structurizr | HEALTHY | none |
| 5 PM/change | Plane | **WRONG** | **17.D** |
| 6 Component | InvenTree | HEALTHY | (D-16-01 closed) |
| 7 Personal cloud | Nextcloud | HEALTHY | none |
| 8 Observability | VM/Grafana + Zabbix | ROLE-CLARIFICATION NEEDED | **17.E (NOT retirement)** |
| 9 AI inference | Ollama + LiteLLM + AnythingLLM + Open WebUI | HEALTHY | none |
| 10 Backup | Restic + MinIO@QNAP | HEALTHY | none |
| 11 Media | *arr + Plex + plex-mcp | HEALTHY | 17.H |
| 12 Smart home | Home Assistant | HEALTHY | none |
| 13 Agent UIs | obot + openhands + 3 dashboards + chat UIs | **OVERLAPPING** | **17.F** |
| 14 Cross-cutting glue | xindex + MCP servers | HEALTHY (success pattern) | none |

**Net:** 1 wrong tool (Plane), 1 role-clarification need (observability), 1 surface bloat (agent UIs), 1 broken orphan (sportarr), 1 architectural drift candidate (topology-api). Everything else is on the right track.

---

## 5. The honest meta-finding

**The stack is mostly correct.** The cross-index work has actually paid off — Layer 14 makes Layers 1-13 queryable and that is the whole point.

The two real corrections (Plane and agent UI consolidation) are exactly the kinds of "evaluated individually" mistakes the operator named in the audit request. Catching them now, before 17.Q/17.R build on these surfaces, is the right move.

The Layer 8 reversal is itself the meta-lesson. The first draft pattern-matched two metrics tools as redundant; the D#20 probe surfaced 4,593 SNMP items + 510 JMX items + 55 hosts that one of them carries and the other cannot. That is the exact failure mode D#20 codifies: vibes-based retirement recommendations get rejected at audit review unless the capability evidence supports them.

The proposed D#18/D#19/D#20/D#21 doctrine additions exist specifically to prevent this class of finding from accumulating again.
