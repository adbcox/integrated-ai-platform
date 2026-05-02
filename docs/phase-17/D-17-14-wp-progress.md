## D-17-14 work-package progress (transient)

**Lifecycle.** This file is a transient progress marker for D-17-14 (exo
distributed inference cluster). It captures install fingerprints and
chronicle findings between WP-level commits so the audit trail survives
session boundaries before the T5 framework flip. **At T5, contents fold
into `docs/architecture-facts/exo-cluster.md` and this file is deleted.**

---

### WP-17-14-01 — exo install on Mac Mini orchestrator (DONE 2026-05-02)

**Install location:** `~/repos/external-tools/exo/` (clone, not submodule).

**Pinned versions on Mac Mini:**
- exo: `v1.0.71` at commit `fd707de30b42db4211d15da96b9052e1dc280ed1`
- MLX: `0.31.2.dev20260502+ec49d18e` (rltakashige fork
  `mlx-jaccl-fix-small-recv` at commit
  `ec49d18ec4cfba0e0c7a37f20d1cf4d75fe56731`, source-built from this fork
  per exo `pyproject.toml`)
- macmon: `0.7.0` (vladkens fork at commit
  `a1cd06b6cc0d5e61db24fd8832e74cd992097a7d`, `cargo install` from git
  rev — NOT Homebrew, which reportedly crashes on Apple M5)
- rustup toolchains: stable `1.95.0`, nightly `1.97.0` (minimal profile)
- Apple toolchain: Xcode `26.4.1` build `17E202`, Metal Toolchain
  `com.apple.dt.toolchain.Metal.32023.883`, metal compiler version
  `32023.883 (metalfe-32023.883)`, target `air64-apple-darwin25.3.0`

**Verification (control window probed 2026-05-02 ~15:05 local):**
- `~/repos/external-tools/exo/.venv/bin/exo --help` returns the expected
  CLI usage (no `--version` subcommand exists).
- `python -c "import mlx.core as mx; print(mx.default_device())"` →
  `Device(gpu, 0)` — Metal GPU is the default backend.

---

### WP-17-14-02 — exo install on Mac Studio peer (DONE 2026-05-02)

**Install location:** `~/repos/external-tools/exo/` on Mac Studio
(reachable via `ssh mac-studio` → mac-studio.local on TB-Bridge en6).

**Pinned versions on Mac Studio (parity with Mac Mini):**
- exo: `v1.0.71` at commit `fd707de30b42db4211d15da96b9052e1dc280ed1`
- MLX: `0.31.2.dev20260502+ec49d18e` (rltakashige
  `mlx-jaccl-fix-small-recv` @ `ec49d18e`, source-built)
- mlx-lm: rltakashige fork at commit
  `c7010341e1f41ac15815feb5dc55134f44e3b044` (see Finding C
  refinement below — exo pins TWO rltakashige forks, not one)
- macmon: `0.7.0` from vladkens fork @
  `a1cd06b6cc0d5e61db24fd8832e74cd992097a7d`
- rustup toolchains: stable + nightly (minimal profile)
- Apple toolchain: Xcode `26.4.1` build `17E202`, Metal Toolchain
  `com.apple.dt.toolchain.Metal.32023.883`, target
  `air64-apple-darwin25.4.0` (Mac Studio is on macOS 25.4.0;
  Mac Mini on 25.3.0 — minor OS version drift between nodes)

**Verification (control window probed 2026-05-02 ~15:13 local):**
- `~/repos/external-tools/exo/.venv/bin/exo` present and executable
- `python -c "import mlx.core as mx; print(mx.default_device())"` →
  `Device(gpu, 0)` — Metal GPU is the default backend on M3 Ultra.

**Bootstrap sequence (all unattended via SSH, no sudo prompts):**
1. `brew install uv node` — clean install
2. `rustup` install via curl — stable 1.95.0
3. `rustup toolchain install nightly --profile minimal` — 1.97.0
4. `cargo install --git ... --rev a1cd06b6 macmon` — 0.7.0 from
   vladkens fork at pinned commit
