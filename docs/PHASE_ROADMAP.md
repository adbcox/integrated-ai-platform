# Platform Roadmap — Consolidated Phase Structure

**Last updated:** 2026-04-30
**Current state:** Phase 15 Blocks A–G complete. Phase 13 technically open (CL gate pending).
**Discovery numbering:** continues at #37+
**Regression baseline:** PASS=16 FAIL=0 WARN=3 (`phase-14-final`, tag `9acfe6e`)

---

## Completed phases (closed)

| Phase | Scope | Gate |
|---|---|---|
| 1–12 | Foundation, Vault, Caddy, Observability, Zabbix, NetBox Block 4 | Various |
| 13 (partial) | NetBox CMDB authority, Increment 1 doctrine, 2A InvenTree deploy, Block 3 HA/voice, Increment 1.5 §6/§7 hardening | `increment-2a-final` (2B–CL open) |
| 14 | D-DOC, D-STR, D-MKD, D-ZBX, D-RST, D-LOG, D-XINDEX, NF-14-1/2, CL-14 | `phase-14-final` PASS=16 |
| 15 A–G | CF-1–4 carry-forwards, D-OP ADRs, D-CN connector hardening, Mac Studio day-1, 4.H upgrade-watcher, 4.J network discovery, Plane curation | (in progress) |

---

## Revised forward structure: 3 large phases

The remaining work partitions cleanly into three capability milestones.
Each is 80–150 hours and closes with a meaningful state the platform
didn't have before it opened.

---

## Phase 16 — Compute Expansion + Data Integrations

**Capability milestone:** Mac Studio is a productive AI/ML compute node.
InvenTree holds real supplier data and talks to Mouser/DigiKey. The
platform has a unified cross-index spanning NetBox + InvenTree + OpenProject + ADRs.
Phase 13 is formally closed.

> **Plane → OpenProject (D-17-04, 2026-05-01).** Items below that
> reference "Plane" as the project-management surface predate the
> retirement and are preserved as historical scope. Where the text
> describes still-active forward intent (Phase 16/17/18 prereqs,
> webhook receivers, cross-index members, Nextcloud Deck migration),
> read "Plane" as "OpenProject"; mechanical work to point the
> integrations at OpenProject is tracked under D-17-04 / D-17-09.

**Effort:** ~85–130h
**Hard prerequisites before opening:**
- Mac Studio physically present and Blocks D steps complete (2–3h day-1 work)
- Mouser API key, DigiKey OAuth, 129-component CSV (for Increment 2B block)

**Soft prerequisites (can execute in parallel):**
- Gmail OAuth for receipt ingestion
- Vision path decision (local llava vs claude-pro)

### 16.A — Mac Studio full compute stack (~12–18h)

Builds on Block D day-1. Delivers the Studio as a fully operational AI compute node.

**Scope:**
- Ollama on Studio: pull qwen2.5-coder:32b + llama3.3:70b + llava:13b + nomic-embed-text
  (~70GB total; schedule overnight pull)
- LiteLLM Gateway on Mini: add `studio-fast` (qwen2.5-coder:32b@Studio),
  `studio-large` (llama3.3:70b@Studio), `studio-embed` (nomic-embed-text@Studio) routes
- Caddy on Mini: `ollama-studio.internal`, `openhands-studio.internal` routes
- AnythingLLM: switch primary LLM backend to Studio Ollama (no network hop for large queries)
- OpenHands: run latency benchmark (Mini Ollama vs Studio Ollama); migrate if ≥20% improvement
- Node exporter on Studio → vmagent on Mini scrapes it → Grafana "Compute Nodes" panel
- Zabbix agent on Studio → Mini Zabbix server; "mac-studio" host registered
- Restic backup: include Studio application-state paths (exclude model blobs — re-pullable)
- Subagent pattern update: `decomposer` and `implementer` agents point to Studio Ollama endpoints
- CLAUDE.md LLM Access Doctrine: add studio-fast/studio-large routes; update subagent targets
- Regression probe section (i): Studio Ollama + node-exporter health → PASS count increases to 17

**Gate:** `phase-16-16A` — PASS=17 FAIL=0 WARN≤3.
Studio Ollama answers inference requests. Studio node-exporter metrics appear in Grafana.

---

### 16.B — InvenTree Suppliers + CSV + Cross-Index (~25–40h)

Closes the InvenTree arc begun in Increment 2A. Delivers the Phase 13 CL gate.

