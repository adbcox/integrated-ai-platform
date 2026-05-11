# ADR-A-020 — Track 2 Agent Role Codification

**Status:** ACCEPTED
**Date:** 2026-05-11 (PROPOSED); 2026-05-11 (ACCEPTED)
**Acceptance gate:** operator decision via Thread A WP-4 chat session 2026-05-11; Q-1 through Q-7 resolved per §5
**Phase:** 17 (closeout)
**Deliverable:** Thread A WP-4 (Brief D plan-doc handoff)
**Supersedes:** none (this is the first ADR consolidating Track 2 agent roles)
**Related ADRs:** ADR-A-003 (Ollama-first default coding posture); ADR-A-004 (Aider as adapter, not backbone); ADR-A-005 (Claude Code is supervisory or exceptional); ADR-A-014 (NetBox CMDB authority — context); ADR-A-019 (OrbStack container runtime — reserved-but-unauthored at time of writing per `docs/runbooks/foundation-install-status-track-2.md` Stage 0b).

---

## Context

Phase 17 Thread A WP-1 + WP-2 + WP-3 verified that six Track 2 agents are installed and operationally live on the MacBook surface (per `docs/runbooks/foundation-install-status-track-2.md` Stage 1–7 + corroborating capability audits + filesystem evidence): **Aider 0.86.2, Goose 1.33.1, Serena 1.2.0, OpenCode 1.14.41, Continue 1.2.22, OpenHands 1.7** (Cline 3.82.0 also installed on MacBook but is out-of-scope for this ADR per the WP-4 brief — see §5 Q-7).

At time of writing, the work-class × tier × default-agent matrix is **distributed across at least eight independent doctrine documents**: `local-ai-workstation-roadmap.md` §1.2 (host assignment), §4.3 (model assignment), §11–§15 (per-agent roles); `work-routing-doctrine.md` (D-17-95 — three-tier classifier); `goose-capability-boundary.md` (D-17-13 — Goose posture); `aider-intelligence-doctrine.md` (D-17-103 — three-layer Aider guard); `aider-verifier-doctrine.md` (D-17-110 — Layer 1.5 DeepSeek verifier); `model-provenance-doctrine.md` (verdict-source taxonomy affecting routing); `local-prompt-library-doctrine.md` (D-17-90 — persona routing); `integration-audit-doctrine.md` Findings 19/22 (tier-classification + workspace-isolation). Brief D LAN-session execution will inherit and act on these roles per `docs/_planning/phase-17-brief-d-plan-2026-05-11.md` WP-D-07; cross-doctrine reconciliation is currently a brief-author responsibility, which is brittle.

This ADR consolidates the role-codification surface into a single decision record. **No execution. No doctrine doc edits in this commit.** Acceptance of this ADR is downstream of the operator-decision questions enumerated in §5.

## Decision

The six Track 2 agents have their canonical role, work-class binding, LiteLLM tier binding, default model, and capability boundary codified in §2 below. The codification is **evidence-based**: every per-agent row cites the doctrine doc, capability audit, or §9 row that resolves the role. Where existing doctrine is silent or conflicting, the row carries an explicit `Q-NN` flag deferring resolution to the operator decision list in §5.

The codification is structurally cross-cutting: a single Track 2 ADR is chosen over per-agent ADRs because the routing matrix (work-class × tier × default-agent) is intrinsically cross-agent — separate ADRs would duplicate the matrix and risk drift. See §7 for the alternatives considered.

---

## §1 Sources consulted (evidence chain)

This ADR consolidates roles from:

- **Roadmap doctrine (canonical, ingested 2026-05-09):** `docs/architecture-facts/local-ai-workstation-roadmap.md` §0 (executive correction), §1.2 (host assignment), §2.2 (lane policy), §3.2 (versions), §4.1–§4.4 (model strategy), §9 (OpenCode), §10 (Goose), §11 (Serena), §12 (Aider), §14 (Continue), §15 (OpenHands).
- **Roadmap errata:** `docs/architecture-facts/local-ai-workstation-roadmap-errata.md` E-001 (Serena install command), E-003 (Thunderbolt host-applicability — affects Aider/OpenCode endpoint resolution).
- **Work-routing doctrine:** `docs/architecture-facts/work-routing-doctrine.md` (D-17-95 — TIER 1/2/3 classifier + decision tree).
- **Goose capability boundary:** `docs/architecture-facts/goose-capability-boundary.md` (D-17-13 — Posture 1; demoted to Posture 0 per D-17-53 chronicle).
- **Aider intelligence:** `docs/architecture-facts/aider-intelligence-doctrine.md` (D-17-103 — three-layer guard); `docs/architecture-facts/aider-verifier-doctrine.md` (D-17-110 — Layer 1.5).
- **Capability audits:** `docs/_audit/capability/openhands-app-2026-05-01.md` (operator-decided KEEP; canonical image namespace verified).
- **§9 rows:** D-17-13 (Goose), D-17-23 (capability self-knowledge), D-17-90 (prompt library), D-17-93 (Aider routing audit), D-17-94 (Aider operator wrapper), D-17-95 (work-routing doctrine), D-17-101 (Aider doc-authoring Tier-2 reclassification), D-17-103 (Aider three-layer intelligence), D-17-104 (Kimi K2.6 DEFERRED), D-17-109 (Aider performance tuning), D-17-110 (DeepSeek verifier), D-17-111 (Aider stack hardening + Layer 0).
- **LiteLLM config:** `configs/litellm/config.yaml` (T1/T2/T3 tier bindings + auto-fallback chain).
- **Wrapper substrates:** `agent-orchestration/scripts/{wrap-aider,wrap-goose,wrap-opencode}.sh` (implicit routing extracted from `MODEL=` / `LITELLM_MODEL=` resolution lines).
- **Install evidence:** `docs/runbooks/foundation-install-status-track-2.md` Stages 1–7 (✓ all complete per 2026-05-09).