5. `git clone exo + git checkout fd707de3` — pinned to v1.0.71
6. `cd dashboard && npm install && npm run build` — built in 4.50s
7. `uv sync` — MLX + mlx-lm source-built (Metal shaders compiled
   under the TOOLCHAINS env var inherited from Mac Studio's
   `~/.zshenv`); EXIT=0

---

### WP-17-14-04 — Model loading via provenance gate (DONE 2026-05-02, single-node scope per Finding O)

**Scope reframe.** Original WP-04 intent: load Qwen2.5-Coder-7B via
the D-17-10 provenance gate, distribute layers across the cluster
via MlxRing. Reframed mid-execution to single-node placement on
Mac Mini (where the model is cached) per Finding O — multi-node
MLX backends are upstream-blocked.

**Model selected.** `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit`
- HF cache path:
  `~/.cache/huggingface/hub/models--mlx-community--Qwen2.5-Coder-7B-Instruct-4bit/snapshots/019cc73c45c770444708a6dd8690c66243cc5c80/`
- On-disk size: 4.0 GB (4,284,263,424 bytes per exo storageSize)
- Layers: 28, hiddenSize: 3584, contextLength: 32768
- Provenance gate exit: 3 (verified-base-family — canonical for
  mlx-community re-quants per Finding M); proceeded under doctrine,
  no override required

**Download path.** `scripts/hf-download-verified.sh
mlx-community/Qwen2.5-Coder-7B-Instruct-4bit` after wrapper patch
in commit `1dc2f3b` (Finding N).

**Instance + runner state (verified via /state API at port 52416):**
- Instance ID: `ac2f1124-c147-401e-b9bc-beedc18d6680`
- Variant: `MlxRingInstance`
- Runner ID: `2dadb879-c3ab-41c6-8ca9-20d355e724d9`
- Runner state: `RunnerReady`
- Node placement: Mac Mini
  (peer-id `12D3KooWRDCXYqaWCGKn9maRvfZcJ5wUi4QUDUq3mX84ZPdYy1PS`)
- Worker port: ephemeral 54929
- World size: 1 (single-node)

**Inference benchmark (streaming /v1/chat/completions, 256 max
tokens, temperature 0.2):**
- Prompt: "Write a Python function to compute the Fibonacci
  sequence iteratively. Include a docstring."
- Time-to-first-token: **0.659s**
- Total wall time: **4.391s**
- Generation time: **3.731s**
- Throughput: **55.21 chunks/sec** (token-delta events)
- Output token-deltas: 206
- Output quality: coherent, syntactically correct Python with
  docstring; matches prompt intent

**Memory footprint (Mac Mini, single-node placement):**
- exo master process (PID 49152): 0.16 GB RSS
- MLX runner subprocess (PID 49396): **4.56 GB RSS**
- macOS pages_wired delta during inference: minimal
  (~117 pages over baseline)

**Network footprint.** Single-node placement → no inter-node
tensor traffic on TB-Bridge during this inference. Cluster
heartbeat traffic on TB-Bridge `169.254.169.73:5679 ↔
169.254.35.30:5678` continues at libp2p baseline.

**Deferred to WP-05/T5.** Multi-node distributed inference figures
(per-node memory split, TB-Bridge tensor-pass utilization) cannot
be measured against a working backend until upstream fixes
MLXRing/Jaccl over TB5 (Finding O). T5 must NOT publish T4-tier
latency figures based on this single-node WP-04 run.

---

### WP-17-14-06 — litellm route operational; Open WebUI deferred (DONE 2026-05-02, narrowed scope per operator decision)

**Scope as delivered.** litellm-gateway carries a sixth route,
`exo-qwen-coder-7b`, pointing at exo's OpenAI-compatible API at
`host.docker.internal:52416/v1`. The route is callable by any
litellm-authed client (subagents, MCP servers, platform scripts,
autonomous-coding agents) using the `LITELLM_MASTER_KEY` Bearer
token. End-to-end verified: client → litellm:4000 → exo:52416 →
loaded MLX runner on Mac Mini → coherent OpenAI-shaped response.

