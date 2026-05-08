# Candidate Tools

Tools observed in the 2026-04-30→05-01 article-intake window
(deliverable D-17-19) that may warrant evaluation against a specific
platform need. Listed here so the option exists when the need
matures — not endorsed, not committed.

Each entry includes scope-gating: what would have to be true for
this tool to make sense, and what would have to be true for it to
NOT make sense (so the bar to adopt is explicit, not vibes).

When a candidate is adopted, its entry flips here (kept for history)
with status, deliverable reference, and pointer to canonical
doctrine.

---

## Cisco Model Provenance Kit — model lineage attestation (ADOPTED)

**Status.** ADOPTED via D-17-10 (commit chain TBD on landing).
Pinned at upstream tag `1.0.0` (commit `5f27dc56`). License: Apache
2.0.

**Tool.** [`cisco-ai-defense/model-provenance-kit`](https://github.com/cisco-ai-defense/model-provenance-kit) — open-source Python toolkit
+ CLI that fingerprints transformer models (architecture metadata,
tokenizer structure, weight-level features) and matches against a
reference DB of known base models. Reports F1 0.963 / accuracy
96.4% on the 111-pair release benchmark. Released 2026-05-01;
adopted 2026-05-02.

**What we use it for.** Lineage attestation of model pulls. Every
new HuggingFace / Ollama model is verified against Cisco's catalog
before landing on a compute node. Convention-style wrappers
(`scripts/{verify-model-provenance,ollama-pull-verified,hf-download-verified}.sh`)
plus a documented override mechanism.

**What we do NOT use it for.** Cryptographic signature
verification (different threat model; sigstore / transparency-log
work would be a separate deliverable).

**Coverage as of catalog snapshot 2026-05-02.** 152 fingerprints,
39 families, 866 MB seed DB. Strong on base instruction models
(Qwen, Gemma, Llama, Mistral, DeepSeek, Phi, GPT-OSS, Granite,
Falcon, Yi, …). Weak on code-specialized fine-tunes (Coder
variants of Qwen2.5 absent; Gemma 4 family absent; Qwen3-Coder
family absent; nomic-embed family absent).

**Canonical doctrine.** `docs/architecture-facts/model-provenance.md`.

**Operator workflow.** `docs/runbooks/pull-new-model.md`.

**Baseline backfill.** `docs/_provenance/backfill-2026-05-02.md`.

---

## Goose CLI — local agent surface (BLOCKED-UPSTREAM)

**Status.** Evaluated under D-17-13 (2026-05-03). NOT adopted.
**Blocked-upstream**, not "adopted-not-tried." Pinned at
v1.33.1 (`brew install block-goose-cli`). License: Apache 2.0.

**Tool.** [`block/goose`](https://block.github.io/goose/) — Block-
authored open-source AI agent CLI with first-class MCP
integration and an OpenAI-compatible provider that supports
custom `OPENAI_HOST` + `OPENAI_API_KEY` (so it can target the
platform's litellm-gateway directly).

**Wiring that worked.** Brew install, config dir
`~/.config/goose/config.yaml`, provider points at
`http://127.0.0.1:4000` (litellm host port). Launcher
`scripts/goose/goose-platform.sh` injects the litellm master key
from Vault at run time (no credential in static config).
filesystem-mcp + xindex MCP extensions registered as stdio
extensions; both surface to Goose's tool inventory.

**Blocker.** Goose hard-codes `supports_streaming: true` in its
openai provider; Ollama drops `tool_calls` from streaming
responses; exo's OpenAI-compat shim returns tool calls as
`<tools>{json}</tools>` text rather than structured `tool_calls`.
Goose can therefore chat with the model but cannot complete a
single tool-using turn against any backend in the platform's
local stack. Full root-cause analysis:
`docs/architecture-facts/local-tool-calling.md` Findings 1+2.

**Revisit signal.** Either (a) Ollama emits `tool_calls` in
streaming responses, OR (b) Goose exposes a config key to
disable streaming for the openai provider, OR (c) exo's
OpenAI-compat shim post-processes Qwen's native tool-call
markers into structured `tool_calls`. Any one unblocks adoption.

**Demo posture.** Centerpiece stays Claude Code + subagents
(decomposer/implementer/reviewer per `~/.claude/agents/`) talking
directly to Anthropic in the orchestrator and Ollama in the
subagent shell — both paths handle tool-call protocol natively.
exo remains the inference backend for chat/completion paths.

**Eval artifacts.** `docs/phase-17/d-17-13/EVALUATION_2026-05-03.md`.
Install + Vault-mediated launcher + MCP wiring is reusable when
the upstream block lifts.

---

## Inbox Zero — AI-assisted email triage (Gmail tier scope-gated)

**Tool.** Inbox Zero (open-source, ~MIT-licensed AI email assistant
that proposes archive/label/respond actions and lets the user
batch-approve). Runs against Gmail OAuth.

**Scope-gate (would make sense if).**
- Operator's Gmail volume materially exceeds the 5–10 min/day
  triage budget AND
- A future Gmail OAuth deliverable is in scope (currently gated
  per `secret/gmail/oauth` external prereq) AND
- The triage actions Inbox Zero proposes are inspectable (not
  black-box) and run via the operator's own Gmail OAuth, not a
  third-party broker.

**Scope-gate (would NOT make sense if).**
- Gmail tier is "personal use, low volume" — manual triage is
  faster than reviewing AI proposals AND
- Operator prefers email-as-a-stream rather than email-as-a-task-
  queue (Inbox Zero's whole framing is the latter).

**Adjacent platform fit.** If adopted, deploy in the same pattern
as other AI-touching services: Vault-mediated OAuth (no creds in
env), Caddy site, NetBox CMDB row, xindex registration. Local LLM
backend (litellm → Ollama) — must NOT depend on Anthropic API per
LLM Access Doctrine in CLAUDE.md.

**Action threshold.** Revisit when a Gmail OAuth deliverable is
opened. Until then, this entry is a bookmark, not a commitment.

---

## OpenShell sandboxing primitive

**Tool.** OpenShell — a sandboxing primitive for shell operations,
constraining which commands, paths, and network calls a subprocess can
make.

**Scope-gate (would make sense if).**
- Local agent execution (Goose, OpenCode subagents) needs granular
  permission isolation without heavy containerization AND
- Sandboxing overhead is <5% on typical workloads AND
- Permission ruleset is human-reviewable (not a magic blackbox).

**Scope-gate (would NOT make sense if).**
- Container-based isolation (Docker) is already the boundary AND
- Permission model doesn't map cleanly to the agent's actual needs AND
- Complexity outweighs marginal safety gains.

**Adjacent platform fit.** If adopted, integrate as an optional
permission layer in Goose's execution sandbox (separate from Caddy/Vault
RBAC). Audit trail of sandboxed operation outcomes → OpenProject
ticket for appeal/override.

**Action threshold.** Evaluate if Goose reaches Phase-B (broad
operator-facing tasks) and permission audit flags show >5 denied-but-necessary operations per week.

---

## exo distributed inference

**Tool.** exo — distributed inference cluster across multiple machines,
coordinating token generation and KV cache management via a
decentralized protocol.

**Scope-gate (would make sense if).**
- Ollama single-machine throughput becomes a bottleneck (>10
  concurrent requests) AND
- Network latency between Mac Studio + Threadripper is <20ms AND
- Token-per-second gain >30% compared to single-machine Ollama.

**Scope-gate (would NOT make sense if).**
- Current single-machine Ollama sustains all workloads without queuing AND
- Cluster complexity (distributed state, recovery, monitoring) becomes
  a staff burden AND
- Ollama upstream adds native distributed features (monitor upstream).

**Adjacent platform fit.** If adopted, integrate as a transparent
Ollama replacement on Mac Studio (exo cluster coordinator runs there,
Threadripper joins as peer). Existing OpenCode/Aider/Goose provider
configs point to Mac Studio endpoint; exo handles routing internally.

**Action threshold.** Profile Ollama queue latency at 6+ concurrent
requests; revisit exo if p95 latency >2s consistently.

---

## InstantMesh + TripoSR pipeline

**Tool.** InstantMesh (single-image 3D mesh generation) + TripoSR
(image-to-3D geometry) as a pipeline for converting 2D (photos,
floorplans, renders) to 3D assets for digital-twin visualization.

**Scope-gate (would make sense if).**
- 3D model generation becomes a frequent operational task (>5 models/month)
  AND
- Output quality meets floorplan/spatial-context accuracy needs
  (visual fidelity ≥ Sweet Home 3D manual tracing) AND
- GPU time required per model is <1 hour (Threadripper RTX 4070).

**Scope-gate (would NOT make sense if).**
- Manual CAD tracing in Sweet Home 3D remains fast enough (operator
  choice, not infrastructure burden) AND
- Generated 3D assets require >30% post-processing (diminishing returns)
  AND
- Model fidelity drifts too far from reality for spatial reasoning.

**Adjacent platform fit.** If adopted, integrate as a batch job:
operator uploads source image → asynchronous Threadripper job →
generates .obj/.glb → stores in QNAP media/3d-assets/ → Home Assistant
Picture Elements references it.

**Action threshold.** Prototype with a single floorplan test image;
evaluate output quality against Sweet Home 3D equivalent manually
traced.

---

## IKEA MYGGSPRAY E2494 Matter-over-Thread sensor

**Tool.** IKEA's MYGGSPRAY E2494 — a Matter-certified environmental
sensor (temperature, humidity, air quality) with Thread support for
mesh-network reach extension.

**Scope-gate (would make sense if).**
- Home Assistant + Frigate integration needs expanded sensor coverage
  (currently no air-quality sensors) AND
- Price <$30/unit AND
- Thread network is already deployed (Matter + Thread router on network).

**Scope-gate (would NOT make sense if).**
- Existing non-Matter sensors (Zigbee, Z-Wave) already cover the space
  AND
- Matter ecosystem on this hardware (Mac Mini Home Assistant support) is
  incomplete AND
- 6-month firmware update lag on new devices becomes a support burden.

**Adjacent platform fit.** If adopted, pair with a Thread border router
(Home Assistant Thread support via Apple TV optional + OPNsense MQTT
relay for non-Matter fallback). Data → InfluxDB → Grafana dashboard
(existing pattern).

**Action threshold.** Revisit when Home Assistant Thread support is
available on the control node and at least 2 other Thread devices are
deployed.

---

## Three-axis camera slider from 3D printer parts

**Tool.** Mechanical camera slider (motorized X-Y-Z motion) built from
3D-printed parts and commodity components (stepper motors, rails,
timing belt), controlled via GPIO or serial interface.

**Scope-gate (would make sense if).**
- Frigate camera calibration (zone remapping, camera pitch/yaw adjustment)
  requires frequent manual repositioning AND
- Automated slider reduces setup time by >50% AND
- Build cost is <$200 and build time is <16 hours.

**Scope-gate (would NOT make sense if).**
- Frigate cameras are mounted in fixed, pre-optimized locations AND
- Mechanical complexity introduces more failure modes than it solves
  AND
- 3D-printed parts wear quickly under repeated motion (durability risk).

**Adjacent platform fit.** If adopted, integrate slider control as a
Plane ticket action (operator clicks "Recalibrate camera 1" → slider
moves to preset position → Frigate zone overlay resets). GPIO control
via Raspberry Pi or QNAP GPIO pins; status logged to Zabbix.

**Action threshold.** Prototype with a single axis (X only) using
existing 3D printer scrap parts; measure failure rate over 100 cycles.

---

## $60 hackable drone

**Tool.** Low-cost (<$100) programmable drone with accessible source
code, API, or firmware for custom flight logic and sensor integration.

**Scope-gate (would make sense if).**
- Home digital-twin use cases require aerial imagery (roof inspection,
  perimeter survey, land-plat verification) AND
- Operator has line-of-sight flying space (not urban/neighbor-dense)
  AND
- Regulatory path is clear (FAA Part 107 exemption or waiver scope).

**Scope-gate (would NOT make sense if).**
- Static Frigate camera network already covers all needed angles AND
- Local FAA rules prohibit autonomous flight (Part 107 solo not exempted)
  AND
- Build/repair skills required exceed operator capacity.

**Adjacent platform fit.** If adopted, integrate as a one-off survey
tool (not continuous operation). Flight logs → QNAP archive → link
from OpenProject ticket. Thermal/RGB sensor streams → Home Assistant
dashboard (if available).

**Action threshold.** Research regulatory pathway (FAA Part 107 rules,
waiver process) before procurement. Revisit only if a specific
operational need (roof condition, land survey) makes drone data
essential.

---

## lidarr.internal search

**Tool.** Enhanced search capabilities for Lidarr (music indexer),
improving both UI search quality and programmatic API search precision
for music library discovery.

**Scope-gate (would make sense if).**
- Music library size exceeds 10,000 albums AND
- Operator search-miss rate (artist/album not found on first try) exceeds
  10% AND
- Lidarr search quality improvement is achievable without upstream
  forking.

**Scope-gate (would NOT make sense if).**
- Current Lidarr search is fast enough for daily workflows AND
- Search enhancement requires custom indexing (Elasticsearch, etc.) that
  adds infrastructure burden AND
- Lidarr upstream already has planned improvements (monitor 3-month
  roadmap).

**Adjacent platform fit.** If adopted, implement as a read-only Solr or
Meilisearch index (external to Lidarr, fed by Lidarr webhook on library
changes). Navidrome integrates with the same index for client-side
search. No modification to Lidarr core required.

**Action threshold.** Revisit when music library reaches 10K+ albums or
when operator feedback indicates search is a friction point (tracked in
QNAP survey logs).

---

## Lambda Hermes agent reasoning traces dataset

**Tool.** Publicly available dataset of agent reasoning traces (model
outputs, tool calls, intermediate states) from Lambda model agent
experiments, useful for benchmarking and failure-pattern analysis.

**Scope-gate (would make sense if).**
- Benchmark matrix (existing artifact schema) needs >100 real-world
  failure cases to improve recurrence_rate metrics AND
- Dataset format (JSONL, time-indexed traces) aligns with artifact
  schema AND
- Data licensing permits local archival and analysis.

**Scope-gate (would NOT make sense if).**
- Current 12-packet operator hand-grade is sufficient for decisions AND
- Dataset is proprietary or requires cloud ingestion AND
- Traces are not relevant to the platform's task classes (long-context,
  multi-file refactor, tool-call, agentic).

**Adjacent platform fit.** If adopted, ingest as supplemental benchmark
corpus: `scripts/ingest-benchmark-corpus.sh --source lambda-hermes
--output docs/_benchmark-corpus/`. Failures tagged by class and
cross-indexed to WP artifacts for pattern analysis.

**Action threshold.** Revisit when hand-grade backlog exceeds 50 packets
or when a specific failure class (e.g., malformed-edit-count) shows
unexplained variance.

---

## Homebridge 2.0 Matter update

**Tool.** Homebridge version 2.0 release, adding Matter support for
bridge-less HomeKit and expanded platform compatibility.

**Scope-gate (would make sense if).**
- Existing Homebridge instance is actively maintained AND
- Home Assistant + Homebridge integration needs Matter federation
  (current Zigbee/Z-Wave setup insufficient) AND
- Upgrade path is clear (no breaking changes to existing automations).

**Scope-gate (would NOT make sense if).**
- Home Assistant native HomeKit integration is already sufficient AND
- Current Homebridge version is stable and requires zero maintenance AND
- Matter ecosystem on this network is incomplete (no border router,
  limited Thread devices).

**Adjacent platform fit.** If adopted, upgrade Homebridge in a
maintenance window with automated backup (Restic snapshot pre-upgrade).
Existing Home Assistant automations continue unchanged; new Matter
devices added post-upgrade via Matter controller (Home Assistant web
UI).

**Action threshold.** Revisit when Home Assistant Matter support is
marked stable (not beta) and when Thread network is deployed with ≥3
devices for mesh resilience.

---