---

## §2 Per-agent role table

Six rows, one per agent. Columns: canonical surface / primary work-class / disallowed / default LiteLLM tier / default model / capability boundaries / posture.

### Aider 0.86.2

| Field | Value | Evidence |
|---|---|---|
| Canonical surface | Mac Mini (primary daily-use); MacBook (roaming) | roadmap §1.2 ("Mac Mini should run … Aider …") |
| Primary work-class | **TIER 1** — bounded code/text edits (≤5 files, no probes, deterministic diff) | `work-routing-doctrine.md` (D-17-95) |
| Disallowed | **TIER 2 doc-authoring** (multi-paragraph chronicle append, doctrine extension, structured finding append) — permanently reclassified | D-17-101 §9 row + `work-routing-doctrine.md` "Aider refusal note" |
| Default LiteLLM tier | T2 stunt-double on MacBook off-LAN; T3 Mac Studio Ollama on-LAN | `configs/litellm/config.yaml` `qwen3-coder-30b` → fallback `qwen3-coder-30b-stunt-double` + `wrap-aider.sh` L100 `LITELLM_MODEL="qwen3-coder-30b"` for litellm-local routing |
| Default models | normal: `qwen3-coder:30b-coding`; architect: `qwen3-coder-next:80B`; editor: `deepseek-coder-v2:16b` or `qwen3-coder:30b-coding` | roadmap §4.3 + `wrap-aider.sh` L86-92 task-class-driven selection |
| Capability boundaries | Five-layer intelligence enforcement: Layer 0 ambiguity guard (D-17-111); Layer 1 diff sanity / deletion-rate guard (D-17-103); Layer 1.5 DeepSeek verifier AGREE/DISAGREE (D-17-110); Layer 2 pre-flight shape detector (D-17-103); Layer 3 outcome telemetry (D-17-103). Overridable via `--skip-preflight` / `--skip-validator` / `--skip-verifier` flags | D-17-103 + D-17-110 + D-17-111 §9 rows; `aider-intelligence-doctrine.md` |
| Posture | **Active production** — daily-use entrypoint `scripts/aider-task.sh` | D-17-94 §9 row; install verified at `/opt/homebrew/bin/aider` 0.86.2 |

### Goose 1.33.1

| Field | Value | Evidence |
|---|---|---|
| Canonical surface | Mac Mini per roadmap §1.2; pairs with native Ollama provider direct to Mac Studio (no LiteLLM hop) | roadmap §1.2 + §10 + D-17-13 WP-03 substrate |
| Primary work-class | **C1b** — narrative chronicle/doctrine notes without quote citations (currently **PARKED Posture 0**) | `goose-capability-boundary.md` + D-17-53 chronicle "Posture 0" demotion |
| Disallowed | **C1a** verbatim-quote-bearing reference docs (SUSPENDED indefinitely for Goose+qwen3-coder:30b cell per D-17-53 Sessions 5/7/8/11/12/13 fabrication evidence). Also disabled per WP-05: `developer` (shell exec + file write), `summon`, `apps`, `chatrecall`, `summarize`, `tom`, `code_execution`, `orchestrator` extensions | D-17-13 WP-05 + D-17-53 chronicle Sessions 11/12/13 evidence |
| Default LiteLLM tier | **Bypasses LiteLLM** — direct native Ollama provider to Mac Studio (per D-17-13 WP-03 substrate); falls back to LiteLLM-local via `wrap-goose.sh` `MODEL_HOST=LiteLLM-local` branch when Mac Studio unreachable | D-17-13 WP-03 + `wrap-goose.sh` L51-66 `probe_model_host` |
| Default model | `qwen3-coder:30b-coding` (per `wrap-goose.sh` L79); LITELLM_MODEL fallback `qwen3-coder-30b` for litellm-local | `wrap-goose.sh` L79-96; roadmap §4.3 ("Goose research/ops: qwen3-coder:30b-coding initially") |
| Capability boundaries | Read-only substrate only: `filesystem-mcp` + `xindex` extensions enabled; write/exec extensions all DISABLED. Operator review mandatory on all output (Posture 0 doctrine: "supervised use only"). No Vault, no docker, no ssh-cross-host | D-17-13 WP-05 `goose-capability-boundary.md` Posture 1 boundary (current cell Posture 0 = stricter) |
| Posture | **Posture 0 — supervised invocation only. Autonomous recipe execution NOT permitted. Manual operator approval required per invocation.** (Q-7 resolution honors D-17-53 Posture-2 → Posture-0 demotion chronicle; no low-risk recipe carve-out — full supervised gate.) First measured cell (Goose+qwen3-coder:30b × C1) demoted from Posture 2 → Posture 1 → Posture 0 across D-17-53 sessions 10–13; C1 split into C1a SUSPENDED + C1b parked | D-17-53 §9 row chronicle (Option B trigger; "Goose dispatch RETIRED for C1a work indefinitely") + Q-7 resolution |

