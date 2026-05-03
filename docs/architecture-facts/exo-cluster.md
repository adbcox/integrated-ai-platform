# exo cluster — architecture fact

D-17-14 deliverable artifact. This is the canonical reference for
how the platform's exo distributed-inference cluster is built and
what it actually does versus what it was originally designed to do;
if this file disagrees with any other doc, this file wins (D#22).

## Status of this document

**Authored at D-17-14 close (2026-05-02). Updated at D-17-25 close
(2026-05-02). Updated at D-17-28 recovery cascade close
(2026-05-02).** D-17-14 closes with PARTIAL realization of original
goal: cluster substrate works, single-node inference works, platform
integration via litellm works, **distributed inference does NOT work**
at this writing — see "What is and isn't operational" below for the
precise boundary.

D-17-25 tested the macOS-alignment hypothesis empirically (both nodes
aligned to macOS 26.4.1 / build 25E253) and found it **necessary but
not sufficient.** Macos alignment cleared the "INCOMPATIBLE macOS
VERSIONS" banner and unblocked the MlxJaccl pre-flight check, but
runtime distributed-init now SIGSEGVs inside MLX/jaccl. Two new
upstream gaps surfaced (Findings U + V below). Distributed-inference
unlock now requires upstream fixes covering BOTH the JACCL
coordinator IP selection (Finding U) AND the RDMA control-plane /
runner IBV-matrix disconnect (Finding V).

Future Claude sessions reading the framework MUST NOT read D-17-14's
"DONE" status as "distributed inference is operational." It is not.
Macos alignment moved the failure from pre-flight rejection to
runtime segfault — partial progress, but the distributed path
remains blocked.

D-17-28 (post-D-17-25 recovery cascade) closed the colima/lima
substrate failure surfaced by the same OS upgrade that enabled
D-17-25, and added eight findings (W, X, Y, Z, ZZ, AA, BB, CC)
documenting the operational-substrate gaps the recovery exposed:
per-tool path conventions (W), VM-runtime user-mapping fragility
(X), launchd user-domain disruption (Y), Vault credential-store
friction (Z), AI credential exposure (ZZ), architectural truth
substrate gap (AA), misdiagnosis-via-tool-blame pattern (BB), and
service-registry gap (CC). CC frames a Sunday-priority Service
Registry MVP candidate; full Platform Operational Substrate scope
captured in Findings AA + CC + T.

## What is and isn't operational

### Operational

- **Cluster substrate.** Two nodes (Mac Mini M4 Pro 48 GB orchestrator
  + Mac Studio M3 Ultra 96 GB peer) participate in an exo libp2p
  cluster over Thunderbolt 5 (`bridge0` interface, link-local
  `169.254.0.0/16`, TCP port 5678/5679 between Mini and Studio's
  static `169.254.35.30`). Mini's bridge0 link-local is dynamically
  assigned and DRIFTS across reboots (was `169.254.169.73` at
  D-17-14 close, `169.254.153.133` at D-17-25 close); only the
  Studio's static address is load-bearing for bring-up. Topology
  API reports the combined 144 GB pool. Dashboard renders.
  OpenAI-compatible HTTP API listens on `:52416`.
- **Single-node inference.** A model placed onto a single node via
  exo's MlxRingInstance with `worldSize: 1` runs and responds via
  `/v1/chat/completions`. Verified on Mac Mini with
  `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit`: TTFT 0.659s,
  throughput 55.21 chunks/sec on a 256-token completion, runner
  subprocess RSS 4.56 GB.
- **Platform integration.** `litellm-gateway` carries an
  `exo-qwen-coder-7b` route pointing at exo's OpenAI-compatible
  endpoint; reachable from any litellm-authed client (subagents,
  MCP servers, autonomous-coding agents, platform scripts) via the
  existing Bearer-auth path.
- **Provenance gate compatibility.** D-17-10's
  `hf-download-verified.sh` returns exit 3 (verified-base-family)
  for mlx-community re-quantizations, which is the canonical
  success state for the exo path (see "Provenance gate semantics"
  below).

### Not operational

- **Distributed inference across the unified pool.** The original
  thesis — that the 144 GB pool unlocks models too large to fit
  on either node alone — is not realized. exo's MLX backends fail
  to instantiate across nodes over TB5:
  - **MlxRing (D-17-14 + D-17-25):** "MLX ring backend requires
    connectivity between neighbouring nodes" — the backend's
    neighbour-graph check rejects the TB-Bridge link's
    reachability semantics. macOS alignment did NOT change this
    failure mode for the ring backend.
  - **MlxJaccl (D-17-14):** "jaccl backend requires all
    participating devices to be able to communicate" — pre-flight
    rejection at the placement planner.
  - **MlxJaccl (D-17-25, post-alignment):** pre-flight check
    passes; valid 2-node placement is generated and POSTed; runner
    subprocesses start on both nodes, enter `mlx_distributed_init`,
    then SIGSEGV. Two interacting upstream gaps cause this — see
    Findings U and V below.
  Cross-referenced with exo upstream `MISSED_THINGS.md`
  ("get_mlx_jaccl_coordinators picks the first one, which is
  unstable") and TODO items 15–16 (TB5 prioritization not
  implemented). This is upstream-known instability, not a
  misconfiguration on this cluster.
- **Open WebUI surface for the exo route.** Open WebUI's
  `OPENAI_API_KEY` is empty (length=1; SHA-256 matches the
  empty-string hash). The container has worked through Open WebUI
  for months because it takes the `OLLAMA_BASE_URL` direct path
  for local models and never exercised the OpenAI-compatible
  client. Wiring requires its own Vault-Agent-sidecar deliverable
  (provisional D-17-26).
- **T4-distributed tier as a routable target.** The
  `docs/system-prompts/tiers/T4-distributed.md` framing
  (multi-node distributed inference, cluster-only capacity) is
  documentation-only. No consumer should route T4 today; there is
  no T4 backend.

### Revisit triggers (post-D-17-25)

D-17-25 closed the macOS-alignment hypothesis (necessary but not
sufficient — see Findings U + V). The single revisit signal is now:

- **Upstream exo fixes covering Findings U + V.** Specifically:
  (U) `get_mlx_jaccl_coordinators` selecting a coordinator address
  that respects libp2p static-peer multiaddr config (currently
  picks LAN IP over TB-Bridge); and (V) gating the runner's
  `MLX_IBV_DEVICES` matrix on `nodeRdmaCtl.enabled` state, with
  graceful fallback when RDMA is configured-but-disabled. Track
  upstream `MISSED_THINGS.md`, TODO items 15–16, and any future
  release notes covering MlxJaccl coordinator stabilization or
  RDMA control-plane integration.

The pre-D-17-25 macOS-alignment trigger is no longer relevant —
the test ran and the result is recorded.

## Cluster topology

```
Mac Mini M4 Pro 48 GB (orchestrator)
  ├── role: master (exo --bootstrap-peers <studio-multiaddr>)
  ├── api: http://localhost:52416 (OpenAI-compatible)
  ├── libp2p: 169.254.169.73:5679
  └── HF cache: /Users/admin/.cache/huggingface/hub/

         ↕ Thunderbolt 5 (TB-Bridge interface, link-local)
         libp2p heartbeat over TCP/5678↔5679

Mac Studio M3 Ultra 96 GB (peer)
  ├── role: worker (exo --libp2p-port 5678 ...)
  ├── libp2p: 169.254.35.30:5678
  └── HF cache: separate (Mac Studio's own home)
```

Combined addressable pool: 144 GB. With distributed inference
operational, this would host model classes neither node can host
alone (e.g., Llama-3.3-70B at higher precision than either node's
ceiling).

## Cluster bring-up — PROCEDURE, not config file

exo's libp2p peer-id is **ephemeral** — regenerated on every
restart, with no persistence flag exposed by the CLI (none of
`--bootstrap-peers`, `--libp2p-port`, `--api-port`, or
`EXO_LIBP2P_NAMESPACE` persist node identity). Static-peer
configuration is correct for deterministic-routing intent (TB5 vs
LAN), but the operational pattern is **dynamic-discovery-then-pin-
per-session**, not config-file-driven.

Canonical bring-up sequence (every cluster start):

1. **Start Mac Studio first** (listening peer; no
   `--bootstrap-peers`). Capture the new peer-id from its log.
2. **Construct Mac Mini's `--bootstrap-peers` multiaddr** from the
   Studio's current peer-id and the static TB-Bridge IP.
3. **Start Mac Mini** with that bootstrap config.
4. **Verify cluster formed** via `/state` API on the Mini (port
   `52416` by default, `52415` if conflict).

Detailed step-by-step in `docs/runbooks/exo-cluster-operations.md`.

## Provenance gate semantics for the exo path

exo consumes MLX-format weights, predominantly from
`mlx-community/*` HuggingFace repos. mlx-community re-quantizes
upstream PyTorch weights for MLX runtime; the re-quantized SHA
differs from the upstream-catalog SHA, so the D-17-10
exact-fingerprint check (exit 0) cannot match. The base-family
verification (exit 3, "verified-base-family") confirms lineage to
the upstream attested model and **IS the canonical success state
for any MLX consumer**.

The `hf-download-verified.sh` wrapper case statement
(`0|3) … run_download`) already encodes this. Operator-facing
prose must NOT frame exit 3 as "weaker than exit 0" or as
something requiring override. For exo, exit 3 is the state to
expect.

## litellm route shape

Single addition to `~/control-center-stack/stacks/gateways/
litellm_config.yaml`:

```yaml
  - model_name: exo-qwen-coder-7b
    litellm_params:
      model: openai/mlx-community/Qwen2.5-Coder-7B-Instruct-4bit
      api_base: http://host.docker.internal:52416/v1
      api_key: "sk-no-key-required"  # pragma: allowlist secret
```

`api_key` is a literal placeholder satisfying litellm's
openai-provider client schema; exo runs local with no auth. NOT a
credential. If exo ever introduces auth, this moves to a
Vault-Agent-rendered template.

When WP-05 unblocks (upstream fix or D-17-25 confirmed),
**no litellm config change is required** — exo's API surface is
identical regardless of single-node vs distributed runner
placement.

## Lessons learned — InvenTree-pattern findings

D-17-14 surfaced **19 findings** matching the InvenTree pattern,
with three more (T, U, V) added during D-17-25 and eight more
(W, X, Y, Z, ZZ, AA, BB, CC) added during the D-17-28 recovery
cascade — **30 findings total** across the deliverable family:
*"state appears established but working-system substrate isn't
actually present."* This density is itself a deliverable-level
lesson: composite supply chains (upstream tool + custom forks +
Apple toolchain + multiple OS versions + libp2p ephemerality +
container env propagation + VM-runtime layer + user-domain
launchd registry + credential-store cold-start dependencies)
accumulate latent gaps that surface only when a new consumer
exercises a previously-untested path or a routine operation
(OS upgrade, restart) traverses the dependency cascade.

The 30 findings, grouped by pattern:

### Toolchain prep (A–G)

- **A** — D-17-15 Day-1 toolchain gap. Mac Studio came up bare from
  Day-1 deliverable; D-17-14's "Day-1 done" assumption was wrong.
- **B** — Screen Sharing not functional to Mac Studio (workaround:
  SSH-only install path).
- **C** — exo MLX dependencies are TWO custom git forks
  (rltakashige `mlx-jaccl-fix-small-recv` + `mlx-lm`), not one.
- **D** — App Store is not a supply path on this platform; Xcode
  install must use `.xip` direct-download.
- **E** — Metal Toolchain is a separately downloadable Xcode 26.x
  component, not bundled with the base Xcode `.xip`.
- **F** — Xcode `.xip` and Metal Toolchain build versions drift
  between download cycles.
- **G** — Metal Toolchain cryptex install requires `TOOLCHAINS`
  env var set BEFORE `xcrun` resolves; in `~/.zshenv` not
  `~/.zshrc`.

### Cluster topology + transport (H–K, refinements I, Q)

- **H** — Multi-path topology requires explicit static-peer
  configuration to pin TB5 over LAN. **Refined by Q:** static-peer
  intent is correct, but bring-up must be dynamic-discovery
  (peer-id ephemerality) + per-session pinning.
- **I** — exo `topology.connections` fields label RDMA interfaces
  by name; `transport=Tcp` declares the *transport over which the
  remote peer is reachable*, not the in-flight tensor-pass medium.
- **I (refinement, D-17-25 result)** — Aligned macOS versions
  across nodes is **necessary but not sufficient** for distributed
  inference. Empirically validated 2026-05-02 with both nodes at
  macOS 26.4.1 / build 25E253: the "INCOMPATIBLE macOS VERSIONS"
  banner cleared and the MlxJaccl pre-flight check now passes,
  but the runner SIGSEGVs in `mlx_distributed_init` due to two
  separate upstream gaps (Findings U + V). The original I-refinement
  framing — "alignment is the unlock" — was incorrect; alignment
  is one of three required preconditions.
- **J** — exo's HTTP API binds to all interfaces by default
  (`0.0.0.0:52416`); operator-facing surface must be aware of this
  (Caddy reverse-proxy or ipfilter restriction if exposing beyond
  loopback).
- **K** — `~/.exo/models` directory must exist before exo starts;
  missing-dir traceback is non-fatal but log-noisy.
- **Q** — exo libp2p peer-id is ephemeral, NOT persistent across
  restarts; bring-up is a PROCEDURE, not a CONFIG FILE (see
  "Cluster bring-up" section above).

### Session resumption + tooling (L, N, R)

- **L** — CLAUDE.md "Current Phase:" staleness causes
  auto-prioritization drift across sessions; D-17-24 owns the
  fix.
- **N** — `huggingface-cli` deprecated in `huggingface_hub>=1.0`;
  canonical CLI is `hf`. `hf-download-verified.sh` patched at-
  source rather than worked-around in the consuming deliverable
  (commit `1dc2f3b`).
- **R** — Process-management kill patterns must account for
  asymmetric cmdlines per node-role; `pkill -f '.venv/bin/exo'`
  or PID-file based, NOT cmdline-flag-substring matching.

### Provenance + scope (M, O, P)

- **M** — exit 3 IS the only achievable success state for the exo
  path through D-17-10. mlx-community re-quants; codified in
  "Provenance gate semantics" above.
- **O** — Distributed inference is upstream-blocked, not
  operator-blocked. WP-05 deferred; codified in "What is and
  isn't operational" above.
- **P** — Configuration bugs (`--no-downloads`) compound; canonical
  config must be doctrine-correct. `--no-downloads` disables the
  DownloadCoordinator subsystem; provenance is gated at the
  wrapper layer (`hf-download-verified.sh`), NOT at the runner.

### Platform integration (S)

- **S** — Open WebUI's OpenAI-compatible client path is unwired
  (latent until exercised). Empty `OPENAI_API_KEY` was invisible
  for months because Open WebUI took the Ollama-direct path for
  local models. Wiring requires its own Vault-Agent-sidecar
  deliverable (provisional D-17-26). Meta-instance — extends the
  "appears established but isn't" pattern outside the exo install
  itself.

### Asset-management substrate gap (T) — surfaced D-17-25

- **T** — Platform asset-management substrate gap. No coherent
  inventory of OS / firmware (motherboard BIOS, GPU VBIOS, NVMe,
  network card, BMC, accessory: Garmin, Oura, Zigbee sensors, 3D
  printer mainboards, ESP32) / container runtime / container
  images / application binaries / library dependencies. AI
  cannot consult asset state before recommending upgrades.
  Operator cannot prevent AI failure modes pre-emptively.
  Visualization layer cannot surface upgrade-staleness for
  operator awareness. **Canonical example surfaced D-17-25:**
  the 2026-05-02 Mac Mini orchestration-node OS upgrade
  (26.3 → 26.4.1) was AI-recommended without consulting asset
  state, without asking which node was appropriate
  (orchestration vs idle-compute), without verifying premise
  against literature (RDMA major-vs-minor version requirement),
  without considering operational dependencies on the
  orchestration node, and without scheduling an appropriate
  maintenance window. Operator caught the planning failure but
  the reboot was already triggered. Post-D-17-25 intake will
  scope a deliverable family (asset data layer + visualization
  integration + AI maintenance layer + process documentation +
  doctrine) covering this gap. Finding T was the 20th
  InvenTree-pattern finding when surfaced; D-17-28 recovery
  added W, X, Y, AA, BB, CC reinforcing it from multiple angles
  (per-tool path conventions, VM-runtime layer, launchd registry,
  architectural truth registry, misdiagnosis pattern, service
  registry). The empirical case for the platform-operational-
  substrate deliverable family is now overwhelming.

### Distributed-init upstream gaps (U, V) — surfaced D-17-25

- **U** — `MLX_JACCL_COORDINATOR` address selection ignores libp2p
  static-peer multiaddr config. Empirical evidence (D-17-25 WP-05,
  2026-05-02): cluster control plane on TB-Bridge (`bridge0`,
  `169.254.x.x`) per static-peer config; JACCL coordinator chose
  Mac Studio's LAN IP `192.168.10.142:52617` instead. Matches exo
  upstream's `MISSED_THINGS.md` flag: *"get_mlx_jaccl_coordinators
  picks the first one, which is unstable."* Operator config cannot
  override; requires upstream fix. Reproducer evidence:
  `docs/phase-17/d-17-25-wp-05-multinode-evidence/`
  (`mini-runner-trail.log` + `studio-runner-trail.log` show the
  `MLX_JACCL_COORDINATOR: 192.168.10.142:52617` line).

- **V** — `nodeRdmaCtl.enabled=false` doesn't propagate to MLX
  runner's `MLX_IBV_DEVICES` matrix. Runner receives RDMA-device
  configuration (`[[null, "rdma_en5"], ["rdma_en3", null]]`) even
  when control plane reports RDMA disabled, resulting in SIGSEGV
  during `mlx_distributed_init` when the runner attempts to use
  uninitialized devices. Two interacting upstream bugs:
  (a) IBV-matrix not gated by RDMA control-plane state;
  (b) runner doesn't gracefully handle "configured for RDMA but
  RDMA actually disabled" — should fall back to TCP, doesn't.
  Reproducer evidence:
  `docs/phase-17/d-17-25-wp-05-multinode-evidence/state-pre-create.json`
  (`nodeRdmaCtl.*.enabled=false`) + runner-trail logs (the
  `MLX_IBV_DEVICES` line followed by `signal=11` ~3s later).

### Asset-management substrate refinement (W, X, Y) — surfaced D-17-28 recovery cascade

- **W** — Colima 0.10.1 stores its lima VM at `~/.colima/_lima/`,
  not the default `~/.lima/`. Diagnostic commands run without
  `LIMA_HOME` set will appear to show "no instance" when the
  instance actually exists. D-17-28 cold-recovery hit this:
  `limactl list` reported "No instance found" while
  `~/.colima/_lima/colima/disk` was 21.5 GB and intact. False-
  negative diagnostic risk is high — almost led to "data lost"
  recovery framing before operator caught with control-window
  verification. Future asset-management substrate must track
  per-tool path conventions, not just OS-default paths.

- **X** — macOS upgrades can break Lima VM user-ID mappings.
  D-17-28 evidence: colima daemon log shows `panic: user:
  unknown userid 502` at 2026-05-02 22:13:17, immediately
  followed by clean daemon shutdown. VM disk image survived;
  user mapping had to be re-established by `colima start`
  (which succeeded on first attempt — auto-recovery worked
  this time but not guaranteed). "VM-runtime layer" is a class
  below the container layer that traditional container-state
  monitoring (Zabbix container probes, Uptime Kuma HTTP checks)
  wouldn't catch — failures here cascade through the entire
  container substrate.

- **Y** — `launchctl` user-domain registry can be disrupted by
  macOS upgrades. D-17-28 evidence: `launchctl list | grep
  com.iap` returned zero registered jobs post-reboot despite 14
  IAP launchd plists present in `~/Library/LaunchAgents/`.
  `launchctl bootstrap gui/<uid>` failed with "Domain does not
  support specified action" (error 125). Non-urgent — the
  affected agents do background sync work (Strava,
  vault-audit-rotate, etc.), not platform-critical services —
  but adds "user-domain launchd agents" to the asset-management
  tracking scope and to recovery-runbook coverage. Re-registration
  needed before next session that depends on these agents.

### Vault architectural concerns (Z, ZZ) — surfaced D-17-28 recovery

- **Z** — Vault-as-credential-store creates persistent operator
  friction disproportionate to benefit in single-operator self-
  hosted environment. D-17-28 evidence: 4th reinstall counted via
  stale key files in `~`; cold-start chicken-and-egg between
  `seal-vault` (Transit autounseal source) and `vault-server`
  (autounseal consumer) requires manual Shamir unseal of
  `seal-vault` first; 30+ dependent services (vault-agent
  sidecars + every credential-consuming workload) down on routine
  OS upgrade. Operator considered architectural retirement during
  recovery. Empirical case for credential-storage architecture
  review documented as post-demo deliverable; not pre-empting the
  decision here.

- **ZZ** — AI-side credential exposure during recovery operations.
  During D-17-28, AI used `python3 -m json.tool` for diagnostic
  readability on Vault state output, exposing the seal-vault
  Shamir key in tool output. Operator-side rotation required
  post-demo. Documents an exact failure mode for credential-
  handling-via-AI: even with "minimal exposure" intent, default
  tool selection (pretty-print, log-tail, full-content fetch)
  produces full-content output. Future credential-handling AI
  work needs explicit redaction patterns and tool-selection
  doctrine, not "just be careful" — analogous to platform
  doctrine that prohibits credential values in tool output,
  commit messages, or transcripts (see CLAUDE.md "Anti-patterns").

### Platform Operational Substrate gap (AA, BB, CC) — meta-finding from D-17-28

- **AA** — Architectural truth substrate gap. Platform lacks
  canonical, AI-consultable documentation of containers, ports,
  credentials, dependencies, failure modes, and per-tool path
  conventions. Recovery sessions become archaeology — same facts
  re-discovered every time. D-17-28 evidence: AI re-discovered
  Vault port mapping (8201 not 8200), seal-vault/vault-server
  cold-start ordering, lima `_lima` path convention, vault-agent
  recovery semantics — all of which are knowable from existing
  platform configuration but not surfaced in a form an AI session
  can query. Sister concern to Finding T (asset/state/lifecycle
  gap); together they form the **Platform Operational Substrate**
  gap.

- **BB** — Misdiagnosis-via-tool-blame pattern. When the platform
  fails, AI tendency is to label the failed tool as "wrong tool."
  D-17-28 evidence: AI initially framed Vault as the friction
  source ("Vault-as-credential-store creates persistent operator
  friction") when the actual failure mode was AI not knowing
  seal-vault's port (8201 not 8200) — substrate gap, not tool
  gap. Tool selection is downstream symptom; substrate gap is
  cause. Doctrine: when proposing tool replacement under recovery
  pressure, first verify the alternative would actually fix the
  observed failure mode. (The Vault retirement question per
  Finding Z is real but separate from tonight's port-discovery
  failure.)

- **CC** — Service-registry gap. Platform has 84+ containers
  across multiple compose stacks with port mappings, internal-
  vs-host addresses, and Caddy-routed external names. There is
  NO canonical, AI-queryable answer to "where is service X
  reachable from context Y." AI defaults to well-known ports
  (8200 for Vault) and discovers actual mappings via archaeology
  when wrong. D-17-28 seal-vault port-discovery failure (8201)
  is the canonical example.

  Distinct from Finding AA (architectural truth as
  documentation): this is **runtime topology** that should be
  *derived* from authoritative sources (compose files +
  `docker inspect` + Caddy config), not maintained as
  documentation that drifts.

  Operator's framing (verbatim, captured for canonical reference):
  > "It's like a DNS helper to resolve what you think it's gonna
  > be to the correct port. Because it goes two ways. Internally
  > is different in the Docker because of [internal] addresses
  > chosen[;] externally it's been lost because you just showed
  > it. You didn't know the right port to go to for it. So this
  > is not a, like, a a document thing[;] it is a network routing
  > thing."

  Prior art (control-window-verified):
  - Docker's embedded DNS at `127.0.0.11` already provides
    internal name → IP resolution for container-to-container
    traffic (works on this platform today).
  - Host-side resolution gap is well-known. Established patterns:
    (a) CoreDNS proxy on host forwarding to `127.0.0.11` —
        exposes container DNS to host shell tools;
    (b) `devdns` / `dockerdns` purpose-built tools watching
        Docker events maintaining DNS records;
    (c) custom compose-aware inventory script producing
        canonical JSON of container → port mappings →
        credentials → dependencies for AI consultation.
  - For this platform, the right answer is probably BOTH (a) for
    host-shell convenience AND (c) for AI-structured
    consultation.

  **Doctrine implication — Platform Operational Substrate has
  three layers, not two:**
  1. **Architectural truth registry** (Finding AA) — design-
     level documentation: what is X, what does it do, how does
     it relate to Y.
  2. **Service registry** (Finding CC) — runtime topology:
     where is X reachable, on what port, from what context, with
     what credentials.
  3. **Asset/state/lifecycle management** (Finding T) —
     temporal state: what version, what's stale, when to upgrade.

  Service registry is most urgent because every recovery,
  upgrade, and debug session depends on it.

### Doctrine-shaping finding (codified as D#24)

The recurring "two-install-options, defaulted-conservative, paid-
for-it-with-extra-round-trips" pattern (T1.0/T1.5/Xcode escalation
rounds in D-17-14) became the seed for **D#24 — install the full
set on developer toolchain decisions** (see PROJECT_FRAMEWORK §3.5).

## Dependencies + follow-on deliverables

- **D-17-25** — macOS alignment hypothesis test for RDMA-over-TB5
  (Finding I refinement). **CLOSED 2026-05-02 with Outcome C:**
  alignment necessary but not sufficient; Findings U + V surfaced
  as the new upstream gaps. Did NOT unblock Finding O. Reproducer
  evidence preserved at
  `docs/phase-17/d-17-25-wp-05-multinode-evidence/`.
- **D-17-24** — CLAUDE.md staleness fix (Finding L). Reduces
  resumed-session prioritization drift.
- **D-17-26 (provisional)** — Vault-Agent sidecar for open-webui
  wiring `OPENAI_API_KEY` from Vault (Finding S). Required before
  Open WebUI can route to exo or any other litellm-routed model.
- **D-17-27 (provisional, post-D-17-25)** — File upstream issue
  with reproducer evidence covering Findings U + V. ~30 min
  scoped follow-up; may be merged into the asset-management
  deliverable family work.
- **D-17-28** — Colima/lima/Docker stack recovery from 2026-05-02
  OS-upgrade cascade. Cluster substrate restored via `colima start`
  (no UID 502 panic on retry); Vault unsealed by operator per
  credential doctrine; 12+ platform services healthy post-recovery.
  Surfaced 8 findings (W–CC) documenting the operational-substrate
  gaps the recovery exposed.
- **Asset-management deliverable family (post-D-17-25)** — A/B/C/D
  scope captured in operator memory, will be intake-doc'd as a
  standalone family. Closes Finding T. **Reframed post-D-17-28 as
  one of three layers in the Platform Operational Substrate**
  (asset/state/lifecycle layer; sister to architectural truth
  registry per Finding AA and service registry per Finding CC).
- **Service Registry MVP (Sunday-priority candidate, post-
  D-17-28)** — Compose-aware inventory script + optional CoreDNS
  proxy. Output: AI-consultable JSON inventory of container →
  port mappings → credentials → dependencies + DNS resolution
  from host shell. Closes Finding CC. ~4–6h scope. Substrate
  for the next 6 days of demo prep.
- **Upstream exo** — TODO items 15–16 (TB5 prioritization),
  `MISSED_THINGS.md` (MlxJaccl coordinator stabilization).
  Findings U + V are the specific gaps to monitor; multi-node
  WP-05 revisits when an upstream release covers both.

## See also

- `docs/runbooks/exo-cluster-operations.md` — operational procedures
- `docs/system-prompts/tiers/T4-distributed.md` — T4 tier prompt
  (currently documentation-only; updated at D-17-14 close to
  reflect actual single-node WP-04 numbers + explicit
  "T4-distributed not routable" caveat)
- `docs/architecture-facts/model-provenance.md` — D-17-10 gate
  semantics (companion to the "Provenance gate semantics" section
  above)
- `~/repos/external-tools/exo/MISSED_THINGS.md` — upstream's own
  list of known gaps (load-bearing for Finding O)