**Scope explicitly deferred.** Open WebUI's interactive-chat surface
for the exo route. Requires its own follow-up deliverable; see
Finding S.

**Why narrower than original brief.** The original WP-06 brief
included "operator can chat with cluster-routed model via Open
WebUI." That requires Open WebUI to authenticate against
litellm-gateway, which it currently cannot — `OPENAI_API_KEY` in
the Open WebUI container is effectively empty (length=1; SHA-256
hash matches the empty-string hash). Today the platform routes
Open WebUI directly to Ollama via `OLLAMA_BASE_URL`, bypassing
litellm entirely; the empty `OPENAI_API_KEY` had been latent.
Reaching exo through Open WebUI requires populating
`OPENAI_API_KEY` from Vault — a Vault-Agent-sidecar wiring that is
the right technical answer but the wrong scope answer mid-D-17-14
(operator-rejected as scope expansion against tonight's
discipline).

**litellm config change applied.**
File: `~/control-center-stack/stacks/gateways/litellm_config.yaml`
Change shape: ADDITION only (no modification to the five existing
Ollama routes). Block:

```yaml
  - model_name: exo-qwen-coder-7b
    litellm_params:
      model: openai/mlx-community/Qwen2.5-Coder-7B-Instruct-4bit
      api_base: http://host.docker.internal:52416/v1
      api_key: "sk-no-key-required"  # pragma: allowlist secret
```

Notes on the literal `api_key` value: this is NOT a credential.
exo runs local with no auth; litellm's openai-provider client
mandates *some* `api_key` to satisfy client-side schema validation.
If exo ever introduces auth, this moves to a Vault-Agent-rendered
template — flagged for runbook.

**Reload mechanism.** `docker restart litellm-gateway`; healthy in
6s. Container restart picks up the YAML diff (litellm reads config
on startup; no hot-reload needed for config additions).

**End-to-end verification.**
- `/v1/models` registers six routes (5 ollama + `exo-qwen-coder-7b`)
- `POST /v1/chat/completions` with `model=exo-qwen-coder-7b`,
  Bearer `$LITELLM_MASTER_KEY`, returns `{content:'ack'}` from the
  loaded model in <1s; `usage` block populated correctly.
- Authentication uses LITELLM_MASTER_KEY rendered by litellm's
  existing Vault Agent sidecar at `/vault/secrets/credentials.env`
  (no new Vault path required, no new sidecar required).

**Hash-only verification on token operations.** LITELLM_MASTER_KEY
extracted from container's Vault-Agent-rendered file for testing;
no value displayed in transcript. SHA-256 hash comparison used to
diagnose the empty `OPENAI_API_KEY` in Open WebUI (both hashes
shown to operator; values never exposed). Per platform doctrine.

**Forward-compatibility with WP-05 unblock.** When/if multi-node
distributed inference becomes available (upstream exo fix or D-17-25
macOS-alignment hypothesis confirmed), no litellm config change is
required: exo's OpenAI API surface is identical whether the
underlying placement is single-node or distributed. The
`exo-qwen-coder-7b` route stays as-is; the runner just becomes
multi-node behind the same endpoint.

---

### WP-17-14-05 — DEFERRED at WP-04+WP-06 closeout (operator decision 2026-05-02)

**Original scope.** Distributed inference of a pool-sized
(70B-class) model across the 144 GB cluster pool to validate that
the unified pool unlocks models that don't fit on either node
alone. This is the original D-17-14 thesis: cluster-as-aggregate-
capacity, not cluster-as-model-zoo.

**Deferral reason.** Upstream-blocked per Finding O. exo's MLX
backends (MlxRing, MlxJaccl) cannot establish multi-node
connectivity over TB5; cross-referenced with exo upstream
`MISSED_THINGS.md` ("Jaccl coordinator over TB5 is unstable") and
TODO items 15–16 (TB5 prioritization not implemented).

**Why NOT re-scope WP-05 to a single-node model on Mac Studio.**
Operator-rejected. Single-node Mac-Studio inference does not
validate the pool capability; it validates Mac Studio alone (which
could be done without ever setting up a cluster). Re-scope would be
"changing the question to fit the answer." Mac Studio capability
characterization, if needed, belongs in a future deliverable with
its own framework row, not bolted onto D-17-14.