### Serena 1.2.0 (MCP tool, not standalone agent — Q-3 RESOLVED)

**Note:** MCP tool, not standalone agent. Provides LSP-based symbol intelligence consumed by other agents (Cline + Aider + OpenCode + Goose). Row retained for visibility per Q-3 resolution; tier/model columns remain N/A — Serena does not invoke an LLM directly.

| Field | Value | Evidence |
|---|---|---|
| Canonical surface | Per-workspace (`--project /path/to/current/worktree`); install at `~/.local/bin/serena` on MacBook + Mac Mini Pro | roadmap §11.3 ("Avoid a global Serena server"); errata E-001 install command |
| Primary work-class | **Semantic code-intelligence layer** — symbol lookup, references, definitions. Used BY agents (Cline + Aider + OpenCode + Goose), NOT a standalone executor | roadmap §2.2 + §11.1 |
| Disallowed | Not an agent — no LLM consumption surface. Avoid global server posture (silent project-switch risk) | roadmap §11.3 |
| Default LiteLLM tier | **N/A** — MCP tool, not LLM consumer | roadmap §11 |
| Default model | **N/A** — Serena does not call models directly; consumers configure their own model | n/a |
| Capability boundaries | Per-workspace project scope; read-mostly (symbol/reference queries); no Vault access; no production credential interaction | roadmap §11.1 ("Shared semantic code-intelligence layer") + §11.3 |
| Posture | **Active production** — installed v1.2.0 via corrected install command (errata E-001); config at `~/.serena/serena_config.yml` + memories populated | install evidence per WP-1 supplementary probe; `~/.serena/serena_config.yml` exists |

**Note:** Q-3 in §5 asks whether Serena should be classified as an "agent" (row in this table) or "MCP tool" (footnote / sibling doc). Pending resolution, this ADR carries Serena as a row.

### OpenCode 1.14.41

| Field | Value | Evidence |
|---|---|---|
| Canonical surface | Mac Mini per roadmap §1.2 (primary terminal coding executor); MacBook for roaming | roadmap §1.2 + §9.1 ("primary Claude Code-style terminal coding executor candidate") |
| Primary work-class | **OpenCode normal coding** (per §4.3); Plan/Build mode discipline per roadmap §9.5 AGENTS.md template | roadmap §4.3 + §9.5 |
| Disallowed | TIER 2 multi-paragraph doc-authoring (C1a) DISALLOWED — inherits Aider boundary per D-17-101 (Q-2 resolution: OpenCode refuses C1a chronicle/doctrine append; route to Claude Code/Codex) | D-17-101 §9 row + work-routing-doctrine.md "Aider refusal note" (extended by ADR-A-020 to OpenCode) |
| Default LiteLLM tier | T2 stunt-double on MacBook off-LAN; T3 Mac Studio Ollama on-LAN. `wrap-opencode.sh` `probe_model_host` returns Thunderbolt → LAN → LiteLLM-local fallback chain (L51-66) | `wrap-opencode.sh` probe + `configs/opencode/opencode.json` Thunderbolt + LAN-fallback providers |
| Default models | normal: `qwen3-coder:30b-coding`; hard plan: `qwen3-coder-next:80B`; via LiteLLM stunt-double on MacBook: `qwen3-coder-30b-stunt-double` (auto-fallback per `configs/litellm/config.yaml`) | roadmap §4.3 + `configs/opencode/opencode.json` `models` block + LiteLLM fallback chain |
| Capability boundaries | Plan/Build mode discipline (AGENTS.md template per §9.5); safety rules per roadmap §8 permission profiles; `--dangerously-skip-permissions` flag available in v1.14.41 CLI (wrap-opencode uses it on litellm-local path L181 only) | roadmap §8 + §9.5 + `wrap-opencode.sh` |
| Posture | **Active candidate** — installed v1.14.41; PATH-wired in `~/.zshrc:24`; configs/opencode/opencode.json pointing at Mac Studio Ollama with LAN fallback; not yet benchmarked vs Aider (WBS 11.1 deferred to Brief D) | WP-1 install evidence + `~/.opencode/bin/opencode` smoke-test PASS |