**Scope:**
- Vault policy update: add Mouser + DigiKey paths to `inventree-policy.hcl`
- Vault Agent template: render `MOUSER_API_KEY`, `DIGIKEY_CLIENT_ID`, `DIGIKEY_CLIENT_SECRET`
- InvenTree plugins: enable `inventree-supplier-panel` + `inventree-part-import` (already installed, not enabled)
- 129-component CSV import: first-batch-verify 10 parts, then bulk; ADR-A-012 equivalence harness
- Mouser integration: Mouser Electronics supplier, API key, SKU lookup test on 5 sample parts
- DigiKey integration: OAuth client_credentials flow, token refresh, stock-level lookup test
- NetBox cross-reference: `inventree_bom_url` custom field on `dcim.device`
- Cross-index service (4.E): extend `scripts/cross-index-validate.py` with InvenTree axis;
  find NetBox devices without BOM URLs; produce gap report
- 4.G Vision plugin: `inventree_vision_plugin` using llava:13b on Studio; photo → part match
- Gmail receipt ingestion (4.I): if Gmail OAuth arrives mid-phase, execute; otherwise stub
- Phase 13 CL closeout: final regression probe `phase-13-final`, tag `v13-final`, closeout doc

**Gate:** `phase-13-final` — PASS≥17 FAIL=0 WARN≤3. Phase 13 formally closed.
InvenTree has 129+ parts. Mouser + DigiKey integrations return live data. Cross-index clean.

**ADR-A-012 harness required:** CSV row count == InvenTree part count before CL gate.

---

### 16.C — Automation Integrations (~25–40h)

Autonomous write-side integrations: receipt ingestion, network discovery maturation,
upgrade watcher calibration.

**Scope:**
- Gmail receipt ingestion (4.I): if not done in 16.B, execute here with full pipeline
  (OAuth → Gmail API → LLM parse → InvenTree draft parts → operator review queue)
- Network discovery hardening (4.J): first run may have gaps; add hostname resolution,
  DNS PTR lookup, MAC vendor lookup; create NetBox Device stubs for discovered hosts
  not yet in dcim/devices; weekly launchd schedule
- Upgrade watcher calibration: Diun first-run results reviewed; tune watch schedule,
  filter out noisy base images (node:22, python:3.12-slim); verify Plane issue creation
  per image-update event