**Why NOT re-scope WP-05 to model-zoo / cross-node API routing.**
Operator-rejected. Validates a different cluster-value axis (model-
zoo capacity vs unified-pool capacity) and represents motivated-
momentum scope expansion mid-deliverable. Worth a future
deliverable; not appropriate as a substitute for the original
WP-05.

**Revisit triggers (either-of):**
- (a) Upstream exo TB5 prioritization + Jaccl coordinator
  stabilization lands (track exo upstream `MISSED_THINGS.md` and
  TODO items 15–16).
- (b) D-17-25 macOS alignment hypothesis test confirms
  RDMA-as-primary-path fixes the MLX-backend issue (Finding I
  refinement).

**Independence of WP-04 / WP-06.** WP-05 deferred status does NOT
affect WP-04 single-node baseline (already DONE) or WP-06 platform
integration (in progress). Both are independent deliverables that
close at full scope.

**T5 framing requirement.** D-17-14 closes with PARTIAL realization
of original goal:
- Achieved: cluster substrate (libp2p, peer discovery, 144 GB
  topology reporting, dashboard, OpenAI API surface), single-node
  inference benchmarked, platform integration via litellm + Open
  WebUI.
- NOT achieved: distributed inference across the 144 GB unified
  pool.
- Reason: upstream-blocked (Finding O, upstream-acknowledged in
  MISSED_THINGS.md).

`docs/architecture-facts/exo-cluster.md` (T5) MUST EXPLICITLY state
that distributed inference is NOT operational at D-17-14 close.
State what works and what doesn't with clear boundaries — future
Claude sessions reading the framework must NOT read D-17-14's
"DONE" status as "distributed inference is operational."

---

### Chronicle findings (toolchain prep — to be folded into T5 doctrine)

These findings emerged during WP-17-14-01/02 toolchain prep. Each one
required empirical discovery on the actual hardware; none was predicted
from the planning-phase reads. The density of findings (seven, in
toolchain prep alone) reinforces the operator-flagged structural pattern
of the same morning's intake review: deliverables close against
documented scope but the next deliverable in sequence assumes a
working-system-level state the previous deliverable didn't actually
establish.

**Finding A — D-17-15 Day-1 toolchain gap.** Mac Studio came up bare
from D-17-15 (no developer toolchain: no brew, node, rust, uv, or
active CLT). D-17-15 closed against its stated scope (hardware + macOS
+ network reachable) but did not establish a developer-toolchain
baseline that the immediate next deliverable (D-17-14) required. Future
"Day-1" deliverables for new compute nodes should explicitly enumerate
developer-toolchain baseline as part of done-criteria.

**Finding B — Screen Sharing not functional to Mac Studio.**
Operator-reported during D-17-14 execution. Not in D-17-14 scope to
fix; flagged for separate troubleshooting. Workaround used here:
`softwareupdate` and `xcodebuild` invoked via SSH for unattended
toolchain operations. Documents that SSH-only install paths are
achievable and may be preferable when GUI access is uncertain.

**Finding C — exo MLX dependencies are TWO custom git forks (refined
2026-05-02 during Mac Studio build).** exo `pyproject.toml` pins:
- `mlx` → `rltakashige/mlx-jaccl-fix-small-recv` @
  `ec49d18ec4cfba0e0c7a37f20d1cf4d75fe56731`
- `mlx-lm` → `rltakashige/mlx-lm` @
  `c7010341e1f41ac15815feb5dc55134f44e3b044`

Both are custom forks of the upstream `ml-explore/mlx` and
`ml-explore/mlx-lm` projects. Both are source-built per node (Metal
shader compilation across many `.metal` files). Cannot substitute
`pip install mlx mlx-lm` — exo's lockfile will reject upstream
versions. Total per-node build time: ~15-45 min depending on node
parallelism. Implication for upgrades: `rltakashige` fork commits
are unilateral — no upstream coordination — so exo upgrades will
generally bring two new pinned commits to verify.