### Continue 1.2.22

| Field | Value | Evidence |
|---|---|---|
| Canonical surface | Mac Mini per roadmap §1.2; VS Code extension `continue.continue` installed on MacBook + ~/.continue/ config substrate | roadmap §1.2 + §14.1 + WP-1 supplementary probe |
| Primary work-class | **IDE helper / autocomplete / inline checks** — NOT an autonomous executor | roadmap §2.2 ("Continue | IDE helper/autocomplete/checks | Autonomous executor [= incorrect role]") |
| Disallowed | Use as autonomous executor (explicit incorrect role per roadmap §2.2) | roadmap §2.2 |
| Default LiteLLM tier | **autocomplete: fastest acceptable local model**; per §4.3 "Continue autocomplete: fastest acceptable local model" — implies T1 Ollama 7b for fast tasks (no LiteLLM hop needed for autocomplete latency profile) | roadmap §4.3 |
| Default model | `qwen2.5-coder:7b` (T1 explicit pin per Q-4 resolution; Continue's own config retains runtime override capability via VS Code extension settings) | roadmap §4.3 + Q-4 resolution (explicit T1 pin selected over "fastest acceptable" ambiguity) |
| Capability boundaries | IDE-scoped (VS Code extension); no shell exec via Continue itself; helper role — operator review on every suggestion | roadmap §2.2 + §14.1 |
| Posture | **Active production** — installed v1.2.22; ~/.continue/{config.json,config.yaml,package.json,sessions/sessions.json,index/index.sqlite} populated | WP-1 supplementary probe |

### OpenHands 1.7

| Field | Value | Evidence |
|---|---|---|
| Canonical surface | Sandbox-only via Docker per roadmap §15.1; image `docker.openhands.dev/openhands/openhands:1.7` (operator-verified canonical per WP-2 + capability audit `openhands-app-2026-05-01.md`) | roadmap §15.1 + capability audit |
| Primary work-class | **Sandboxed full-project autonomy experiment** — SWE-bench-like tasks on COPIED repos | roadmap §15.1 |
| Disallowed | Verbatim §15.2: "No canonical repo edits / No direct QNAP write access except artifact export directory / No Vault access / No .env access / No host Docker destructive control / No production service credentials / No persistent unattended autonomy" | roadmap §15.2 (verbatim) |
| Default LiteLLM tier | **T3 Mac Studio Ollama (default — sustained autonomous runs)** per Q-6 resolution. Escape hatch: operator may invoke OpenHands sandbox on T2 vllm-mlx stunt-double for short experimental runs under manual session supervision; sustained autonomous SWE-bench-like batches require T3 to avoid MacBook thermal throttling during travel sessions. | roadmap §4.3 + Q-6 resolution |
| Default model | T3: `qwen3-coder:30b-coding`; T3 hard plan: `qwen3-coder-next:80B`; T2 escape hatch: `qwen3-coder-30b-stunt-double` (short manual-supervised runs only) | roadmap §4.3 + Q-6 resolution |
| Capability boundaries | Verbatim §15.2 (above). Operator-decided KEEP per Phase 17 capability audit 2026-05-01 | roadmap §15.2 + capability audit |
| Posture | **Sandbox-only — KEEP** per capability audit; install v1.7 via Track 2 Stage 6 (smoke-test PASSED 2026-05-09) | Track 2 Stage 6 + capability audit operator-decided KEEP |

---

## §3 Tier-routing matrix

Cross-section of work-class × tier × default-agent. **Cross-references §2 rows; does not introduce new claims.**

| Work-class | T1 (Ollama 7b — fast) | T2 (vllm-mlx stunt-double 30b-3bit — MacBook off-LAN) | T3 (Mac Studio Ollama 30b-coding — on-LAN) | Default agent |
|---|---|---|---|---|
| **C0 fast / autocomplete** | `qwen2.5-coder:7b` (Q-4 explicit pin) | n/a (fast-path stays T1) | n/a | Continue (autocomplete) |
| **C1 bounded code edit (TIER 1)** | n/a | `qwen3-coder-30b-stunt-double` | `qwen3-coder:30b-coding` | Aider |
| **C1 architect / hard plan** | n/a | (vllm-mlx limited to 30b-3bit) | `qwen3-coder-next:80B` | Aider (architect mode) / OpenCode (hard plan) |
| **C1a verbatim-quote reference doc** | n/a | n/a | n/a | **Reserved Claude Code under `claude-local`** — Goose SUSPENDED for this cell per D-17-53 |
| **C1b narrative chronicle / doctrine** | n/a | n/a | n/a | Claude Code (Goose+qwen3-coder:30b at Posture 0 — supervised use only) |
| **C2 IDE-supervised Plan/Act** | n/a | n/a | n/a | Cline (out-of-ADR-scope; queued for Brief D WP-D-07) |
| **TIER 2 doc-authoring (C1a multi-paragraph chronicle/doctrine)** | n/a | n/a | n/a | **Claude Code / Codex** — Aider refuses (D-17-101); OpenCode refuses (Q-2 inherits Aider boundary) |
| **TIER 2 orchestration / probes / Vault** | n/a | n/a | n/a | Claude Code / Codex |
| **TIER 3 frontier escalation** | n/a | n/a | n/a | Claude Code under `claude-pro` |
| **Sandbox SWE-bench-like (sustained autonomous)** | n/a | escape hatch only (operator-supervised short runs) | `qwen3-coder:30b-coding` / `qwen3-coder-next:80B` for hard plan (Q-6 default) | OpenHands (sandbox-only, T3 default) |

**Reading note.** T1 is local Mac Mini / MacBook Ollama 7b for fast tasks; T2 is MacBook off-LAN vllm-mlx serving `mlx-community/Qwen3-Coder-30B-A3B-Instruct-3bit` on port 8500; T3 is Mac Studio Ollama serving `qwen3-coder:30b-coding` env-var-driven via LiteLLM. The LiteLLM auto-fallback chain `qwen3-coder-30b → qwen3-coder-30b-stunt-double` (per `configs/litellm/config.yaml`) means agents requesting T3 transparently downgrade to T2 when Mac Studio is unreachable — no agent-side change needed.

---

## §4 Capability boundaries (per-agent + cross-cutting)

**Cross-cutting boundaries (apply to all 6 agents):**

- **Cross-cutting prohibition (Q-1 resolution):** all Track 2 agents are denied `.env` file access AND cross-host SSH access in their default invocations. OpenHands §15.2 already mandates this for OpenHands; Q-1 generalizes the prohibition to Aider / Goose / Serena / OpenCode / Continue. Operator-authored runbooks providing explicit narrow-scope credential or SSH access are the only sanctioned override path; the override must be invocation-scoped, not session-scoped, and must surface in artifact provenance.
- **Vault:** No agent reads, writes, or rotates Vault secrets directly. Vault interaction is Claude Code / Codex territory (TIER 2 per `work-routing-doctrine.md`). OpenHands §15.2 explicitly forbids.
- **Production canonical repo:** OpenHands forbidden from canonical repo edits per §15.2; other agents may edit canonical repo within their work-class boundaries (Aider TIER 1; Goose Posture 0 supervised; OpenCode/Continue per their roles).
- **`.env` access:** Forbidden for OpenHands per §15.2; not specified for other agents — Q-1 in §5: is `.env` access disallowed for ALL Track 2 agents?
- **Cross-host SSH:** Disabled by default in Goose Posture 0; not specified for other agents — Q-1 sibling.

**Per-agent supplementary boundaries:** see §2 rows for verbatim citations of each agent's disallowed surfaces.

**Provenance gating (cross-cutting, model-side):** Per `model-provenance-doctrine.md`, the LiteLLM Tier 3 entry (`qwen3-coder:30b-coding` on Mac Studio Ollama) inherits an `operator_confirmed` verdict-source classification pending Mac Studio rejoin (per KI-010). The stunt-double T2 entry (`qwen3-coder-30b-stunt-double`) inherits `quantization-of-operator-confirmed-base` per D-17-92 quantization-divergence doctrine. **None of the 6 agents currently route to a model with `verified-specific` provenance** — this is a known-stable position pending Mac Studio rejoin per KI-010, not an audit gap.

**Worktree isolation (cross-cutting per roadmap §6 + §7.2 + integration-audit-doctrine.md Finding 22):** Each agent operates in a dedicated worktree under `~/local-ai-workstation/worktrees/<repo>-<agent>/` (Aider, OpenCode, Cline, Continue, OpenHands, Goose). No agent edits the canonical repo directly. The worktree-creation script (WBS 7.1 — `agent-orchestration/scripts/create-agent-worktrees.sh`) is the authority. This ADR carries the worktree-isolation invariant through to each agent's row by reference; no row enumerates "must use worktree" because it is universally true.

**Artifact emission (cross-cutting per roadmap §7 + §8.2):** Each agent invocation emits a JSONL artifact to `~/local-ai-workstation/agent_runs/<task_id>/<agent>/artifact-{pre,post}-run.json` per the canonical schema at `~/local-ai-workstation/AGENT_ARTIFACT_SCHEMA.json` (13 required fields). The wrapper scripts (`wrap-{aider,goose,opencode}.sh`) implement this; Continue/Cline/OpenHands artifact emission paths are agent-specific (Continue records via VS Code extension; Cline records via extension; OpenHands records via sandbox export). Q-1 sibling: should the ADR mandate JSONL emission for ALL six agents or accept the asymmetry between wrapper-driven (Aider/Goose/OpenCode) and tool-internal (Continue/Cline/OpenHands)?

---

## §5 Resolved decisions (2026-05-11)

Seven decision questions surfaced during PROPOSED authoring (Thread A WP-4 commit `34b6e6dd`). All seven resolved 2026-05-11 via operator decision in the Thread A WP-4 chat session; resolutions are baked into §2 + §3 + §4 above. Resolution log:

| Q# | Question | Resolution | Decision date | Decision source |
|---|---|---|---|---|
| Q-1 | Cross-cutting boundary: should `.env` access + cross-host SSH be explicitly disallowed for ALL Track 2 agents (not just OpenHands per §15.2)? | **YES** — `.env` access AND cross-host SSH denied for all 6 agents in default invocations. Operator-authored runbooks with narrow-scope override are the only sanctioned path; override must be invocation-scoped + surfaced in artifact provenance. Codified as the first bullet of §4 cross-cutting boundaries. | 2026-05-11 | Thread A WP-4 chat session |
| Q-2 | OpenCode work-class — inherit Aider's TIER 1 work-class boundaries (refuse TIER 2 doc-authoring) or operate at TIER 2 by default? | **Inherit TIER 1 boundaries** — OpenCode refuses C1a multi-paragraph doc-authoring per D-17-101 (extended from Aider to OpenCode by this ADR). Frontier-cost discipline retained. Codified in §2 OpenCode "Disallowed" cell + §3 TIER 2 doc-authoring row. | 2026-05-11 | Thread A WP-4 chat session |
| Q-3 | Serena classification — "agent" (row in §2) or "MCP tool" (footnote / sibling doc)? | **MCP tool, not standalone agent** — Serena provides LSP-based symbol intelligence consumed by other agents (Cline + Aider + OpenCode + Goose). Row retained for visibility with explicit annotation; tier/model columns N/A. Codified in §2 Serena row annotation. | 2026-05-11 | Thread A WP-4 chat session |
| Q-4 | Continue model assignment — explicit T1 `qwen2.5-coder:7b` for autocomplete, or "fastest acceptable local model" left runtime-configurable? | **Explicit T1 pin `qwen2.5-coder:7b`** for autocomplete. Continue's own VS Code extension settings retain runtime override capability for IDE-chat use cases. Codified in §2 Continue "Default model" cell + §3 matrix C0 row. | 2026-05-11 | Thread A WP-4 chat session |
| Q-5 | Cline (out-of-scope for this ADR) — when does it earn an ADR row? Sibling ADR? Folded into this one in a v1.1 amendment? | **ADR-A-020 v1.1 amendment** planned post-Brief D WP-D-07 Mac Mini canonical-surface install. This ADR v1.0 scope explicitly excludes Cline; Cline state is "covered separately" pending Brief D execution evidence. NOT a sibling ADR — v1.1 amendment keeps the agent-routing matrix in a single file. | 2026-05-11 | Thread A WP-4 chat session |
| Q-6 | OpenHands sandbox tier — should sandbox-only constraint force T3-only (Mac Studio) routing, never T2 stunt-double? Or inherit standard T2-on-MacBook-off-LAN fallback? | **T3 Mac Studio default for sustained autonomous runs**; T2 vllm-mlx stunt-double available as operator-supervised escape hatch for short experimental runs. Sustained SWE-bench-like batches forbidden on T2 (MacBook thermal throttling during travel sessions). Codified in §2 OpenHands "Default LiteLLM tier" cell + §3 sandbox row. | 2026-05-11 | Thread A WP-4 chat session |
| Q-7 | Goose Posture 0 doctrine — does the ADR mandate "supervised use only with operator-approved recipes" or also allow autonomous low-risk recipes (read-only summarization, repo introspection)? | **Supervised invocation only; autonomous recipes NOT permitted.** Manual operator approval required per invocation. No low-risk autonomous carve-out — full supervised gate honors D-17-53 Posture-2 → Posture-0 demotion chronicle. Codified in §2 Goose "Posture" cell. | 2026-05-11 | Thread A WP-4 chat session |

**Resolution outcome.** All seven decisions baked into ADR body above; Status flipped PROPOSED → ACCEPTED 2026-05-11. Downstream propagation queued for Thread A WP-5 per §6 below.

---

## §6 Consequences (now actionable — Thread A WP-5 propagation scope)

Acceptance 2026-05-11 triggers the downstream propagation work below. **None of it executes in this Acceptance commit** — propagation is Thread A WP-5 scope; this section enumerates the queued work for that follow-on brief.

**Doctrine doc updates (Thread A WP-5):**
- `work-routing-doctrine.md` (D-17-95) — add a cross-reference to this ADR's §3 matrix AND fold in the Q-1 cross-cutting `.env` + SSH prohibition as a new sub-section of the tier definitions (the prohibition applies across all tiers, so it belongs in the doctrine's preamble, not under any single tier).
- `goose-capability-boundary.md` — add a cross-reference to this ADR's Goose row + formalize the Q-7 "supervised invocation only" gate as an explicit promotion-criterion entry (no autonomous recipes until Posture 1 re-promotion gate passes).
- `capability-self-knowledge.md` (D-17-23) — add a reference to this ADR's §2 per-agent role table as the canonical agent-identity index (capability-self-knowledge currently focuses on capability-discovery flavors A/B/C/D; the per-agent role table is the missing identity layer).
- `aider-intelligence-doctrine.md` — add a cross-reference; the five-layer enforcement structure is already canonical there. No content rewrite.
- `local-prompt-library-doctrine.md` (D-17-90) — add cross-reference linking persona selection to this ADR's per-agent model defaults.

