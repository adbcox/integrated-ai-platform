# Orchestration-Layer Rebuild Audit — Delivered vs Spec

**Author:** Claude Code (Opus 4.7, 1M context)
**Date:** 2026-05-11
**Anchor:** `docs/architecture-facts/local-ai-workstation-roadmap.md` §17.2 WBS (ingested 2026-05-09 via `feat/foundation-install-track-2` Stage 0a)
**Repo state:** main HEAD `06a31741` (post-Brief A/B/C closeout merges); branch `feat/orchestration-rebuild-audit` cut from this commit
**Companion:** `docs/architecture-facts/local-ai-workstation-roadmap-errata.md` (branch `docs/local-ai-workstation-roadmap-errata` at `3efc27d5` — NOT yet merged to main; surfaces E-001/E-002/E-003 defects in the canonical roadmap)

---

## §1 Summary

The orchestration-layer rebuild has **delivered the spec's primary surfaces with two intentional deviations** (Track 1.B vllm-mlx stunt-double subsystem; OrbStack as container runtime) and **two operator-introduced abstractions beyond §17.2 scope** (Track 1.A LiteLLM proxy + smart fallback; LocalAIConfig migration package). Track 2 agent-stack installs are **partially complete on MacBook**: Aider + Goose + Serena confirmed live; OpenCode + Cline + Continue + OpenHands not installed as primary CLIs (configs/refs only). Mac Studio future-integration readiness is **prepared on the wire**: LiteLLM Tier 3 is env-var driven and flips when `MAC_STUDIO_OLLAMA_BASE_URL` is exported, with an automatic fallback chain to Tier 2 stunt-double, but device-side trust (D-17-115 Phase 2) and Headscale rejoin (KI-010 / KI-011 close-out path) are LAN-gated and untestable from the current off-LAN MacBook session.

Recommendation: prioritize completing Track 2 agent-stack installs on the home Mac Mini (OpenCode + Cline + Continue + OpenHands per §17.2 WBS rows 5.1, 5.5, 5.6, 5.7) ahead of the next on-LAN session, then close KI-010/KI-011/D-17-115 Phase 2 in a single LAN-gated brief. The Track 1.B stunt-double subsystem is a durable substrate that should remain post-Mac-Studio-rejoin as the Mac-Mini-only inference path for MacBook off-LAN work — not a temporary shim.

**Non-scope:** No execution. No installs, no config changes, no §9 row mutations, no roadmap or errata edits. This is the audit deliverable only.

---

## §2 Method

**Spec anchor.** `docs/architecture-facts/local-ai-workstation-roadmap.md` §17.2 Detailed WBS (41 rows across WBS groups 1.x–12.x). Per the canonical doc's "Document status: Corrected implementation plan" header (line 3) and `Date: 2026-05-06`. Companion errata file `local-ai-workstation-roadmap-errata.md` (errata branch) extends the canonical doc with three known defects.

**Track terminology.** "Track 1.A / Track 1.B / Track 2" is operator-defined organizational scaffolding that groups §17.2 WBS rows by execution lane; the roadmap itself does not use Track-N.X numbering. The mapping is:

- **Track 1.A — LiteLLM proxy + smart fallback** → operator-introduced abstraction layer on top of WBS 4.x (Model host setup) + WBS 6.x (Tool configuration) for model routing. Not literally specified by §17.2.
- **Track 1.B — Stunt-double for Mac Studio L3** → operator-introduced workaround NOT in spec. Spec §2.1 assumes Mac Studio Ollama is the primary inference host; stunt-double covers off-LAN MacBook work. Intentional deviation, not a gap.
- **Track 2 — Agent stack** → WBS 5.1–5.7 (Install OpenCode/Goose/Aider/Serena/Cline/Continue/OpenHands) + WBS 6.1–6.6 (Configure each). Spec mapping is verbatim.
- **OrbStack container runtime** → NOT in spec. The roadmap focuses on Ollama; container runtime choice is implicit. OrbStack is the operator's choice for Docker-shaped MCP servers (e.g., openhands sandbox).
- **LocalAIConfig migration package** → NOT in spec. Operator-introduced portable-config substrate for travel-Mac bootstrap. Goes beyond §17.2 scope; closes Phase 1 cross-host portability that §17.2 doesn't address.