**Finding D — App Store is not a supply path on this platform.** Both
admin accounts (Mac Mini, Mac Studio) are intentionally walled off from
App Store via Apple ID for security reasons. Apple-supplied tooling
that was historically App-Store-only (full Xcode IDE) must be sourced
via `developer.apple.com/downloads` `.xip` files, scp'd between hosts,
expanded with `xip --expand`, and `sudo mv`d to `/Applications/`.
Future deliverables that assume App Store availability are making a
wrong assumption — the canonical Apple tooling supply path on this
platform is the developer portal, not the App Store. This applies
uniformly to both Apple Silicon nodes (Mac Mini and Mac Studio).

**Finding E — Metal Toolchain is a separately downloadable Xcode 26.x
component.** Installing `Xcode.app` and switching `xcode-select` is
necessary but **not sufficient** for MLX builds on macOS 26.x. The
`metal` binary at
`/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/metal`
is a stub (107 KB) that requires a separate Metal Toolchain component.
Download via `sudo xcodebuild -downloadComponent MetalToolchain
-buildVersion <build>`. Failure signature when missing: `error: cannot
execute tool 'metal' due to missing Metal Toolchain`.

**Finding F — Xcode `.xip` and Metal Toolchain build versions drift;
must specify `-buildVersion` explicitly.** Omitting `-buildVersion`
caused `xcodebuild -downloadComponent` to attempt a download for a
build version that did not match the installed Xcode, resulting in
404. Operator resolved by passing the exact build version from
`xcodebuild -version` output. Doctrine: always pass `-buildVersion`
when downloading Xcode components on a non-App-Store-managed Xcode
install.

**Finding G — Metal Toolchain cryptex install requires `TOOLCHAINS`
env var.** Metal Toolchain installs to a macOS cryptex-mounted location
(`/private/var/run/com.apple.security.cryptexd/mnt/com.apple.MobileAsset.MetalToolchain-…`)
that does NOT auto-register with `xcrun`'s default toolchain search.
After successful component download, `xcrun metal --version` still
fails with the same "missing Metal Toolchain" error. Workaround: add
`export TOOLCHAINS=<toolchain-identifier>` to `~/.zshenv` (loads for
all zsh invocations including non-interactive SSH and uv subprocesses).
Identifier discovered via `xcodebuild -showComponent MetalToolchain`.
Current identifier on this platform:
`com.apple.dt.toolchain.Metal.32023.883`. Identifier will change with
future Metal Toolchain updates, requiring `.zshenv` re-edit. This is a
**permanent per-session workaround**, not a one-time fix.

**Finding H — Multi-path topology requires explicit static-peer
multiaddr to deterministically route cluster traffic over TB5 vs LAN.**
exo's libp2p layer auto-discovers via UDP broadcast (mDNS) by default;
on a topology with two reachable paths between nodes (10 GbE LAN
192.168.10.x/24 and TB-Bridge link-local 169.254.x.x/16), auto-discovery
forms a cluster over whichever path broadcasts first — typically LAN,
since 192.168 is broadcast-routable while 169.254 link-local sometimes
isn't. That's a silent perf trap: cluster works, inference functions,
but uses the 8x slower path. Resolution: pass an explicit
`--bootstrap-peers /ip4/<TB-IP>/tcp/<port>/p2p/<peer-id>` multiaddr to
the dialing node, with the OS routing table determining the path
(verified via `route -n get <TB-IP>` resolving to bridge0). Confirmed
via lsof showing the established TCP connection on bridge0 IPs only.
Operator framing: hospitality-TV analogy — two paths exist for a
reason; cluster traffic must use the path it was built for, not by
happy accident of broadcast timing.

**Finding I — exo `topology.connections` fields label RDMA interfaces
even when RDMA is not active.** The `/state` JSON returned by exo's
HTTP API includes
`connections.<peer>.<peer>.[{sourceRdmaIface, sinkRdmaIface}]`. These
strings (e.g. `rdma_en3`, `rdma_en5`) name the RDMA-capable interface
exo would use **if** RDMA were negotiated; they do NOT confirm RDMA is
active transport. Authoritative answer for active-transport status is
the dashboard banner ("⚠️ RDMA NOT ENABLED ✕") or the established
TCP socket via lsof. Doctrine for runbook: don't trust the
`*RdmaIface` fields as evidence of RDMA-active transport — verify via
dashboard banner or socket-level inspection.