**Wrapper script updates (Thread A WP-5 — NOT this commit):**
- `agent-orchestration/scripts/wrap-opencode.sh` — gain explicit Q-2 doc-authoring refuse path (extension of D-17-101 Aider boundary; OpenCode now refuses C1a multi-paragraph chronicle/doctrine append at the wrapper layer, surfacing the work back to operator with a `route to Claude Code/Codex` message).
- `agent-orchestration/scripts/wrap-goose.sh` — gain explicit Q-7 supervised-mode gate (current `--no-context` posture is read-only-substrate-aligned; WP-5 adds an explicit "operator approval required" prompt OR an `AGENT_OPERATOR_APPROVED=1` env-var gate so autonomous invocations are structurally blocked).
- `agent-orchestration/scripts/wrap-aider.sh` — already enforces TIER 1/TIER 2 boundary via the three-layer intelligence system (D-17-103); WP-5 adds a cross-reference comment pointing to this ADR.

**LiteLLM config audit (Thread A WP-5):** verify `configs/litellm/config.yaml` Tier-1 `qwen2.5-coder` entry serves the Q-4 explicit `qwen2.5-coder:7b` pin (the current config aliases `qwen2.5-coder` → `ollama_chat/qwen2.5-coder:7b` per the WP-2 pre-flight read; Q-4 is satisfied at the LiteLLM layer but the wrapper / extension config alignment is worth verifying).

