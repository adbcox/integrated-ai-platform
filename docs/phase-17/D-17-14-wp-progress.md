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