**Finding I (refinement) — RDMA over TB5 requires aligned macOS
versions on both nodes; this platform currently does not satisfy
that.** Mac Mini at macOS 26.3 (build 25D125), Mac Studio at 26.4.1
(build 25E253). exo gracefully falls back to TCP-over-TB-Bridge
(positive validation of exo's robustness — cluster forms and works
without RDMA). Aligning macOS versions (Mac Mini upgrade to 26.4.1)
would potentially unlock RDMA-class throughput. **NOT in D-17-14
scope**; this is a known performance unlock for a separate deliverable
(framework row to be authored). Implication for T4 tier prompt: the
"latency vs single-node" trade-off currently quoted in
`docs/system-prompts/tiers/T4-distributed.md` reflects TCP-over-TB
throughput; RDMA unlock would shift that math favorably.

**Finding J — exo's HTTP API binds to all interfaces by default
(LAN-reachable).** Mac Studio's exo API listens on `*:52415` (lsof
verified IPv4 wildcard). Anyone on `192.168.10.0/24` can reach
`http://192.168.10.142:52415` and submit inference requests to the
cluster. Mac Mini's API on port 52416 was observed only on
`127.0.0.1:52416` in lsof — possibly because it's the dialing
peer, possibly transient state during cluster formation; reconfirm at
WP-06 when integrating with litellm/Open WebUI. Currently the LAN is
internal-only behind OPNsense with no untrusted devices, so this is
not an active risk — but it's a real architectural fact requiring
firewall posture (Caddy or OPNsense rule) once cluster is
production-traffic-bearing. T5 runbook to document.

**Finding K — `~/.exo/models` directory must exist before exo starts.**
exo's info-gatherer probes disk usage at `~/.exo/models` on startup;
if missing, logs a non-fatal `FileNotFoundError` traceback. Cluster
forms and runs anyway (graceful degradation — the missing-dir error
is in a peripheral monitoring loop, not the critical path). Hygiene
step for runbook: `mkdir -p ~/.exo/models` before launch on every
node.

**Finding L — CLAUDE.md "Current Phase:" staleness causes
auto-prioritization drift across sessions.** A /loop wakeup prompt
captured at session-compact time can carry a deliverable identifier
(here: D-16-04.1) that has since closed; combined with a
CLAUDE.md "Current Phase:" line that lags the active deliverable,
the resumed session begins working on stale context before any
operator interaction. Detected this session when the /loop fired
"continue D-16-04.1 backup wait …" while D-17-14 was the active
deliverable. Mitigation: address as separate deliverable D-17-24
(post-D-17-14) — refactor "Current Phase:" line into something that
self-updates from PROJECT_FRAMEWORK active-row state, so a stale
CLAUDE.md cannot mislead resumed sessions. Do NOT edit CLAUDE.md
mid-deliverable (operator doctrine: deliverables don't get
substrate-level edits during their own execution window).

**Finding M — exit 3 IS the only achievable success state for the
exo path through the D-17-10 provenance gate.** mlx-community
re-quantizes upstream PyTorch weights for MLX consumption; the
re-quantized SHA differs from the upstream-catalog SHA, so the
gate's exact-fingerprint check (exit 0) cannot match. The
base-family verification (exit 3) confirms lineage to the upstream
attested model and IS the canonical success state for any MLX
consumer. The wrapper's case statement (`0|3) … run_download`)
already encodes this — but operator-facing prose must not frame
exit 3 as "weaker than exit 0" or as something requiring override.
For exo, exit 3 is the state to expect. Captured for T5
exo-cluster.md "Provenance gate semantics" section.