**§9 row interactions:**
- D-17-95 (work-routing doctrine) — this ADR is downstream consolidation; no row change.
- D-17-13 (Goose) — DONE; this ADR cites it. No row change.
- D-17-101 (Aider doc-authoring Tier-2 reclassification) — DONE; cited. No row change.
- D-17-104 (Kimi K2.6 DEFERRED) — cited as cascade-evaluation that did NOT promote; no row change.

**Brief D plan (`docs/_planning/phase-17-brief-d-plan-2026-05-11.md`):**
- WP-D-07 inherits ADR-resolved agent roles for per-agent validation work. Specifically: Q-5 commits this ADR to a v1.1 amendment after Brief D WP-D-07 closes Mac Mini canonical-surface install for Cline. WP-5 may author a sibling planning note recording the v1.1 trigger.

**Capability boundary canonicalization:**
- Q-1 resolution codifies cross-cutting `.env` + SSH boundaries in §4 of this ADR. WP-5 extends `integration-audit-doctrine.md` with a new Finding cross-referencing this ADR's §4 first bullet — the Finding is the durable observability anchor; the ADR is the decision anchor.

**§9 row interactions:**
- D-17-95 (work-routing doctrine) — this ADR is downstream consolidation; no row change.
- D-17-13 (Goose) — DONE; this ADR cites it. No row change.
- D-17-101 (Aider doc-authoring Tier-2 reclassification) — DONE; cited. No row change.
- D-17-104 (Kimi K2.6 DEFERRED) — cited as cascade-evaluation that did NOT promote; no row change.