**Inventory probes.** All inventory data captured against main HEAD `06a31741` via direct filesystem inspection on the MacBook (operator's current work surface). Mac Studio reachability test (`ping 192.168.10.142`) failed (100% packet loss); Headscale (`tailscale status`) reported logged-out + control-server unreachable — both consistent with the off-LAN session-context.

**Classification rubric (§5).** Four buckets:

1. **DELIVERED-AS-SPEC** — landed artifact matches §17.2 row.
2. **DELIVERED-WITH-DEVIATION** — landed substantively but differs from spec (e.g., vllm-mlx substitutes for Ollama-on-Mac-Studio at Tier 2). Document the deviation; do not count as a gap.
3. **DELIVERED-BUT-NOT-SPEC** — landed beyond what §17.2 required (e.g., subagent definitions, 6 thematic CRs, Phase 17 closeout audit infrastructure itself).
4. **SPECIFIED-BUT-NOT-DELIVERED** — real gap. §17.2 row exists, no landed artifact on main.

---

## §3 Roadmap §17.2 WBS as spec

§17.2 Detailed WBS, verbatim row count:

| WBS group | Row count | Subject |
|---|---:|---|
| 1.x | 3 | Governance and architecture (rename to Local AI Workstation; lane policy; permission profiles) |
| 2.x | 3 | Host/network setup (Thunderbolt Bridge; LAN fallback; firewall Ollama) |
| 3.x | 3 | Artifact and directory setup (local tree; QNAP mount; rsync mirror scripts) |
| 4.x | 3 | Model host setup (Ollama on Mac Studio; pull models; record versions) |
| 5.x | 7 | Agent client installation (OpenCode/Goose/Aider/Serena/Cline/Continue/OpenHands) |
| 6.x | 6 | Tool configuration (OpenCode/Goose/Aider/Serena/Continue/Cline) |
| 7.x | 2 | Worktree isolation (script; policy enforcement) |
| 8.x | 4 | Benchmark and verifier integration (JSONL schema; wrappers; benchmark matrix; verifier gates) |
| 9.x | 3 | Workstation workflows (Goose recipes; task brief template; Plane draft template) |
| 10.x | 2 | Zabbix monitoring (checks; dashboards) |
| 11.x | 3 | Promotion gates (A/B; Serena impact; promotion memo) |
| 12.x | 2 | Documentation and handoff (handoff package; v1 baseline freeze) |

**Total: 41 rows.**

Representative verbatim quotes (one per group):

> 1.2 | Define lane policy | Claude/Codex | `AGENT_LANE_POLICY.md` | Each tool has role and non-role
> 2.1 | Configure Thunderbolt Bridge | Human/Codex | static IPs | Mac Mini reaches Mac Studio on `10.55.0.1`
> 4.1 | Install/update Ollama on Mac Studio | Human/Codex | Ollama service | `/api/tags` passes
> 5.4 | Install Serena | Human/Codex | CLI/MCP | `serena --version`
> 6.4 | Configure Serena MCP | Codex | MCP config | symbol lookup works
> 7.1 | Create worktree script | Codex | shell script | creates four worktrees
> 8.2 | Create wrapper templates | Codex | scripts | run emits artifact stub
> 9.1 | Create Goose recipes | Codex | YAML recipes | first 8 recipes exist
> 11.1 | Run OpenCode vs Aider A/B | Human/Codex | JSONL runs | same task, both tools
> 12.2 | Freeze v1 baseline | Human | tag/archive | baseline reproducible

---

## §4 Delivered inventory per Track

### §4.A Track 1.A — LiteLLM proxy + smart fallback

**Spec recap.** Roadmap §1.3 calls for Ollama-on-Mac-Studio reachable via Thunderbolt-preferred / LAN-fallback. The roadmap does NOT specify LiteLLM as the routing layer — the spec assumes agents talk directly to Ollama via native or OpenAI-compatible endpoints. LiteLLM is an operator-introduced abstraction inserted between agent clients and the inference layer to provide model-name aliases, automatic tier-fallback, and one config-file routing surface.

**Delivered on main `06a31741`:**

| Artifact | Path | Notes |
|---|---|---|
| LiteLLM proxy config (canonical, 3 tiers) | `configs/litellm/config.yaml` | Tier 1 ollama 11434 / Tier 2 vllm-mlx 8500 stunt-double / Tier 3 Mac Studio env-driven |
| Symlinked operational config | `~/local-ai-workstation/configs/litellm/config.yaml` → repo | Confirmed live symlink (target file matches) |
| Backup snapshot | `~/local-ai-workstation/configs/litellm/config.yaml.bak-pre-symlink-2026-05-10` | Pre-symlink-migration safety copy |
| LaunchDaemon plist | `deployment/launchd/com.adriancox.litellm.plist` | Persistent service on port 4000 |

**Fallback chain (operational behavior):**

```yaml
fallbacks:
  - qwen3-coder-30b: ["qwen3-coder-30b-stunt-double"]
```

Mac Studio Tier 3 named `qwen3-coder-30b` auto-falls-back to Tier 2 stunt-double `qwen3-coder-30b-stunt-double` when the env-var `MAC_STUDIO_OLLAMA_BASE_URL` is unset OR Tier 3 is unreachable. This is the "smart fallback" delivered.

**Gap.** None. The operator-introduced abstraction is substantively delivered and matches the on-the-wire behavior described in `CLAUDE.md` §"Current Inference Stack".

### §4.B Track 1.B — Stunt-double for Mac Studio L3

**Spec recap.** Not in §17.2. The roadmap's Tier-2/Tier-3 layering (Mac Studio Ollama with Thunderbolt + LAN fallback) does not contemplate a local-Mac-Mini-or-MacBook stunt-double substitute. Track 1.B is an operator-introduced subsystem that fits a substantive Qwen3-Coder-30B inference path onto MacBook (32 GB unified memory) via MLX-native 3-bit quantization while Mac Studio is off-LAN.

**Delivered on main `06a31741`:**

| Artifact | Path | Notes |
|---|---|---|
| vllm-mlx serving stunt-double | port 8500 (live; per CLAUDE.md L243) | serves `mlx-community/Qwen3-Coder-30B-A3B-Instruct-3bit` via raullenchai/vllm-mlx fork |
| Persistent launchd plist (vllm-mlx) | `deployment/launchd/com.adriancox.vllm-mlx.plist` | Default Tier-2 stunt-double |
| Ollama stunt-double plist (DEMOTED) | `deployment/launchd/com.adriancox.ollama-stunt-double.plist` (.plist.disabled on disk) | One-step rollback preserved (per CLAUDE.md L244) |
| Stunt-double workstation home | `~/local-ai-workstation/stunt-double-mac-studio/` | Operational substrate for stunt-double runtime |
| MLX integration test artifact | `docs/orchestration-layer-build-mlx-integration-test.md` | Cross-referenced from CLAUDE.md |
| Doctrine | `docs/architecture-facts/model-provenance.md`, `model-provenance-doctrine.md` | Path B (operator-accepted) verdict-source for hardware-blocked scans (KI-010) |

**Known issues.** KI-010 (Qwen3-Coder-30B-A3B-Instruct provenance scan deferred to Mac Studio post-Headscale-resolution) and KI-011 (concurrent-load N=3-5 validation deferred to Mac Studio) both track the stunt-double-vs-Mac-Studio handoff.

**Gap.** None on the deliverable; the deviation-from-spec is intentional and substrate is the durable post-Mac-Studio-rejoin path for MacBook work.

### §4.C Track 2 — Agent stack

**Spec recap.** §17.2 WBS rows 5.1–5.7 (install seven agents) + 6.1–6.6 (configure six). Verbatim:

- 5.1 OpenCode — `opencode --version`
- 5.2 Goose — `goose --version`
- 5.3 Aider — `aider --version`
- 5.4 Serena — `serena --version`
- 5.5 Cline — VS Code extension visible
- 5.6 Continue — VS Code extension visible
- 5.7 OpenHands — sandbox launches

**Delivered on main `06a31741` + install state on MacBook:**

| Agent | Spec target version (§3.2 as of 2026-05-06) | MacBook install state | Confirmed publisher | Notes |
|---|---|---|---|---|
| Aider | latest stable | `aider 0.86.2` at `/opt/homebrew/bin/aider` (Homebrew bottle, 2026-05-07) | Aider-AI/aider (correct upstream; verified via dist-info) | ✓ live |
| Goose | v1.33.1 (per §3.2) | `goose 1.33.1` at `/opt/homebrew/bin/goose` (Mach-O arm64 binary) | Block Goose (NOT pressly/goose — the pressly Homebrew formula reports "Not installed" and conflicts with `block-goose-cli`) | ✓ live |
| Serena | v1.2.0 (per §3.2) | `Serena 1.2.0` at `/Users/adriancox/.local/bin/serena`; `~/.serena/` config + memories present | oraios/serena (correct upstream per errata E-001 retry) | ✓ live |
| OpenCode | v1.14.40 (per §3.2) | NOT installed system-wide (`which opencode` → not found). Only present as `configs/opencode/` in repo and `~/repos/ref-docs/opencode/` reference clone | n/a | ✗ install pending |
| Cline | current stable VS Code extension | NOT installed (`which cline` → not found). Spec calls for VS Code extension, not CLI; this audit cannot confirm extension state from CLI surface | n/a | ✗ extension state untested |
| Continue | current stable VS Code extension | NOT installed (`which continue` → shell builtin collision; no agent binary). Same caveat as Cline | n/a | ✗ extension state untested |
| OpenHands | v1.7.0 (per §3.2) | Partial install state: `~/.openhands/openhands.db` exists; no `openhands` CLI binary. Spec §15.1 calls for sandbox-only via Docker; OrbStack-managed | n/a (Docker-image-based) | ⚠ install state ambiguous |

**Spec-corrected install command for Serena** (per errata E-001): `uv tool install -p 3.13 serena-agent@latest --prerelease=allow` — the roadmap's literal `uv tool install serena` is a PyPI namespace-collision trap. Errata file documents this; canonical roadmap is preserved as-ingested.

**Configuration substrate delivered on main:**

| Artifact | Path | Notes |
|---|---|---|
| Agent lane policy doc | `docs/agent-policy/AGENT_LANE_POLICY.md` | Each tool has role and non-role (WBS 1.2 spec acceptance criterion met) |
| Permission profile doc | `docs/agent-policy/AGENT_PERMISSION_PROFILES.md` | Read/write/destructive rules explicit (WBS 1.3) |
| Worktree assignment policy | `docs/agent-policy/AGENT_WORKTREE_POLICY.md` | Per-agent worktree mapping |
| Aider wrappers + utilities | `bin/aider_*.{py,sh}` (21 files) | Includes `aider_local.sh`, `aider_context_pack.py` (D-17-136 RAG), `aider_verifier.py`, `aider_loop.sh`, etc. |
| Goose wrapper | `agent-orchestration/scripts/wrap-goose.sh` | Brief A propagation of wrap-opencode verifier-fix pattern |
| Aider wrapper (artifact-emitter) | `agent-orchestration/scripts/wrap-aider.sh` | Same |
| OpenCode wrapper (artifact-emitter) | `agent-orchestration/scripts/wrap-opencode.sh` | Brief A verifier-fix anchor |
| Worktree-creation script | `agent-orchestration/scripts/create-agent-worktrees.sh` | WBS 7.1 spec acceptance criterion |
| Goose recipes (8) | `agent-orchestration/recipes/00{1..8}-*.yaml` | WBS 9.1 spec calls for "first 8 recipes exist" — count matches exactly |
| Task brief template | `agent-orchestration/templates/task-brief.json` | WBS 9.2 |
| Plane draft template | `agent-orchestration/templates/plane-draft.md` | WBS 9.3 |
| Artifact schema (JSONL) | `~/local-ai-workstation/AGENT_ARTIFACT_SCHEMA.json` | WBS 8.1 |
| System prompt library v1.0.0 | `config/prompts/library/v1.0.0/*` (8 prompts + 4 personas + INDEX + CATALOG) | D-17-121; post-consolidation merged from docs/system-prompts/ |
| Persona loader | `bin/persona_loader.py` (sibling: `tests/unit/test_persona_loader.py`) | API: `load_persona(id, version="latest") -> str` |

### §4.D Container runtime — OrbStack

**Spec recap.** §17.2 does not call out a container runtime. The roadmap focuses on Ollama as the model host and only references Docker-shaped artifacts implicitly (e.g., §15 OpenHands sandbox runs in a container).

**Delivered on main `06a31741` + install state:**

| Artifact | Path | Notes |
|---|---|---|
| OrbStack | `/Applications/OrbStack.app` (v2.1.1, commit 5938f7b) | Operator-installed |
| docker shim | `~/.orbstack/bin/docker` → `OrbStack.app/Contents/MacOS/xbin/docker` | Docker CLI provided via OrbStack |
| docker-compose shim | `~/.orbstack/bin/docker-compose` → `OrbStack.app/Contents/MacOS/xbin/docker-compose` | Same |

**Gap.** None against §17.2. OrbStack is an operator runtime choice not in spec; included here for completeness because the brief flags it as a Track in §4.D.

### §4.E LocalAIConfig migration package

**Spec recap.** §17.2 does not anticipate a portable-config substrate for travel-Mac bootstrap. The spec assumes a single Mac Mini orchestration host.

**Delivered (separate repo at `/Users/adriancox/LocalAIConfig/`):**

| Artifact | Path | Notes |
|---|---|---|
| Package root | `/Users/adriancox/LocalAIConfig/` (separate git repo, HEAD `d327bd2`) | Created 2026-05-07 |
| Migration status doc | `LocalAIConfig/MIGRATION_STATUS.md` | What's done / what's pending; GATE 2 + GATE 4 closed 2026-05-08 Tokyo travel session |
| Home system inventory | `LocalAIConfig/HOME_SYSTEM_INVENTORY.md` | Snapshot of home Mac Mini state |
| Travel bootstrap doc | `LocalAIConfig/TRAVEL_MAC_BOOTSTRAP.md` | Standalone setup guide |
| Roadmap doc | `LocalAIConfig/ROADMAP.md` | Package-local roadmap (distinct from canonical workstation roadmap) |
| Inventory snapshots | `inventory/{brewfile.Brewfile,ollama_list_mac_studio.json,tool_versions.txt,...}` | Captured 2026-05-07 |
| Agent config templates | `agents/{aider,goose,opencode,continue,cline,serena,openhands}/` | Pointers + travel-mode templates |
| Schemas | `schemas/*.json` | Artifact schemas |
| Scripts | `scripts/{healthcheck_home.sh,healthcheck_travel.sh,install_base_tools_macos.sh,install_travel_node.sh}` | Bootstrap/healthcheck |

**Gap.** None against §17.2 (out-of-spec by design); the package is a deliberate Phase 17 extension covering the travel-mode operational gap the spec didn't address.

### §4.F Additional Tracks the roadmap defines

§17.2 does not subdivide work into Tracks; the WBS-group decomposition (1.x–12.x) is the spec's own organizational layer. The four Tracks above are operator-defined organizational scaffolding for the rebuild work. No further Tracks need to be inventoried — all 41 §17.2 rows are covered in the §5 gap classification below.

---

## §5 Gap classification table

Bucket legend: **AS-SPEC** / **WITH-DEVIATION** / **BUT-NOT-SPEC** / **NOT-DELIVERED**.

| WBS | Deliverable | Bucket | Evidence / note |
|---|---|---|---|
| 1.1 | Rename architecture to Local AI Workstation | AS-SPEC | Canonical doc title: "Local Open-Source AI Workstation Architecture and Implementation Roadmap" |
| 1.2 | Define lane policy (`AGENT_LANE_POLICY.md`) | AS-SPEC | `docs/agent-policy/AGENT_LANE_POLICY.md` present on main |
| 1.3 | Define permission profiles (`AGENT_PERMISSION_PROFILES.md`) | AS-SPEC | `docs/agent-policy/AGENT_PERMISSION_PROFILES.md` present on main |
| 2.1 | Configure Thunderbolt Bridge | NOT-DELIVERED on MacBook (host-applicability per errata E-003); applies to Mac Mini ↔ Mac Studio only | Mac Studio currently NOT joined to Headscale; LAN-gated |
| 2.2 | Configure LAN fallback | WITH-DEVIATION | LiteLLM `MAC_STUDIO_OLLAMA_BASE_URL` env-var-driven Tier 3 supersedes hardcoded LAN endpoint; auto-falls-back via Tier 2 |
| 2.3 | Firewall Ollama (restricted port 11434) | NOT-DELIVERED (gap pending Mac Studio rejoin) | Mac Studio off-LAN; firewall config not testable from MacBook |
| 3.1 | Create local directory tree (`~/local-ai-workstation/`) | AS-SPEC | Tree confirmed: agents/, configs/, scripts/, agent_runs/, models/, etc. |
| 3.2 | Mount QNAP artifact path | NOT-DELIVERED on MacBook (off-LAN); home Mac Mini config retained in LocalAIConfig MIGRATION_STATUS | Travel session does not exercise QNAP mount |
| 3.3 | Add rsync mirror scripts | WITH-DEVIATION | `LocalAIConfig/scripts/` ships travel-mode + healthcheck scripts; canonical rsync mirror is in repo `scripts/` family (D-17-37 artifact-ingest substrate) |
| 4.1 | Install/update Ollama on Mac Studio | NOT-DELIVERED-VERIFIABLE | Mac Studio off-LAN; per `~/local-ai-workstation/inventory/ollama_list_mac_studio.json` (2026-05-07 snapshot) Ollama ran with 7 models pre-Tokyo |
| 4.2 | Pull required models | WITH-DEVIATION | Pre-Tokyo snapshot confirmed 7 models on Mac Studio; locally MLX-quant via vllm-mlx covers Qwen3-Coder-30B on MacBook |
| 4.3 | Record versions | AS-SPEC | `~/local-ai-workstation/inventory/tool_versions.txt` + `LocalAIConfig/inventory/` snapshots |
| 5.1 | Install OpenCode | NOT-DELIVERED | `which opencode` not found; configs/ + ref-docs/ only |
| 5.2 | Install Goose | AS-SPEC | `goose 1.33.1` at `/opt/homebrew/bin/goose` (Block Goose, NOT pressly/goose — verified via `brew info` showing pressly variant "Not installed") |
| 5.3 | Install Aider | AS-SPEC | `aider 0.86.2` at `/opt/homebrew/bin/aider` (Aider-AI/aider) |
| 5.4 | Install Serena | AS-SPEC (with errata E-001 install-command correction) | `Serena 1.2.0` at `~/.local/bin/serena` |
| 5.5 | Install Cline | NOT-DELIVERED (extension state untested from CLI) | VS Code extension; not exercised on MacBook |
| 5.6 | Install Continue | NOT-DELIVERED (extension state untested from CLI) | VS Code extension; not exercised on MacBook |
| 5.7 | Install OpenHands | NOT-DELIVERED-FULLY | `~/.openhands/openhands.db` exists; no CLI binary; sandbox launch not verified |
| 6.1 | Configure OpenCode (`opencode.json`) | BUT-NOT-SPEC (configs present without install) | `configs/opencode/` shipped; agent itself not installed |
| 6.2 | Configure Goose profiles | AS-SPEC | `~/local-ai-workstation/configs/goose/` + `LocalAIConfig/agents/goose/` |
| 6.3 | Configure Aider (`.aider.*` files) | AS-SPEC | `.aider.conf.yml` repo-local (with `read: CONVENTIONS.md`); architect mode wrappers in `bin/` |
| 6.4 | Configure Serena MCP | AS-SPEC | `~/.serena/serena_config.yml` + memories; per-workspace pattern per spec §11.3 |
| 6.5 | Configure Continue | NOT-DELIVERED | Continue extension not installed |
| 6.6 | Configure Cline | NOT-DELIVERED | Cline extension not installed |
| 7.1 | Create worktree script | AS-SPEC | `agent-orchestration/scripts/create-agent-worktrees.sh` + `~/local-ai-workstation/worktrees/` (4 worktrees: opencode, openhands, cline, aider) |
| 7.2 | Enforce worktree policy | AS-SPEC | `docs/agent-policy/AGENT_WORKTREE_POLICY.md` |
| 8.1 | Create JSONL schema | AS-SPEC | `~/local-ai-workstation/AGENT_ARTIFACT_SCHEMA.json` + `LocalAIConfig/schemas/` |
| 8.2 | Create wrapper templates | AS-SPEC | `wrap-opencode.sh`, `wrap-aider.sh`, `wrap-goose.sh` (Brief A verifier fix propagated to all three) |
| 8.3 | Define benchmark matrix | AS-SPEC | `benchmark/` family + `bin/aider_benchmark.py` + `bin/aider_envelope_benchmark.py` |
| 8.4 | Define verifier gates | AS-SPEC | `bin/aider_verifier.py`; `config/prompts/library/v1.0.0/07-deepseek-verifier-prompt.md` |
| 9.1 | Create Goose recipes (8 expected) | AS-SPEC | `agent-orchestration/recipes/00{1..8}-*.yaml` — exact 8-recipe count match |
| 9.2 | Create task brief template | AS-SPEC | `agent-orchestration/templates/task-brief.json` + 3 worked TASK-0001-* briefs |
| 9.3 | Create Plane draft template | AS-SPEC | `agent-orchestration/templates/plane-draft.md` (Plane retired post-D-17-04; template retained for historical reference) |
| 10.1 | Add Zabbix checks | AS-SPEC (delivered in Phase 17 D-17-46/119) | Scraparr + QNAP Syncthing template + zabbix-trapper-pattern.md substrate |
| 10.2 | Add dashboards | AS-SPEC | `docker/grafana-provisioning/dashboards/arr-stack-overview-p18.json` + zabbix-overview-p14 |
| 11.1 | Run OpenCode vs Aider A/B | NOT-DELIVERED (gated on 5.1 OpenCode install) | Cannot run A/B without both tools live |
| 11.2 | Run OpenCode with/without Serena | NOT-DELIVERED (gated on 5.1) | Same gate as 11.1 |
| 11.3 | Review promotion (promotion memo) | WITH-DEVIATION | `docs/architecture-facts/promotion-criteria.md` + per-cell promotion log in D-17-53 chronicle (Goose+qwen3-coder cell first measured datapoint) |
| 12.1 | Create handoff package | BUT-NOT-SPEC-richer | Brief A/B/C closeout audit infrastructure (this audit + `phase-17-closeout-audit-2026-05-11.md` + `system-prompts-consolidation-audit-2026-05-11.md`) substantially exceeds the spec's handoff-package requirement |
| 12.2 | Freeze v1 baseline (tag/archive) | NOT-DELIVERED (phase-17-final tag deferred until Brief D lands) | Brief D LAN-session gates the tag-cut |

**BUT-NOT-SPEC entries (work landed beyond §17.2):**

- LocalAIConfig migration package (entire package; §4.E above)
- vllm-mlx stunt-double subsystem (entire Track 1.B; §4.B above)
- LiteLLM proxy as the routing layer (entire Track 1.A; §4.A above)
- 4 subagent definitions at `.claude/agents/{state-verifier,brief-author,doctrine-author,provenance-runner}.md` + scaffolded `.claude/agent-memory/` per agent
- 6 thematic Change Records CR-17-001 through CR-17-006 (§9 retrospective Phase 18 escalation set)
- F7 false-positive completion correction infrastructure (Brief C scope-split D-17-54 → D-17-137; doctrine response in audit §10.1)
- Cisco Model Provenance Kit + 13-model backfill register (D-17-122) — outside §17.2 model-host scope
- Caddy internal-CA trust distribution (D-17-115) — outside §17.2 scope
- D-17-95 work-routing doctrine (TIER 1 Aider-eligible / TIER 2 Claude Code) — extends §11.1 A/B promotion concept into a daily work-routing rubric
- D-17-136 Retrieval-Augmented Aider context pack generator — extends §8.4 verifier gates with retrieval substrate

**Counts:** AS-SPEC 22 / WITH-DEVIATION 5 / BUT-NOT-SPEC 9 / NOT-DELIVERED 14.

Of the 14 NOT-DELIVERED rows, 11 are LAN-gated or Mac-Studio-rejoin-gated (rows 2.1, 2.3, 3.2, 4.1, 11.1, 11.2 plus 5.1/5.5/5.6/5.7/6.5/6.6 awaiting agent installs on the home Mac Mini); only 3 are off-LAN-executable now (5.1 OpenCode install on MacBook, 12.2 baseline tag pending Brief D).

---

## §6 Mac Studio future-integration readiness

Mac Studio (M3 Ultra, 96 GB unified, `192.168.10.142`) was physically delivered 2026-05-01 (D-17-15) and is currently NOT joined to Headscale per `CLAUDE.md` L95 and KI-010. The audit assesses on-the-wire readiness for the Mac Studio rejoin.

### §6.A Mac-Studio-READY (prepared on main; no action needed at rejoin)

| Item | Evidence | Behavior at rejoin |
|---|---|---|
| LiteLLM Tier 3 entry | `configs/litellm/config.yaml` `qwen3-coder-30b` row with `api_base: os.environ/MAC_STUDIO_OLLAMA_BASE_URL` | Export the env var → Tier 3 goes live; fallback chain still protects Tier 2 |
| LiteLLM auto-fallback chain | `fallbacks: - qwen3-coder-30b: ["qwen3-coder-30b-stunt-double"]` | Tier 3 unreachable → automatic Tier 2 stunt-double serve |
| vllm-mlx stunt-double substrate | `deployment/launchd/com.adriancox.vllm-mlx.plist` (persistent) | Stays live post-rejoin as the durable MacBook off-LAN path (NOT a temporary shim) |
| Pre-Tokyo Mac Studio inventory | `~/local-ai-workstation/inventory/ollama_list_mac_studio.json` (7 models snapshot 2026-05-07) | Establishes the model set that should be re-verified at rejoin |
| Cisco Provenance Kit deployment plan | `model-provenance.md` + `KI-010` | Pull provenance scan execution to Mac Studio (96 GB clears the BF16 fingerprint step that fails on Tier 1/2 hardware) |
| D-17-14 exo distributed inference cluster | DONE on main (commit chain 86600b8+0d6ebf3+a025827+1dc2f3b+ede9480+726725a+f90ce04) | Substrate ready for distributed inference when operator schedules; upstream-blocked per D-17-25 Findings U+V (single-node placement on Mac Mini works and is the demo path) |
| Ollama-stunt-double rollback path | `com.adriancox.ollama-stunt-double.plist.disabled` | One-step rollback if vllm-mlx misbehaves post-rejoin |

### §6.B Mac-Studio-NOT-READY (work pending; action required)

| Item | Evidence | Action at rejoin |
|---|---|---|
| Headscale rejoin runbook for Mac Studio | NO dedicated runbook on main (`docs/runbooks/headscale-client-onboarding.md` covers generic clients; `macbook-headscale-enrollment.md` covers MacBook specifically; no `mac-studio-headscale-enrollment.md`) | Author a Mac-Studio-specific Headscale enrollment runbook OR confirm the generic runbook covers Mac Studio with no host-specific deviations |
| KI-010 closure (Qwen3-Coder-30B-A3B-Instruct provenance scan on Mac Studio) | OPEN, `accept-as-deferred-pending-on-LAN-session` | Run Cisco kit scan against the upstream HF model on Mac Studio; 96 GB clears the BF16 fingerprint constraint that hard-stops on Tier 1/2 |
| KI-011 closure (concurrent-load N=3-5 validation for vllm-mlx) | OPEN, same disposition | Run the concurrent-load benchmark; if the stunt-double substrate is moved to Mac Studio, this validates the larger-RAM placement |
| D-17-115 Phase 2 (Caddy CA trust on Mac Studio) | Phase 1 DONE off-LAN (macOS trust script + KI-012 + runbook); Phase 2 LAN-gated per Phase-17 closeout Brief C carry-forward | Extract Caddy CA cert via `docker exec` on Mac Mini → commit `deployment/caddy/internal-root.crt` → run trust script on Mac Studio + Mac Mini + MacBook |
| Mac Studio Headscale + Tailscale node-join verification | `tailscale status` on MacBook today: logged out, control server unreachable (vpn.reivernet.com:8082 timeout) — entire Headscale fleet currently inaccessible from off-LAN session | First LAN session must re-establish Headscale control-server reachability; then join Mac Studio per the runbook |
| Mac Studio firewall (Ollama port 11434 restriction) | Not in spec for the MacBook side; WBS 2.3 acceptance criterion is "only trusted hosts can reach" — requires Mac Studio host-side config | Apply firewall rules on Mac Studio after Headscale rejoin so only Mac Mini Pro reaches port 11434 |
| Cisco Provenance Kit deployment to Mac Studio host | Kit deployed at `~/repos/model-provenance-kit/` on Mac Mini + MacBook per CLAUDE.md L252; NOT confirmed on Mac Studio | Deploy kit to Mac Studio at rejoin for KI-010 closure |

### §6.C Mac Studio readiness summary

LiteLLM-side readiness is essentially complete: a single env-var export and one Cisco kit deployment will close KI-010 and bring Tier 3 live. Headscale rejoin itself is the load-bearing gate; once it lands, the substrate flips from "stunt-double-only" to "Tier-3-preferred-with-stunt-double-fallback" without further config changes.

---

## §7 Recommendations / next-step prioritization

Ordered by leverage (highest-leverage gap first):

1. **OpenCode install on home Mac Mini (WBS 5.1 + 6.1 unblock).** Highest leverage: unblocks WBS 11.1 (OpenCode vs Aider A/B), 11.2 (Serena impact), and brings the four-agent baseline (OpenCode + Aider + Goose + Serena) to spec on the home host. Off-LAN-executable now. Errata E-002 warns the roadmap's §22 OpenCode source URL likely points at the wrong repo; use the official `curl` install per opencode.ai. Brief Stage 1 of Track 2 dodged the E-002 trap on prior install attempts.
2. **Brief D LAN-session bundle.** Headscale rejoin → Mac Studio rejoin → KI-010 scan → KI-011 concurrent-load benchmark → D-17-115 Phase 2 cert distribution → exo distributed-inference smoke. Single LAN-gated brief covering all the Mac-Studio-NOT-READY rows in §6.B.
3. **Cline + Continue VS Code extension state probe.** Open VS Code on the home Mac Mini, verify extension visibility per WBS 5.5/5.6 acceptance criteria; document in `LocalAIConfig/agents/{cline,continue}/README.md`. Closes the "extension state untested" gap from §4.C.
4. **OpenHands sandbox launch verification.** `~/.openhands/openhands.db` indicates partial state; run the OrbStack-managed sandbox per §15.1 and confirm `sandbox launches` acceptance criterion. Off-LAN-executable now on the home Mac Mini.
5. **WBS 12.2 v1 baseline freeze.** Cut `phase-17-final` tag after Brief D lands and all 8 phase-17-closeout-audit criteria satisfy. Phase-17-final is the spec's WBS 12.2 acceptance criterion ("baseline reproducible").
6. **F7 spot-check sweep of §18.O Goose-pipeline-authored §9 DONE rows** (per Phase 17 Brief C §10.1 audit handoff). Carry-forward risk-register row already in place; execute as part of Brief D scope.
7. **Roadmap errata branch merge to main.** `docs/local-ai-workstation-roadmap-errata` branch at `3efc27d5` is unmerged; merging makes E-001/E-002/E-003 visible on main for future install sessions. Low-effort but improves discoverability.
8. **Phase 18 CR mapping cross-check.** CR-17-001 through CR-17-006 retrospective escalations cover 39 §9 deliverables; verify the orchestration-layer-rebuild work that is NOT-DELIVERED maps cleanly to one of these CRs OR a fresh Phase 18 row. Audit-only; no scope mutation.

---

## §8 Risk register — known unknowns

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Roadmap version drift since 2026-05-09 ingest | LOW | Canonical doc inspected this audit is preserved as-ingested per errata maintenance rule; no in-place edits | Errata file is the canonical drift-tracker; this audit cites errata branch HEAD `3efc27d5` |
| Track 2 install completeness mis-stated for Cline / Continue | MEDIUM | Spec acceptance criterion is "extension visible" in VS Code, which is NOT verifiable from CLI; this audit reports both as NOT-DELIVERED but they may already be installed | Open VS Code on home Mac Mini and verify; update LocalAIConfig/agents/{cline,continue}/README.md with extension state |
| LocalAIConfig migration completeness asymmetric | MEDIUM | Live config is split across `/Users/adriancox/repos/integrated-ai-platform/` AND `~/local-ai-workstation/` AND `~/LocalAIConfig/`. This audit attempts to disambiguate via path provenance, but a live-vs-stale check at the host level (home Mac Mini) is the authoritative answer | Run `LocalAIConfig/scripts/healthcheck_home.sh` on the home Mac Mini and reconcile against this audit |
| Mac Studio inventory snapshot stale | LOW-MEDIUM | `~/local-ai-workstation/inventory/ollama_list_mac_studio.json` is dated 2026-05-07 (~4 days old at audit time, but pre-Tokyo travel session); Mac Studio state at rejoin may have drifted if anyone has run pulls/deletes against it | Re-snapshot at Brief D rejoin; treat current snapshot as historical-baseline only |
| pressly/goose vs Block Goose collision recurrence | LOW | This audit verified `brew info goose` reports the pressly variant "Not installed" and that the installed `goose 1.33.1` is a Mach-O arm64 binary matching Block Goose's version. If a future `brew install` or `brew upgrade` runs without the `block-goose-cli` flag, the pressly variant could overwrite | `brew pin block-goose-cli` (if installed) OR document the install-tap explicitly in `LocalAIConfig/scripts/install_base_tools_macos.sh` |
| Errata E-002 (§22 OpenCode source URL) unverified | LOW | Roadmap §22 OpenCode URL pointing at `github.com/anomalyco/opencode` is flagged "suspicious, not yet broken" in errata. If an install session follows §22 literally, the install could pull from the wrong upstream | Track 2 OpenCode install must use the official `curl` install from opencode.ai (matches §17.2 row 5.1 acceptance criterion `opencode --version` without binding to a specific repo URL) |
| OpenHands install state ambiguity | MEDIUM | `~/.openhands/openhands.db` exists without an `openhands` CLI binary; spec §15.1 explicitly calls for sandbox-only via Docker/OrbStack, so absence of a CLI binary is consistent with spec, but absence of a `sandbox launches` verification artifact means WBS 5.7 acceptance is not provably met | Run the sandbox once on the home Mac Mini and capture the launch confirmation artifact per §15.1 |
| WBS 11.1/11.2 A/B benchmark execution gap | LOW-MEDIUM | Both rows are gated on WBS 5.1 OpenCode install. If OpenCode is installed but the A/B comparison is skipped at WBS 12.2 baseline-freeze time, the spec's promotion-gate evidence requirement is not satisfied | Brief D scope should include at least one A/B task class (e.g., the bug-fix on a single file task from §5.1 of the implementation schedule) before tag-cut |
| Mac Studio rejoin uncovers Headscale config drift | MEDIUM | Headscale unreachable today (`vpn.reivernet.com:8082` timeout). If the unreachability is caused by control-server side drift, the Mac Studio rejoin runbook may be insufficient | Treat the first LAN session as a Headscale-server health check first; Mac Studio rejoin is downstream |
| Cisco Provenance Kit OOM recurrence on Mac Studio | LOW | KI-010 documents that Tier 1/2 (32 GB) OOMs on the BF16 fingerprint step; Mac Studio's 96 GB should clear it, but the kit's memory model may scale with model size and a 60+ GB BF16 download may approach Mac Studio limits on simultaneous swap pressure | KI-010 closure brief should monitor memory pressure during the scan; surface back if OOM recurs |

---

## End of audit

No execution. Single audit deliverable. Brief D (LAN-session) is the natural next execution context for the §7 prioritization above. Off-LAN-executable items in §7 (OpenCode install, Cline/Continue extension probe, OpenHands sandbox launch, roadmap errata branch merge) can land in interim briefs without LAN dependency.