**Finding N — `huggingface-cli` deprecated in huggingface_hub>=1.0;
canonical CLI is `hf`.** D-17-10's `hf-download-verified.sh` was
authored against the older CLI name. Wrapper updated to invoke
`hf download` (same subcommand syntax, different binary name).
Doctrine integrity preserved by patching the wrapper rather than
adding a workaround inside D-17-14. Commit `1dc2f3b` carries the
fix and references this finding. Pattern: when an upstream tool
deprecates an interface that a platform wrapper depends on, fix the
wrapper at-source rather than working around it in the consuming
deliverable; otherwise the workaround becomes permanent debt.

**Finding O — exo distributed inference (multi-node MLX backends)
is upstream-blocked, not operator-blocked.** Both MlxRing and
MlxJaccl backends fail to instantiate across nodes over TB5:
- MlxRing: "MLX ring backend requires connectivity between
  neighbouring nodes" — backend's neighbour-graph check rejects the
  TB-Bridge link's reachability semantics.
- MlxJaccl: "jaccl backend requires all participating devices to
  be able to communicate" — same class of rejection.
Cross-referenced with exo upstream `MISSED_THINGS.md` ("Jaccl
coordinator over TB5 is unstable") and TODO items 15–16 (TB5
prioritization not implemented). This is a known upstream
limitation, not a misconfiguration on this cluster. **Scope
implication for D-17-14:** WP-04 reframed as single-node
validation; WP-05 re-scoped from "distributed 70B" to "single-node
32B-class on Mac Studio's 96 GB pool"; WP-06 (litellm + Open WebUI)
unchanged. Multi-node distributed inference is deferred — likely
requires either an upstream MLX-backend fix or the OS-version
alignment hypothesized in Finding I-refinement (RDMA-over-TB5
gating).

