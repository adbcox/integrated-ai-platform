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
> `docs/_audit/stack-architecture-2026-05-01.md` for rationale and
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
- **D-17-40 candidate (logged 2026-05-03 from D-17-38 close):** Container-side TLS
  handshake failure to QNAP appliance — root-cause + workaround. Symptom: every
  `requests.get(https://192.168.10.201, verify=False)` from inside Debian-13
  containers returns `tlsv1 alert internal error` (TLS alert 80) regardless of
  TLS version (1.2/1.3) or SNI. Host (macOS native LibreSSL) negotiates TLSv1.3
  + AEAD-CHACHA20-POLY1305-SHA256 cleanly. Working hypothesis: Debian 13 OpenSSL
  3.5.5 default cipher suite or X.509 verification stricture incompatible with
  QNAP QTS TLS config. D-17-38 worked around at the reachability layer with a
  bare TCP-connect fallback in `connectors/qnap.py:health_check`; storage stats
  via `_storage_via_qts` still impacted (warns "Storage check failed: error").
  Investigate: explicit cipher suite pinning, OpenSSL config override, QNAP cert
  re-issue with modern key/sig profile, or replace HTTPS path with QTS-native
  CLI over SSH (would need publickey auth provisioned — QNAP rejects password SSH).

**Audit note (D-17-60, 2026-05-04):** `D-17-40` is a reserved candidate ID in
`docs/PROJECT_FRAMEWORK.md` §9 (intentionally no standalone row until promoted).
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
- **Prowlarr Application URL canonicalization sweep** (F10 worked-example #5 follow-on,
  D-17-36 follow-on 2026-05-03, ~1-2h): scan all Prowlarr `/api/v1/applications` records;
  flag any `prowlarrUrl` containing `localhost` or `127.0.0.1` (must be `http://prowlarr:9696`
  container DNS); flag any `baseUrl` using `<host>.internal:` form (must be container DNS
  to the consumer container, e.g. `http://sportarr:1867`). Bilateral fix per D-17-36
  follow-on. Pattern note: fullSync against a broken Application URL creates duplicate
  consumer indexer rows (Sportarr exhibited 8 rows for 5 Prowlarr slots before fix); sweep
  must include "consumer indexer count > Prowlarr indexer count for same Application"
  duplicate-detection probe.
- **Per-consumer Prowlarr auth-freshness sweep** (F10 worked example #6, D-17-50 DONE
  2026-05-03): moved from single-master hash comparison to implementation-aware functional
  probes. Sonarr/Radarr and Sportarr can validly present different Prowlarr-proxy key
  hashes (`07ab59f4731b` vs `a3051e37707a` observed live), so hash mismatch alone is not
  a remediation trigger. Canonical trigger is functional auth failure (`HTTP 401`) on
  consumer release probe. Canonical fix path is Prowlarr-side Application recreate +
  forced `ApplicationIndexerSync`, then functional re-probe.

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

### 18.F — Electronic Design / DIY Projects Track (deferred — see prereqs)

Standing pattern for small, parallelizable hardware projects (ESP32-class
sensor nodes + HA integration). Each project lands as its own deliverable
when scoped, with a fixed shape:

- Asset registry record (ESP32 base + sensor BOM + enclosure license per
  asset-mgmt-deliverable-family Deliverable A — see
  `docs/architecture-facts/exo-cluster.md` Finding T)
- HA integration via ESPHome or Matter
- License tracking on enclosure STL (asset-registry license field)
- Provenance for AI-generated firmware/configs (sibling to D-17-10
  model-provenance kit)

**Track ethos:** small, parallelizable, each project closes in one
weekend. Doctrine sibling to arr-stack ecosystem expansion — community
has solved most of these; we integrate rather than invent.

**Candidate projects (operator picks priority):**

1. **Indoor air quality node** — CO2/VOC/PM2.5/AQI per room.
   Hardware: ESP32 + SGP30 + SCD41 + PMS7003 + SSD1306 OLED.
   HA integration: ESPHome native. Slot: carriage house workout area
   (north end) priority. Estimated $40-60/node hardware.