- Plane webhook receiver production-grade: add request authentication (shared secret),
  deduplication (don't create duplicate Plane issues for same image+tag), exponential
  backoff on 429
- Topology API extension: add cross-index endpoint (`/api/cross-index`) returning
  NetBox + InvenTree + Plane + ADR data in a single JSON response; power a Grafana
  "Platform State" text panel
- CLAUDE.md updates: document Studio Ollama routes, update container count (now 65+),
  record Phase 16 completion

**Gate:** `phase-16-final` — PASS≥17 FAIL=0 WARN≤3.
Phase 16 CLOSED. Platform has two compute nodes, supplier data, and autonomous write-side integrations.

---

## Phase 17 — Three-plane architecture corrections + local AI stack

> **Phase 17 was renumbered during Bundle A.5 (2026-05-01).** The
> original "Phase 17 — Health Stack + Long-Horizon Infrastructure"
> scope (a6253c3, bd6a844) is now Phase 18 (see below). The
> audit-surfaced architectural corrections in this Phase 17 must
> close before Phase 18 work can build on a clean foundation. See
> `docs/STACK_ARCHITECTURE_AUDIT_2026-05-01.md` for rationale and
> `docs/phase-17/PHASE_17_PLAN_2026-05-01.md` for the canonical
> 20-deliverable plan across 5 tiers.

**Capability milestone:** Stack-level architecture audited and
corrected. Per-tool capability template established. Plane replaced
by OpenProject. Agent surfaces consolidated. Local AI stack
matured behind a provenance gate.

**Effort:** ~75–110h across 20 deliverables (D-17-01–T).
**Canonical plan:** `docs/phase-17/PHASE_17_PLAN_2026-05-01.md`.
**Status (this file is a pointer; framework §9 is the live tracker):**
3 of 20 done at Bundle A.5 close (D-17-01, D-17-19, D-17-20).

Phase 17 is intentionally NOT expanded inline here — single source
of truth lives in the plan doc to avoid drift between two locations.

---

## Phase 18 — Health Stack + Long-Horizon Infrastructure

**Capability milestone:** Personal health data flows into VictoriaMetrics alongside
platform metrics. Threadripper/Linux arrives and joins the topology. Platform
evaluated against OpenBao and Backstage.

**Effort:** ~80–130h
**Hard prerequisites:**
- Oura OAuth client registered (`secret/oura/oauth` in Vault)
- Garmin auth path decided (garth / FIT export / Health API)
- BLE label printer hardware on hand (model confirmed)
- Linux/Threadripper physically present (for 18.C)

> **Scope notes from D-17-19 article-intake (awaiting specific 18.X parents):**
>
> *(a) License-aware Manyfold + Gitea LFS schema.* When a 3D-model
> database deliverable is scoped under Phase 18, the schema must
> include SPDX license ID per model, source URL + retrieval date
> for provenance, and license-compatibility checks at ingest.
> Manyfold as the cataloging surface; Gitea LFS as the binary
> store. See `docs/architecture-patterns/strategic-watch.md` for
> source-platform risk context.
>
> *(b) AI 3D generation license provenance.* If/when InstantMesh,
> TripoSR, or similar AI 3D-generation tools enter the platform,
> outputs must carry license provenance derived from the input
> training corpus (where known) and the operator's intended
> downstream use. Default to most-restrictive applicable license
> when corpus provenance is uncertain.

### 18.A — Health & Fitness Stack (~20–30h)

**Scope:**
- HF-1 Oura Ring 4: `scripts/oura-ingest.py` → VictoriaMetrics metrics
  (sleep score, readiness, activity, heart rate variability)
  Schedule: nightly launchd at 03:00. Grafana "Health & Fitness" dashboard.
- HF-2 Garmin Fenix/Edge: via `garth` SDK (preferred) or FIT file export pipeline
  (activity distance, duration, VO2max, resting HR) → same VictoriaMetrics target.
  Shared Grafana dashboard with HF-1 panels.
- BLE label maker (4.F): `scripts/print-inventree-label.py` using `framework/niimbot_printer.py`;
  print InvenTree part labels from CLI or InvenTree plugin action
- Health AI coach (stretch): AnythingLLM + Studio Ollama as a personal health coach;
  nightly context injection: "Sleep score: 78, Readiness: 65, Steps: 8,200 — recommendations?"
  Output to a daily digest file or Nextcloud note
- Oura + Garmin unified Grafana dashboard: combined panels, 30-day trends,
  correlation view (sleep quality vs activity score)

**Gate:** `phase-18-18A` — health metrics appearing in VictoriaMetrics;
Grafana health dashboard rendering. PASS count stable.

---

### 18.B — Linux/Threadripper Integration (~35–50h)

Adds the Threadripper + RTX 4070 as a GPU compute node. This is the
biggest topology change since the Mac Mini was the only node.

**Scope:**
- Linux node bootstrap: Docker (native, not Colima), Vault agent, Headscale client;
  IP assignment in OPNsense + NetBox dcim/devices
- GPU workload migration: Ollama on Linux (CUDA backend) for models where GPU
  inference beats Apple Silicon (primarily large batch jobs, not latency-sensitive inference);
  LiteLLM `gpu-fast` route pointing at Linux Ollama
- cAdvisor fix: on Linux Docker (not Colima), `name`/`image` labels populate correctly;
  remove `label_replace` workaround in Grafana; update CLAUDE.md known trade-off entry
- Per-host Vault config: `config/vault-configs/vault-config-linux.hcl` (already scaffolded);
  deploy Vault agent on Linux as a Vault client (Vault server stays on Mini)
- Zabbix: Linux host registered; "Linux servers" template; ICMP monitoring now works
  (NET_RAW available on real Linux); remove "unsupported" ICMP item documentation
- Observability: node-exporter on Linux → vmagent scrape → Grafana "Linux Compute" panel
- Restic: include Linux application-state paths in backup
- Regression probe section (j): Linux Ollama + node-exporter health → PASS count 18+
- ADR-A-017: GPU workload routing policy — when to prefer Linux/CUDA vs Mac/ANE
- Architecture diagram update: add Threadripper box to network map

**Gate:** `phase-18-18B` — Linux Ollama answers inference requests.
GPU inference benchmark vs Mac Studio documented.

---

### 18.C — Platform Evaluation + Hardening (~25–50h)

Long-horizon evaluation items and platform hardening that improve the
foundation rather than adding features.

**Scope:**
- OpenBao parallel-deploy evaluation: spin up OpenBao container alongside Vault;
  test API parity for AppRole + KV + Transit; document migration path;
  ADR-A-018: adopt/defer/skip OpenBao; no migration unless ADR says adopt
- Backstage re-evaluation: run Backstage in a container (30-day trial);
  compare against current NetBox + Structurizr + MkDocs trio;
  ADR-A-019: adopt/defer/skip Backstage; no migration unless ADR says adopt
- `service-registry.yaml.DEPRECATED` deletion: run ADR-A-012 deprecation-gate harness;
  verify CMDB_SOURCE=netbox is stable (≥30 days no incident); delete YAML file
- `secret/anthropic/api` Vault path deletion: verify no consumer; delete
- cAdvisor label workaround: remove from Grafana if Linux makes it moot; otherwise document timeline
- Headscale DERP server: self-hosted DERP relay for WireGuard traffic (avoids public DERP relays);
  improves resilience when external DERP is unavailable
- Vault token rotation automation: replace manual 30-day rotation reminder with a
  launchd agent that rotates the root token automatically (`vault token renew` or
  `vault token create -orphan`)
- macOS host monitoring: replace Zabbix agent container with a macOS-native approach
  (telegraf with macOS plugins) for true host-OS metrics (SMC temperatures, Bonjour, disk volumes)
- Nextcloud: enable Talk (video), Notes, and Deck apps; migrate any Plane project-tracking
  that doesn't need public issue tracking to Nextcloud Deck (lighter-weight alternative
  for personal tracking)