**Brief D plan (`docs/_planning/phase-17-brief-d-plan-2026-05-11.md`):**
- WP-D-07 may inherit ADR-resolved agent roles for per-agent validation work; the plan currently has no per-agent role binding — ADR Acceptance unblocks adding those per-row.

**Capability boundary canonicalization:**
- Q-1 resolution potentially codifies cross-cutting `.env` + SSH boundaries into a sibling doctrine doc OR extends `integration-audit-doctrine.md` with a Finding.

**Audit doc reconciliation:**
- `docs/_audit/orchestration-layer-rebuild-audit-2026-05-11.md` §4.C per-agent install-state table will gain a "Role-codified by ADR-A-020 row N" cross-reference column on Acceptance. The audit's gap-classification (§5) is unchanged by this ADR — Acceptance does not promote any NOT-DELIVERED row to AS-SPEC; it codifies the AS-SPEC rows' roles.

**§9 framework table — no new rows authored by this ADR.** This ADR is not itself a deliverable in §9. Acceptance MAY trigger a follow-on §9 row (e.g., "D-NN-MM: Implement ADR-A-020 wrapper routing rules") if operator chooses to track the downstream wrapper-script work as a discrete deliverable. That decision is operator-discretion at Acceptance time, not pre-determined here.

---

## §7 Decision drivers and alternatives considered

**Decision drivers:**

1. **Cross-doctrine drift risk.** Roles distributed across 8+ docs lose coherence over time; Brief D execution will face the brittleness without consolidation.
2. **Operator decision-load minimization.** Q-1 through Q-7 are existing ambiguities that already gate Brief D execution; surfacing them as a single ADR decision list is cheaper than discovering them mid-session per-WP.
3. **Audit-trail integrity.** This ADR codifies what's actually live (per WP-1/2/3 evidence), not aspirational state — same evidence-based discipline WP-2 codified in `§7 risk register` of the orchestration-rebuild audit.

