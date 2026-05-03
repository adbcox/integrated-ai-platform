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