2. **Ultrasonic distance / occupancy detection.**
   Hardware: XIAO ESP32-C6 + HC-SR04 ultrasonic.
   Use case: garage bay parking guidance, workout-area presence
   (alternative to MYGGSPRAY for spaces where illuminance isn't
   relevant). Estimated $15/node.
3. *Reserved* — remaining projects from article's missing 3 evaluated
   when full text retrieved.

**Hard prerequisites for any deliverable in this track:**

- Asset registry schema with enclosure license field landed
  (asset-mgmt-deliverable-family Deliverable A)
- 3D model database license-aware schema landed (sibling to enclosure
  license tracking; same Deliverable A class)

**Track-level backlog items (author when first project activates):**

- ESPHome vs MicroPython firmware doctrine
- Standardized BOM-to-asset-registry workflow

**Defer until** asset-registry substrate (Deliverable A) lands AND
operator picks one of the candidate projects to activate first. Do not
add an ESP32 node speculatively — each one costs hardware + ongoing
maintenance + firmware update overhead.

---

### 18.G — arr-stack ecosystem expansion (multi-deliverable family)

Backlog from D-17-36 + D-17-38 close work. The arr-stack today (Sonarr,
Radarr, Prowlarr, Sportarr, qBittorrent) covers the "find + grab" half
of the pipeline but has structural gaps the chronicle work has surfaced:
no observability beyond container health (Finding 1 / F5), no declarative
configuration substrate for the full stack (Finding 11 / F11 —
Radarr + Prowlarr now covered by D-17-44; Sonarr v4 + Sportarr
pending upstream plugin support), no automated bad-download removal or missing-content hunting
(would have caught the Radarr paused-torrent + F1 episode-4-of-9 missing
scenarios), no AI-orchestration surface (forcing this session into
ad-hoc curl loops against `localhost:9696`/`localhost:7878`).

This is a **multi-deliverable family** — not a single deliverable.
Each component below becomes its own `D-NN-NN` at scope time.

**Components and prereq order** (later components depend on earlier
ones being stable):

1. **Scraparr / Exportarr → existing VictoriaMetrics** ✅ DONE D-17-46 (2026-05-03)
   *(observability before expansion — adding components to a stack
   you can't observe is exactly the F5 silence-mechanism trap that
   D-17-38 closed.)* Prowlarr-side metrics, per-indexer success/fail
   rates, queue depth, import-import lag. Vault-managed API tokens
   per service (D-17-38 credential pattern). Grafana dashboards
   `arr-stack-overview-p18` + per-service drill-downs.
   **Delivered:** Scraparr deployed with Vault Agent sidecar and vmagent
   scrape path into VictoriaMetrics; minimal provisioned Grafana dashboard
   `arr-stack-overview-p18` landed for scrape age/duration + exporter health.
   **Follow-on backlog:** adapt/import Scraparr community dashboard JSON once
   datasource templating (`DS_MIMIR`/`${datasource}`) is normalized for this
   Grafana provisioning substrate.

2. **Buildarr config-as-code** ✅ DONE D-17-44 (2026-05-03)
   *(declarative state lock-in; first worked example for F11
   config-drift doctrine — now a numbered Finding.)* Radarr +
   Prowlarr managed. Scope: Radarr full coverage, Prowlarr
   applications-only. Sonarr v4 + Sportarr out-of-scope (documented
   known limitations in Finding 11). YAML at
   `config/arr-stack/buildarr/buildarr.yml`, daily launchd sync via
   `scripts/buildarr-run.sh`. Manual UI edits become either ratified
   into the YAML or reverted on next run. YAML IS the playbook.