**Finding P — Configuration bugs compound; canonical config must
be doctrine-correct.** Mac Studio exo was started during WP-03
with `--no-downloads` as a defensive default ("don't pull anything
unsanctioned"). When the master scheduled the WP-04 model onto the
Studio, the worker rejected DownloadModel tasks silently because
the DownloadCoordinator subsystem was disabled by the flag. The
debugging window cost a surface-back round-trip. Operator decision
was to restart the Studio cleanly rather than rsync-pre-stage the
model (rejected as motivated reasoning — "production pattern"
framing rationalizing what is actually a workaround for a
configuration mistake). Pattern: defensive-default flags applied
without thinking through which subsystems they disable can produce
silent failure modes that look like infrastructure bugs. The
canonical exo cmdline for runbook should NOT include
`--no-downloads`; provenance is gated at the wrapper layer
(`hf-download-verified.sh`), not at the runner.

**Finding Q — exo libp2p peer-id is ephemeral, NOT persistent
across restarts.** Verified empirically (operator control window):
exo CLI exposes no peer-id-persistence mechanism. None of
`--bootstrap-peers`, `--libp2p-port`, `--api-port`, or
`EXO_LIBP2P_NAMESPACE` persist node identity. Each restart
regenerates a fresh libp2p peer-id. **Implication for runbook
shape:** cluster bring-up is a PROCEDURE, not a CONFIG FILE.
Each bring-up cycle:
1. Start Mac Studio (listening peer; no `--bootstrap-peers`).
2. Grep peer-id from Mac Studio's log.
3. Construct Mac Mini's `--bootstrap-peers` multiaddr from the
   current Studio peer-id.
4. Start Mac Mini with that bootstrap config.
T5's `docs/runbooks/exo-cluster-operations.md` MUST reflect this —
NOT a static config file with hardcoded peer-ids that becomes
stale on first restart. **Refines Finding H:** static-peer choice
remains correct for deterministic-routing intent (TB5 vs LAN), but
the operational pattern is dynamic-discovery-then-pin-per-session,
not config-file-driven.

**Finding R — Process-management kill patterns must account for
asymmetric cmdlines per node-role.** During WP-03 reform,
`pkill -f 'exo --libp2p-port'` matched the Studio cmdline (which
starts `exo --libp2p-port …`) but did NOT match the Mini cmdline
(which starts `exo --bootstrap-peers … --libp2p-port …`).
Asymmetric cmdline-prefix substring matching missed the master node
and required PID-based kill. **Canonical pattern for runbook:**
either `pkill -f '\.venv/bin/exo'` (matches the venv path that
both nodes share) or PID-file-based shutdown. Avoid cmdline-flag-
substring matching, which is fragile to argument-order differences
between roles.

**Finding S — Open WebUI's OpenAI-compatible client path is
unwired (latent until exercised).** Detected during WP-06: Open
WebUI container has `OPENAI_API_BASE_URL=http://litellm-gateway:4000/v1`
set, BUT `OPENAI_API_KEY` is effectively empty (length=1; SHA-256
matches the empty-string hash). The platform has worked through
Open WebUI for months because Open WebUI takes the
`OLLAMA_BASE_URL=http://host.docker.internal:11434` path for local
models and never exercised the OpenAI-compatible client. The empty
key was latent — invisible until WP-06 introduced the first
use-case (exo via litellm) that actually needed it. **Wiring path
when the platform wants the litellm-routed UI surface:**
1. LITELLM_MASTER_KEY value at known Vault path (already exists at
   the path consumed by litellm-gateway's own Vault Agent sidecar).
2. Vault Agent sidecar for `open-webui` container rendering the
   key into a credentials file at
   `/Users/admin/.vault-agent-secrets/open-webui/`.
3. Compose rewire for `open-webui` to source `OPENAI_API_KEY` from
   that file (NOT a Docker `environment:` variable, per
   credential-supply doctrine).
This is its own deliverable scope (provisional D-17-26 or wherever
it slots) when the platform actually wants the Open WebUI UI surface
for litellm-routed models. Deferred from D-17-14 because mid-
deliverable scope expansion against tonight's discipline; Vault-
Agent-sidecar work has its own doctrine-clean implementation pattern
that deserves its own scope. **Meta-instance note for T5:** Finding
S is itself an InvenTree-pattern instance — state appeared present
(`OPENAI_API_KEY` env var was set) but working-system substrate
wasn't actually established (the value was empty). Fits the same
"appears established but isn't" pattern as Findings A, K, L, P; the
new wrinkle is that the gap surfaced only when a new consumer
exercised the previously-latent path.

**Chronicle count check.** A–S = 19 InvenTree-pattern findings in
this single deliverable. Pattern of "state appears established but
working-system substrate isn't actually present" is structurally
recurrent in exo bring-up AND in the broader platform integration
surface (Finding S extends the pattern outside the exo install
itself); T5 must surface this as a deliverable-level lesson, not
just per-finding remediation.

---

### Operator decision doctrine — captured here for T5 codification

**Doctrine (proposed D# at T5):** "When in doubt with toolchain, install
the full set." Per operator 2026-05-02: stop being conservative with
disk space and download time on developer toolchain decisions. They
are permanent infrastructure; the platform has plenty of capacity (Mac
Mini at 625 GB free at decision time). When two install options exist
(CLT-only vs full Xcode, minimal Python vs full uv/pip stack,
single-package vs full-toolchain), default to the full set unless
there is a specific reason to constrain. Decision context:
T1.0/T1.5/Xcode escalation rounds in D-17-14 each cost a surface-back
round-trip that a default-to-full posture would have skipped.

---

### T5 deliverable list (preview)

T5 will:
1. Author `docs/architecture-facts/exo-cluster.md` folding all of the
   above plus cluster topology/peer-discovery/RDMA-gating findings
   from later WPs.
2. Author `docs/runbooks/exo-cluster-operations.md` covering start /
   model add / shutdown / recovery from peer-disconnect, plus a
   "deploying exo on a fresh Apple Silicon node" prereq checklist
   (Findings A–G in checklist form).
3. Update `docs/system-prompts/tiers/T4-distributed.md` with actual
   measured latency and pool-size figures from WP-04/05.
4. Codify operator's "install the full set" doctrine in
   `docs/PROJECT_FRAMEWORK.md` §3.5 with next available D# number.
5. Framework flip D-17-14 → DONE in `PROJECT_FRAMEWORK.md` and
   `docs/phase-17/PHASE_17_PLAN_2026-05-01.md`, sync to OpenProject,
   xindex verify.
6. Delete this file.