**Gate:** `phase-18-final` — PASS≥18 FAIL=0 WARN≤3.
OpenBao + Backstage ADRs committed. YAML deprecation complete. Platform hardening applied.
Phase 18 CLOSED.

---

### 18.E — Sports indexer expansion + Sportarr release-parser tuning (~6h hard cap)

Backlog from D-17-36 unpark execution (2026-05-03). Sportarr unparked
and stable on Miami round (Sprint Race + Qualifying both visible in
Plex Sports library at canonical path), but two operational gaps remain
that should not block the unpark close:

1. Indexer coverage thin (5 original Prowlarr-backed indexers, 2/5
   rate-limited tonight during WP-04 sweep). Sports content surface is
   different from movie/TV — sports-specific trackers (motorsport, F1,
   general DVR) are not in Prowlarr's default catalogue.
2. Release-parser misclassification (F12 worked example): Miami
   Qualifying release fetched at 100% confidence but linked to
   Australian Qualifying event; F12 doctrine chronicled but the
   correctness probe is open.

**Scope:**
- Sports tracker research (motorsport, F1-specific, general sports DVR communities, public + private):
  produce a tracker evaluation matrix (name, sports coverage, public/private, Prowlarr support,
  Cloudflare protection, rate limits, registration approach) — markdown table at
  `docs/phase-18/18E/tracker-evaluation.md`.
- Prowlarr-native vs Jackett/FlareSolverr triage: evaluate which trackers need each pathway;
  deploy FlareSolverr if absent (verify current stack first — operator notes Solar/Sonarr
  referenced previously, confirm presence or deploy in
  `~/control-center-stack/stacks/arr-stack/docker-compose.yml` with pre/post snapshots).
- Sportarr release-parser tuning ReleaseProfiles to address F12 (parser matched Miami Qualifying
  release to Australian Qualifying event at 100% confidence — wrong round): regex/required/preferred
  rules for round-disambiguation, committed to `config/sportarr/release-profiles/` with import
  script for repeatable apply.
- Per-tracker rate-limit awareness: avoid recurring rate-limited indexers like the 2/5 hit during
  D-17-36 WP-04 — health-check probe + Grafana alert when indexer rate-limit threshold approached.
- Indexer ACL classes + tracker-specific config documentation under D-17-37 substrate
  (`vendor-docs` ACL class likely fits; one ingestion per tracker).
- Filename-vs-event-title token mismatch probe `scripts/sportarr-correctness-probe.py`
  (F12 close, ~3-4h): periodic scan over EventFiles parses filename for venue/round tokens,
  asserts linked Event.Title contains the same venue token; soft-fail surfaces as a Sportarr
  tag or external dashboard signal + Grafana panel.

**Prerequisites:**
- D-17-36 closed (Sportarr stable baseline) — DONE 2026-05-03.
- D-17-38 closed (health check signal restored) — pending.
- F12 finding chronicled — DONE 2026-05-03 at
  `docs/architecture-facts/integration-audit-doctrine.md` Finding 7
  + `docs/_audit/integrated-stack-gaps-2026-05-03.md` Gap F12.

**Deliverable artifacts:**
- Tracker evaluation matrix (markdown table in
  `docs/phase-18/18D/tracker-evaluation.md`).
- Parser tuning rules (Sportarr ReleaseProfiles) committed to
  `config/sportarr/release-profiles/` with import script (volume
  mounts) for repeatable apply.