3. **Cleanuparr deployment (Huntarr role consolidated into
   Cleanuparr Seeker module)** *(DEPLOYED; structural closure
   pending credentials + first-pass enablement).*
   Cleanuparr queue/remediation modules target stalled/bad-state
   downloads and trigger replacement searches; Cleanuparr Seeker
   covers missing-content and upgrade hunts with pacing controls.
   Original two-tool prereq order revised when
   `plexguide/Huntarr.io` image became unreachable during
   deployment on 2026-05-03. Worked-example coverage: would have
   caught (a) Radarr's paused-torrent state during D-17-38
   (manually surfaced via selfheal logs); (b) the F1 Australia
   season missing episode-4-of-9 scenario. Current state (D-17-49):
   observable-but-inert deployment in dry-run/monitoring posture;
   destructive cleanup and active Seeker hunting remain gated until
   §18.L provisions download-client credentials and operator
   authorizes first-pass enablement.

4. **Lidarr** ✅ DONE D-17-87 (2026-05-04) *(music management).*
   Deployed on the canonical arr-stack compose substrate with the
   Sonarr/Radarr sibling mount/network pattern, Caddy route
   `lidarr.internal`, Dnsmasq host override, Vault AppRole/policy,
   service-generated API key harvested into `secret/arr/lidarr`,
   and Prowlarr ApplicationIndexerSync completed. Buildarr coverage
   remains unconfirmed and is treated as reactive/manual until plugin
   support is proven from source.

5. **Bazarr** ✅ DONE D-17-47 (2026-05-03) *(subtitle automation,
   universal value across Sonarr + Radarr + Sportarr).* Deployed
   alongside arr-stack with canonical `/downloads` + `/data` binds,
   Caddy route `bazarr.internal`, and Vault Agent sidecar injection
   of Sonarr/Radarr API keys. Initial no-credential provider baseline
   enabled; credential-bearing provider enrollment deferred to §18.L
   companion gate. Buildarr coverage check: no `buildarr-bazarr`
   plugin/package currently available (known partial-coverage gap,
   same F11 pattern). Follow-on backlog: Bazarr -> Plex notification
   provider/refresh trigger not configured in baseline; validate and
   land as a component-5 hardening step when provider-credential
   enrollment is scheduled.

6. **arr-suite-mcp-server** *(AI orchestration surface — replaces
   ad-hoc Claude Code direct-API curl loops with a typed MCP tool
   surface).* Tools: `get_queue`, `search_movie/show/song`,
   `get_indexer_health`, `get_calendar`, `get_library_stats`,
   plus mutation tools (gated): `force_search`, `delete_indexer`,
   `update_application_url`. Critical for D-17-36-style operations
   to become repeatable + audit-logged rather than ad-hoc shell
   loops. Vault AppRole per consumer (Claude Code sessions, Obot
   agents). Docker-compose service on Mac Mini, registered in
   `~/.platform-registry/inventory.json` per D-17-29.

7. **Autobrr** *(latency reduction via IRC announce channels —
   moves grab-decision from periodic-RSS to push-on-announce).*
   For private-tracker users only. Cuts time-to-grab on new
   releases from minutes (RSS interval) to seconds (announce push).
   Sportarr is the highest-value consumer (live-event windows are
   tight). Prerequisites: at least one private tracker registered
   that supports IRC announce (operator gate).

8. **Profilarr OR Recyclarr** *(TRaSH-Guides automation — quality
   profile + custom format curation. Operator picks GUI vs CLI.)*
   Recyclarr = CLI, fits the Buildarr-as-config-as-code pattern;
   Profilarr = GUI, easier ad-hoc tuning. Decision deferred to
   operator at scope time. Both deliver the same outcome:
   Sonarr/Radarr quality profiles stay in sync with the TRaSH
   community guidelines without manual UI maintenance.

**Doctrine cross-references:**
- Finding 1 (F5) — observability before expansion
- **Finding 11 (F11) — config-as-code / declarative state (now
  numbered; D-17-44 close is the first worked example)**
- Finding 6 (F10) — retirement-record-as-restoration-playbook is
  structurally unsound; Buildarr structurally closes this
- D-17-29 (service-registry MVP) — every new component registers
- D-17-37 + D-17-39 (artifact substrate + ingestion flow) — vendor
  docs for each new component go through the canonical surface
- D-17-38 (Vault Agent sidecar credential pattern) — every new
  component uses the pattern, never `.env` credentials