**Alternatives considered:**

- **Per-agent ADRs (six separate decision records).** Rejected. The routing matrix in §3 is intrinsically cross-agent — separate ADRs would duplicate the matrix and risk drift. Per-agent doctrine docs (e.g., `goose-capability-boundary.md`) already exist for agent-specific deep dives; an ADR is the right surface for the cross-agent decision.
- **Extend an existing ADR (e.g., ADR-A-004 "Aider is an adapter").** Rejected. ADR-A-004 addresses a specific Aider role question, not the multi-agent role matrix. Scope-creep on accepted ADRs would muddy the audit trail.
- **Author this content as a doctrine doc (e.g., `docs/architecture-facts/track-2-agent-roles.md`).** Rejected. Role codification is an architectural decision (operator authorization required; PROPOSED → Accepted gate), not a chronicle of existing behavior. Doctrine docs describe; ADRs decide.
- **Defer codification until Brief D LAN session.** Rejected. WP-4 is the off-LAN ADR-author work the brief explicitly authorized; Brief D LAN session is heavy enough without role-codification debate happening mid-execution.
- **Embed the role matrix directly into `work-routing-doctrine.md` (D-17-95).** Rejected. D-17-95 establishes the *generic* tier classifier (TIER 1/2/3 by task shape); this ADR maps *agent identity* into those tiers. Conflating them risks D-17-95 becoming a single doc that both classifies tasks AND assigns agents — two distinct decisions that benefit from independent revision cadence. D-17-95 remains the task-shape authority; this ADR is the agent-assignment authority; they cross-reference.

---

## §8 References

**Roadmap sections cited:** §0, §1.2, §2.2, §3.2, §4.1–§4.4, §9.1, §9.5, §10, §11, §12, §14, §15.1, §15.2.

**Errata entries cited:** E-001 (Serena install), E-003 (Thunderbolt host-applicability).

**Doctrine docs cited:** `work-routing-doctrine.md`, `goose-capability-boundary.md`, `aider-intelligence-doctrine.md`, `aider-verifier-doctrine.md`, `local-prompt-library-doctrine.md`, `model-provenance-doctrine.md`, `integration-audit-doctrine.md` Findings 19+22, `local-tool-calling.md` Finding 1.B.

**Capability audits cited:** `docs/_audit/capability/openhands-app-2026-05-01.md` (operator-decided KEEP).

**§9 rows cited:** D-17-13, D-17-23, D-17-53, D-17-90, D-17-92, D-17-93, D-17-94, D-17-95, D-17-101, D-17-103, D-17-104, D-17-109, D-17-110, D-17-111, D-17-122.

**Implementation references:** `configs/litellm/config.yaml`, `configs/opencode/opencode.json`, `agent-orchestration/scripts/{wrap-aider,wrap-goose,wrap-opencode}.sh`, `scripts/aider-task.sh`, `bin/aider_guard.py`, `bin/aider_verifier.py`, `~/.local/bin/serena`, `~/.opencode/bin/opencode`, `~/.vscode/extensions/continue.continue-1.2.22-darwin-arm64`, `docker.openhands.dev/openhands/openhands:1.7`.

**Related ADRs:** ADR-A-003, ADR-A-004, ADR-A-005, ADR-A-014, ADR-A-019 (reserved-but-unauthored OrbStack ADR).

**Phase 17 closeout artifacts that consume this ADR's outcome:** `docs/_audit/orchestration-layer-rebuild-audit-2026-05-11.md` (audit), `docs/_planning/phase-17-brief-d-plan-2026-05-11.md` (Brief D plan WP-D-07).

**Install evidence (Thread A WP-1 + WP-2 + WP-3 corrections):** `docs/runbooks/foundation-install-status-track-2.md` Stages 1–7; main commits `06d3d6fd` (WP-1), `b71c3689` (WP-2), `bbf3d4e3` (WP-3).

---

## §9 Version history

- **v1.0 PROPOSED** — 2026-05-11 — initial codification, 7 Q-NN gates open. Thread A WP-4 commit `34b6e6dd` on `feat/thread-a-wp-4-track2-agents-adr`.
- **v1.0 ACCEPTED** — 2026-05-11 — Q-1 through Q-7 resolved per operator decision in Thread A WP-4 chat session. Resolutions baked into §2 + §3 + §4 above; resolution log at §5. This commit on the same branch (Thread A WP-4 Acceptance amendment).
- **v1.1 (planned)** — post-Brief D WP-D-07 — Cline canonical-surface coverage added per Q-5 resolution. Trigger: Mac Mini Cline install verified live during Brief D LAN-session. Amendment shape: add Cline row to §2; extend §3 matrix with C2 IDE-supervised Plan/Act row; update §1 Context to seven-agent scope.
