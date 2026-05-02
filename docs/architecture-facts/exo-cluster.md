# exo cluster — architecture fact

D-17-14 deliverable artifact. This is the canonical reference for
how the platform's exo distributed-inference cluster is built and
what it actually does versus what it was originally designed to do;
if this file disagrees with any other doc, this file wins (D#22).

## Status of this document

**Authored at D-17-14 close (2026-05-02).** D-17-14 closes with
PARTIAL realization of original goal: cluster substrate works,
single-node inference works, platform integration via litellm works,
**distributed inference does NOT work** at this writing — see
"What is and isn't operational" below for the precise boundary.

Future Claude sessions reading the framework MUST NOT read D-17-14's
"DONE" status as "distributed inference is operational." It is not.
The distributed-inference unlock requires either an upstream exo
fix (TODO items 15–16, MlxJaccl coordinator stabilization) or
confirmation of the D-17-25 macOS-alignment hypothesis (RDMA-over-
TB5 path).

## What is and isn't operational

### Operational

- **Cluster substrate.** Two nodes (Mac Mini M4 Pro 48 GB orchestrator
  + Mac Studio M3 Ultra 96 GB peer) participate in an exo libp2p
  cluster over Thunderbolt 5 (`TB-Bridge` interface, link-local
  `169.254.0.0/16`, TCP port 5678/5679 between
  `169.254.169.73 ↔ 169.254.35.30`). Topology API reports the
  combined 144 GB pool. Dashboard renders. OpenAI-compatible HTTP
  API listens on `:52416`.
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
  - **MlxRing:** "MLX ring backend requires connectivity between
    neighbouring nodes" — the backend's neighbour-graph check
    rejects the TB-Bridge link's reachability semantics.
  - **MlxJaccl:** "jaccl backend requires all participating
    devices to be able to communicate" — same class of rejection.
  Cross-referenced with exo upstream `MISSED_THINGS.md` ("Jaccl
  coordinator over TB5 is unstable") and TODO items 15–16 (TB5
  prioritization not implemented). This is upstream-known
  instability, not a misconfiguration on this cluster.
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

### Revisit triggers (either-of)

- **Upstream exo TB5 fix.** Track upstream `MISSED_THINGS.md` and
  TODO items 15–16. If the Jaccl coordinator stabilizes over TB5,
  multi-node placement should work without local config change.
- **D-17-25 macOS-alignment hypothesis confirmed.** Mac Mini is
  on macOS 25.3.0; Mac Studio on 25.4.0. The minor OS-version
  drift is one candidate cause for RDMA-over-TB5 failing to
  initialize; aligning both nodes to the same macOS release may
  unblock the RDMA path the MLX backends prefer. Untested as of
  D-17-14 close; D-17-25 carries the test.

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

D-17-14 surfaced **19 findings** matching the InvenTree pattern:
*"state appears established but working-system substrate isn't
actually present."* This density is itself a deliverable-level
lesson: composite supply chains (upstream tool + custom forks +
Apple toolchain + multiple OS versions + libp2p ephemerality +
container env propagation) accumulate latent gaps that surface
only when a new consumer exercises a previously-untested path.

The 19 findings, grouped by pattern:

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
- **I (refinement)** — RDMA over TB5 requires aligned macOS
  versions across nodes; one node ahead of the other prevents
  RDMA-as-primary-path even with otherwise-correct interface
  config. Tracked as D-17-25 hypothesis.
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

### Doctrine-shaping finding (codified as D#24)

The recurring "two-install-options, defaulted-conservative, paid-
for-it-with-extra-round-trips" pattern (T1.0/T1.5/Xcode escalation
rounds in D-17-14) became the seed for **D#24 — install the full
set on developer toolchain decisions** (see PROJECT_FRAMEWORK §3.5).

## Dependencies + follow-on deliverables

- **D-17-25** — macOS alignment hypothesis test for RDMA-over-TB5
  (Finding I refinement). May unblock Finding O.
- **D-17-24** — CLAUDE.md staleness fix (Finding L). Reduces
  resumed-session prioritization drift.
- **D-17-26 (provisional)** — Vault-Agent sidecar for open-webui
  wiring `OPENAI_API_KEY` from Vault (Finding S). Required before
  Open WebUI can route to exo or any other litellm-routed model.
- **Upstream exo** — TODO items 15–16 (TB5 prioritization),
  `MISSED_THINGS.md` (MlxJaccl coordinator stabilization). Track
  upstream releases; multi-node WP-05 revisits when these land.

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