**Family-wide hard prerequisites:**
- D-17-29 service-registry stable (DONE — registry refresh chained)
- D-17-37 + D-17-39 artifact substrate + ingestion flow (DONE)
- D-17-38 health-check substrate stable (closed 2026-05-03)
- arr-stack baseline post-D-17-36 stable (Sportarr unparked, dups
  cleared, Prowlarr Application URLs canonicalized — DONE
  2026-05-03)

**Defer activation until** the family-wide prereqs are met (DONE
above) AND operator picks the first component to scope. Components
1 (observability) and 2 (Buildarr) are the recommended first picks
because they de-risk every later component. Components 3–8 are
parallelizable once 1+2 land.

**Effort estimate at family level:** 50–80h spread across 8 sub-
deliverables, of which 1+2 (~20h combined) are the structural prereqs
for the rest. Individual sub-deliverables per scope at 4–10h each.

---

### 18.H — HACS evaluation + plugin-vetting doctrine

Promoted from D-17-41 candidate intake (2026-05-03). HACS (Home
Assistant Community Store) is a third-party plugin ecosystem on the
Home Assistant hub at .141. Evaluating HACS is partly a feature
question (does HACS unlock capability gaps in the operator's
home-automation surface?) and partly a **supply-chain doctrine**
question (HACS plugins are community-maintained, often reverse-
engineered against vendor APIs, and carry a risk profile distinct
from official HA integrations).

**Scope:**
- HACS deployment on the .141 HA hub (`apt`-installed Home Assistant
  Core; HACS install via the standard `wget`-from-GitHub-release
  pattern). Snapshot HA config pre-install per HA backup procedure.
- Plugin-vetting doctrine authored as `docs/architecture-facts/
  hacs-supply-chain-doctrine.md`. Sibling to D-17-10 model-provenance
  kit. Doctrine fields per plugin: source repo URL, last commit
  date, maintainer count, vendor-API-reverse-engineered flag,
  license, ACL risk class (`vendor-official` < `community-vetted` <
  `reverse-engineered-api` < `unmaintained`).