- FlareSolverr deployment in
  `~/control-center-stack/stacks/arr-stack/docker-compose.yml` if
  not present, with pre/post snapshots in the rewire log.
- Filename-vs-event-title mismatch probe at
  `scripts/sportarr-correctness-probe.py` + Grafana panel.

**Hard cap:** 4h research + 2h implementation when scheduled. If
research surfaces that public sports trackers are uniformly behind
Cloudflare AND FlareSolverr deployment is non-trivial, fall back to
private-tracker-only path and document the public-tracker abandonment
as a Phase 18 finding.

**Gate:** `phase-18-18E` — Sportarr indexer count ≥ 8 healthy
(non-rate-limited), one Phase 18 round (any sport) imports to correct
event row on first attempt. F12 mismatch probe registered in Grafana
with zero current mismatches.

---

### 18.D — Network flow collection + visualization (deferred from Phase 16)

Live NetFlow / IPFIX from OPNsense → flow collector container
(akvorado, ntopng, or pmacct candidate) → Grafana visualization.
Addresses live network-flow visibility for security and
troubleshooting; deferred from Phase 16 because the operator's
"what is each system, IP, connections" requirement was determined
to be satisfied by NetBox + xindex (configured topology), not
requiring NetFlow (live flows). 18.D remains a valid future option.

Effort: ~6-8h (collector choice is a separate research turn).

---

## What does NOT fit in these phases

**Intentionally deferred indefinitely:**
- Kubernetes migration: platform doctrine is Docker + Colima. No k8s until
  operator explicitly wants it. Would require rewriting every compose file.
- Training / fine-tuning pipelines: GPU compute for inference (Phase 18)
  is not fine-tuning. Fine-tuning requires dataset curation, training infra,
  model registry — a dedicated phase if the operator pursues it.
- Multi-tenant / team access: current platform is single-operator.
  Adding team access would require Vault namespace segmentation,
  Plane multi-workspace, and Headscale ACL policies — another dedicated phase.

---

## Effort summary

| Phase | Blocks | Effort | Key milestone |
|---|---|---|---|
| 15 A–G (done) | CF-1–4, D-OP, D-CN, Studio day-1, 4.H, 4.J, Plane curation | ~23–38h | ✅ Complete |
| **16** | Mac Studio AI stack, InvenTree suppliers, cross-index, Phase 13 CL | **~85–130h** | Studio productive; Phase 13 closed |
| **17** | Three-plane architecture corrections + local AI stack (20 deliverables D-17-01–T) | **~75–110h** | Stack corrected; OpenProject migration; agent surfaces consolidated |
| **18** | Health stack, Threadripper/Linux, platform hardening + evaluations | **~80–130h** | GPU compute; health metrics; platform matured |
| **Total remaining** | | **~240–370h** | |

Point estimate: **~210h** at historical +50% discovery overhead on novel-pattern blocks.
Calendar at one 12–18h execution window per week: **~12–18 months**.

---

## External prerequisites summary

| Prereq | Blocks it gates | Current status |
|---|---|---|
| Mac Studio physically present | 16.A | Arrives 2026-05-01 ✅ |
| Mouser API key (`secret/mouser/api#key`) | 16.B | Pending operator |
| DigiKey OAuth (`secret/digikey/api`) | 16.B | Pending operator |
| 129-component CSV | 16.B | Pending operator |
| Gmail OAuth (`secret/gmail/oauth`) | 16.B/16.C | Pending operator |
| Oura OAuth (`secret/oura/oauth`) | 18.A | Pending operator |
| Garmin auth path decision | 18.A | Pending operator |
| BLE label printer hardware | 18.A | Pending operator |
| Linux/Threadripper physically present | 18.B | Future hardware |

---

## Discovery numbering

- Phase 13: #1–#24
- Phase 14 D-DOC / Increment 1.5: #25–#31
- Phase 14 full: #32–#36
- Phase 15: #37+ (ongoing)
- Phase 16+: continues from wherever Phase 15 closes

---

## Execution handoffs

- Phase 15 Blocks A–G: `docs/phase-15/PHASE_15_EXECUTION_HANDOFF_2026-04-30.md` (committed `249a941`)
- Phase 15 Blocks H–O (now Phase 16 scope): procedures are in the same handoff doc; import them into the Phase 16 execution handoff when that phase opens
- Phase 16 execution handoff: to be written at Phase 16 kickoff
- Phase 17 execution handoff: to be written at Phase 17 kickoff (canonical plan: `docs/phase-17/PHASE_17_PLAN_2026-05-01.md`)
- Phase 18 execution handoff: to be written at Phase 18 kickoff