- ACL risk class enforcement: reverse-engineered-API plugins are
  capability-isolated where HA's permission model allows; never
  granted credentials beyond what the underlying vendor API
  exposes (e.g. a reverse-engineered Tesla plugin gets the
  operator's Tesla credential, never platform-wide secrets).
- Capability gap inventory: enumerate the *specific* HA features
  HACS plugins are needed for. If the inventory is empty, HACS
  installation is deferred — speculative plugin ecosystems are a
  supply-chain attack surface without a feature trigger.

**Prerequisites:**
- HA hub on .141 stable (post-D-17-34 confirmed ✅)
- Concrete capability gap that HACS solves (operator-confirmed at
  scope time; **no current trigger**)

**Doctrine cross-references:**
- D-17-10 (model-provenance kit — sibling supply-chain pattern)
- D-17-37 (artifact substrate — HACS plugin source code goes
  through the canonical surface as `vendor-docs` ACL class for
  audit purposes)
- Finding 9 (configuration audits verify against operator-stated
  intent) — the plugin-vetting doctrine IS the operator-stated
  intent against which a plugin inventory is later audited

**Defer until** a concrete capability gap surfaces. **Do not add
HACS speculatively.** Estimated effort when triggered: 6–10h
(deployment 2h + doctrine authoring 3h + first plugin vetting 2h
+ documentation 1–3h).

**Audit note (D-17-60, 2026-05-04):** `D-17-41` is a reserved candidate ID in
`docs/PROJECT_FRAMEWORK.md` §9 (intentionally no standalone row until promoted).

---

### 18.I — OpenCode evaluation as agentic frontend alternative

Operator-confirmed candidate (2026-05-03). OpenCode (formerly an
agentic-coding frontend in the Goose / Continue / Aider category) is
evaluated against the same harness as D-17-13 Goose: tool-call
protocol behavior against the local Ollama + litellm + exo cluster
substrate.

**Scope:**
- OpenCode deployment in a sandbox path (Mac Mini, isolated from the
  primary Claude Code session). Configured against local Ollama
  endpoint (no Anthropic/cloud routes per LLM Access Doctrine).
- Tool-call protocol probe: does OpenCode handle streaming tool
  calls in a way that bypasses the D-17-13 Goose blocker?
  (Goose's tool-call streaming was the architectural sticking
  point — if OpenCode's protocol differs and works against local
  models, it's a candidate replacement.)
- Comparison matrix vs D-17-13 Goose, Continue, Aider, and
  Claude Code (via subagents). Axes: streaming-tool-call support,
  multi-file edit reliability, context window utilization, local-
  model compatibility (Ollama / litellm), token-discipline
  posture.
- Decision: adopt / defer / skip per the same ADR pattern as
  D-17-13. Adoption requires: streaming tool calls work, local
  model parity, no cloud-route dependencies.

**Prerequisites:**
- D-17-13 Goose evaluation closed (provides the comparison
  baseline)
- Local Ollama + litellm stack stable (confirmed)
- exo cluster reachable from Mac Mini (Phase 16 close
  confirmed)

**Decision criteria (gate):**
- IF streaming tool calls work against local models → adopt
  candidate, schedule full ADR
- IF streaming tool calls fail in the same way Goose's did →
  document the structural blocker, skip
- IF tool calls work but local-model parity is missing → defer
  pending model upgrade

**Lower-priority deferral note:** if the Saturday demo proves
Claude Code (Pro subscription) + decomposer/implementer/reviewer
subagents under `claude-local` covers the agentic-coding workflow
adequately, OpenCode evaluation drops in priority. The driver for
this evaluation is "is there a substrate gap in the current
agentic-coding posture?" If the answer is no, defer indefinitely.

**Effort estimate:** 8–12h (deployment 2h + protocol probe 3h +
comparison matrix 3h + ADR 2–4h).

---

### 18.J — Tautulli playback analytics + alerting

Promoted from D-17-42 candidate intake (2026-05-03). Tautulli is a
Plex monitoring substrate that exposes playback analytics, transcode-
vs-direct-play visibility, and alerting hooks Plex doesn't provide
natively.

**Scope:**
- Tautulli deployment on Mac Mini as a Docker compose service.
  Bind-mount config volume; security_opt + cap_drop per platform
  doctrine. Registered in `~/.platform-registry/inventory.json`
  per D-17-29.
- Plex API token via Vault Agent sidecar (D-17-38 credential
  pattern — never `.env`, never environment variables).
- Optional alert integrations (operator picks at scope time):
  Discord webhook, Slack webhook, email-via-Nextcloud-mail. None
  enabled by default — alert fatigue is real.
- Dashboard surfaces:
  - Who-is-playing-what-when (concurrent-stream visibility)
  - Transcode load (CPU / GPU pressure indicator — informs Mac
    Studio compute-node placement decisions)
  - Top-watched shows / movies (informs Sonarr/Radarr quality-
    profile + custom-format tuning)
  - Stream interruption / buffering events (informs network /
    storage troubleshooting)
- Sibling observability surface to the D-17-38 health-check
  substrate, NOT a replacement. Tautulli answers "is anyone
  watching"; D-17-38 selfheal answers "are services healthy".

**Prerequisites:**
- Plex stable ✅
- Vault Agent sidecar credential pattern proven (D-17-38) ✅
- D-17-38 health-check substrate landed ✅

**Doctrine cross-references:**
- D-17-38 — sibling observability surface (not replacement)
- D-17-29 — service-registry registration mandatory
- Finding 1 (F5) — Tautulli adds a new probe shape
  (application-level analytics) above the integration-health
  layer; classify failures correctly

**Defer until** concrete operator signal that Plex usage analytics
matter to workflow. **Do not deploy Tautulli speculatively** — the
substrate lands cleanly when there's a signal, but adding it without
a signal means another service to maintain. Estimated effort when
triggered: 4–6h.

**Audit note (D-17-60, 2026-05-04):** `D-17-42` is a reserved candidate ID in
`docs/PROJECT_FRAMEWORK.md` §9 (intentionally no standalone row until promoted).

---

### 18.K — CMDB reconciliation deliverable

Three-substrate drift problem surfaced repeatedly during Phase 17
chronicle work and Finding 4 (configuration audit doctrine). The
platform's "where do services live, what ports do they use, what
depends on what" question has THREE substrates today, each with a
different authority claim:

| Substrate | Authority claim | Status |
|---|---|---|
| NetBox CMDB at `netbox.internal` | Declared authoritative per ADR-A-014 | Active, primary |
| `config/service-registry.yaml.DEPRECATED` | A-012 deprecation-gate fallback | Deprecated, retained for fallback-only |
| `~/.platform-registry/inventory.json` | D-17-29 runtime substrate (canonical for ports / internal IPs / depends_on / Caddy routes / credential file metadata) | Active, primary at the runtime layer |

NetBox and `inventory.json` are BOTH authoritative — at different
layers (NetBox for declarative service catalog, inventory.json for
runtime state). The reconciliation question is: when do they
diverge, and what is the canonical resolution path?

**Scope:**
- Drift-detection probe: scheduled comparison of NetBox service list
  vs `inventory.json` service list. Diff surfaces as a Grafana
  panel + structured log. Drift cases:
  - Service in NetBox not in inventory → service declared but not
    deployed (or not registered correctly)
  - Service in inventory not in NetBox → service deployed but not
    declared (CMDB drift)
  - Service in both, attribute drift (port, internal IP, network
    membership) — surfaces which substrate is wrong
- Reconciliation doctrine authored as `docs/architecture-facts/
  cmdb-reconciliation-doctrine.md`. Authority hierarchy:
  inventory.json wins for *runtime* attributes (port, IP, healthy);
  NetBox wins for *declarative* attributes (capability, owner,
  ADR linkage). Drift between them is always a bug; the doctrine
  documents which way the fix flows per attribute class.
- YAML deletion gate: `service-registry.yaml.DEPRECATED` is
  deleted when (a) drift-detection probe shows zero NetBox ↔
  inventory.json drift for ≥30 days AND (b) the A-012 deprecation-
  gate harness passes. This is the existing 18.C bullet
  "`service-registry.yaml.DEPRECATED` deletion" elevated to a
  formal sub-deliverable of CMDB reconciliation.
- NetBox automation: CRUD operations on NetBox driven by
  inventory.json refresh (not the other way) — runtime substrate
  is the source of truth for attributes inventory.json owns;
  NetBox is the source of truth for attributes inventory.json
  doesn't model (capability, owner, ADR).

**Prerequisites:**
- NetBox CMDB stable ✅ (Phase 13 D-DOC close)
- `inventory.json` D-17-29 substrate stable ✅
- Caddy ↔ Dnsmasq parity check stable ✅ (D-17-21 close)
- Grafana panel substrate ✅

**Doctrine cross-references:**
- ADR-A-012 (service-registry deprecation gate)
- ADR-A-014 (NetBox as declared CMDB authority)
- D-17-29 (service-registry MVP — runtime substrate)
- Finding 4 (configuration audit doctrine — authority hierarchy
  is per-attribute, not per-substrate)
- Finding 9 (audits verify against operator-stated intent — the
  reconciliation doctrine IS the operator-stated intent against
  which both substrates are audited)

**Effort estimate:** 12–18h (drift probe 4h + doctrine authoring
4h + NetBox automation hook 4h + 30-day stabilization window
zero-effort + YAML deletion 1h + documentation 2–4h). Probe lands
first; doctrine + automation gated on probe-clean state.

---

### 18.L — Credential rotation deliverable

Triggered when stability baseline reached. Credential exposures
accumulated during Phase 17 incident-response and chronicle work
form a deferred-rotation queue; all are operator-acknowledged Sev-3
incidental (no values published, no third-party exposure), but the
queue should clear in a single coordinated rotation rather than
piecemeal. Operator framing: **the rotation itself is a system-
stability test** — if a coordinated rotation across all arr-stack +
infrastructure secrets succeeds without breakage, that's evidence
the Vault Agent sidecar pattern (D-17-38) and the credential-flow
discipline are robust.

**Burned-credentials queue** (chronological):
- **Sonarr / Radarr / Prowlarr API keys** — D-17-38 deferred
  (hash-only verification was followed; values appeared in transit
  through diagnostic command output during D-17-38 execution; no
  third-party exposure but the substrate doctrine treats this as
  rotation-required at next opportunity).
- **QNAP admin password** — D-17-38 Sev-3 incident (credential
  appeared in command output during NAS storage-stats probe
  diagnosis; identical posture to the API-key class above).
- **Torznab apiKey (Prowlarr-issued)** — D-17-36 follow-on Sev-3
  incident (2026-05-03; curl heredoc pipe failure during WP-2c
  duplicate-indexer identification streamed apiKey value to
  terminal stdout; recovered via switch to file-based handling;
  no re-display).
- **Seedbox credentials** — operator-acknowledged deferred (date
  / circumstance not chronicled; flagged here as part of the
  coordinated-rotation queue).
- **Bazarr subtitle-provider credentials** (OpenSubtitles, Addic7ed,
  SubDL, regional/account-bound providers) — deferred by operator at
  D-17-47 baseline. Bazarr deployed with no-credential providers only;
  provider-account enrollment is intentionally coupled to the same
  coordinated-rotation companion session after stability baseline.
- **Lidarr API key** — D-17-87 added the new arr-stack credential
  surface. The key was harvested from the running service and written
  to Vault with hash-only verification (no raw-value transcript
  exposure), but should be included in the coordinated §18.L rotation
  inventory alongside Sonarr/Radarr/Prowlarr.
- **arr-stack admin UI passwords** — D-17-98 seeded `username/password`
  in `secret/arr/{lidarr,sonarr,radarr,prowlarr,bazarr}` (no plaintext
  transcript output). Lidarr now stores auth credentials in
  `/config/config.xml` per application behavior; include in coordinated
  rotation window and ensure post-rotation config/runtime parity.

**Scope:**
- Pre-rotation snapshot: enumerate every consumer of every
  rotating credential. `~/.platform-registry/inventory.json`
  credential_files metadata (D-17-29) is the inventory; verify
  against live state per service before rotation.
- Rotation runbook authored as `docs/runbooks/coordinated-
  credential-rotation.md`. Steps per credential class:
  generate-new → write-to-Vault → trigger-Vault-Agent-sidecar-
  refresh → verify-consumer-reads-new → invalidate-old-on-source.
  Order matters: consumer must be reading new before old is
  invalidated, or the service breaks.
- Rotation execution window scheduled with pre/post snapshots
  in the rewire log per platform doctrine.
- Post-rotation verification: every consumer service health-
  green; D-17-38 selfheal cycle clean (4/4 services healthy
  on next iteration; zero auth-warning escalations).
- Doctrine update: D-17-38 hash-only-verification near-miss
  list cleared; chronicle entry "deferred-rotation queue
  closed YYYY-MM-DD".

**Prerequisites (stability gate):**
- All Phase 17 deliverables closed (D-17-XX status table in
  PROJECT_FRAMEWORK.md §9 shows zero open items)
- D-17-38 selfheal substrate stable for ≥7 days (zero auth-
  warning false positives)
- arr-stack baseline post-D-17-36 stable for ≥7 days (no Sportarr
  / Radarr / Prowlarr operational incidents)
- Vault Agent sidecar refresh path tested non-destructively
  (synthetic credential rotation in dev path before production)
- D-17-49 Cleanuparr dependency chain satisfied before closure
  claims: populate `secret/downloads/qbittorrent` and
  `secret/downloads/sabnzbd`, then run first-pass Seeker enablement
  under operator gate. Until then, component 3 remains
  DEPLOYED/observable and not F10-closure-DONE.

**Doctrine cross-references:**
- D-17-38 (hash-only-verification doctrine; this deliverable is
  the rotation half of the pair — the doctrine prevents new
  exposures, the rotation clears the existing queue)
- D-17-29 (credential_files metadata in inventory.json — the
  consumer inventory)
- Finding 1 (F5) — selfheal is the post-rotation verification
  surface

**Operator framing — rotation as stability test:** if the
coordinated rotation breaks any consumer, that's a finding about
the Vault Agent sidecar pattern, NOT just a rotation execution
issue. The deliverable is dual-purpose: clears the queue AND
exercises the substrate end-to-end.

**Effort estimate:** 8–14h (pre-rotation snapshot 2h + runbook
authoring 3h + execution 2h + verification 2h + chronicle
authoring 1–5h depending on what surfaces).

---

### 18.M — Eve + Nanoleaf Matter-over-Thread brand candidates

Tier-2 brand candidates for the Matter-over-Thread sensor expansion
footprint. The current §18.F DIY-electronics track has the IKEA
MYGGSPRAY pilot referenced as the Tier-1 occupancy / illuminance
substrate (see §18.F candidate 2 — ultrasonic node use case
description). This section catalogs vendor-finished-product
alternatives evaluated as Tier-2 candidates after the MYGGSPRAY
pilot completes.

**Scope:**
- **Eve** (vendor-finished Matter-over-Thread sensors): door /
  window contact, motion, weather (temperature + humidity), energy
  monitor strips. Strengths: HomeKit-native, high build quality,
  long battery life. Weaknesses: price premium, vendor lock-in for
  some firmware features that gate behind the Eve app.
- **Nanoleaf** (vendor-finished Matter-over-Thread): primarily
  lighting (light strips, panels, bulbs) with motion-sensing
  variants. Strengths: Matter standard adherence, robust HA
  integration. Weaknesses: lighting-only product line is narrower
  than Eve's sensor catalog.
- Evaluation matrix at `docs/phase-18/18M/matter-brand-evaluation.md`
  produced before any Tier-2 hardware purchase: device class
  coverage, price-per-sensor, HA integration depth (native / via
  Matter / via vendor-cloud), firmware update transparency,
  vendor lock-in risk, Thread border router compatibility (HA
  hub on .141 vs. Apple TV / HomePod as alternative border router).
- Tier-2 activation gates: **only after** the MYGGSPRAY pilot
  (§18.F candidate 2 territory) has run for ≥30 days with stable
  HA integration. Tier-2 candidates exist to fill capability gaps
  the IKEA Tier-1 set doesn't cover (e.g. door/window contact —
  IKEA's coverage is uneven), NOT to duplicate Tier-1 functionality
  with premium brands.

**Prerequisites:**
- §18.F asset-registry substrate (Deliverable A) landed
- IKEA MYGGSPRAY pilot run ≥30 days (Tier-1 baseline established)
- Concrete capability gap that Tier-2 brands fill (no current
  trigger — defer until pilot reveals gaps)

**Doctrine cross-references:**
- §18.F (DIY-electronics track — sibling deliverable family;
  Tier-2 vendor-finished is the inverse approach to Tier-1
  community DIY)
- D-17-37 (artifact substrate — vendor docs go through canonical
  surface as `vendor-docs` ACL class)
- Finding 9 (configuration audits verify against operator-stated
  intent — Tier-2 evaluation matrix IS the intent against which a
  later inventory is audited)

**Defer activation until** MYGGSPRAY Tier-1 pilot stable for ≥30
days AND specific capability gap identified. **Do not purchase
Tier-2 hardware speculatively** — vendor-finished products carry
ongoing firmware-update overhead and vendor-lock-in risk that DIY
ESP32 nodes don't.

**Effort estimate:** 4–6h evaluation matrix; per-device deployment
when triggered is 1–2h each (HA Matter pairing + asset-registry
record).

**Audit gap note (D-17-60, 2026-05-04):** `18.N` (Jellyfin parallel-deploy
evaluation candidate) and `18.O` (local AI execution-surface migration framework)
are not authored in this roadmap file. `D-17-53` is the existing §9 anchor for the
18.O scope narrative. Authoring of 18.N/18.O is deferred to a separate deliverable.

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
