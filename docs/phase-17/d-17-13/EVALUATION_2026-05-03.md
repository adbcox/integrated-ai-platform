# D-17-13 — Goose evaluation (2026-05-03)

**Goose version:** 1.33.1 (brew formula `block-goose-cli`, Apache 2.0)
**Backend chain tested:** Goose → litellm-gateway:4000 → exo-qwen-coder-7b
**Backend chain (alt):** Goose → litellm-gateway:4000 → ollama (`qwen-coder-7b`, `qwen-coder-32b`, `devstral`)

## Setup that worked

- Brew install (`brew install block-goose-cli`) lands the CLI at
  `/opt/homebrew/bin/goose` with config dir `~/.config/goose/`.
- Provider points at platform litellm via `OPENAI_HOST` +
  `OPENAI_API_KEY` env vars. Launcher
  `scripts/goose/goose-platform.sh` fetches the litellm master key
  from Vault (`secret/litellm/master#master_key`) at run time so no
  credential lives in static config. Hash-only verification:
  `sha256[:12]=439bcdb691d6` (matches D-17-26 chronicle).
- `GOOSE_PROVIDER: openai`, `GOOSE_MODEL: <route>`,
  `GOOSE_MODE: smart_approve` in `~/.config/goose/config.yaml`.
- `goose info` confirms install; minimal smoke (`Reply: PARIS`)
  returns `PARIS` — the chat path through litellm → exo works.

## MCP integration that worked

- `filesystem-mcp` (npx `@modelcontextprotocol/server-filesystem`)
  registered as a stdio extension; 14 tools surfaced
  (`read_text_file`, `list_directory`, `search_files`, …).
- `xindex` (in-repo MCP at `docker/xindex-mcp/app/server.py`)
  registered with `XINDEX_BASE_URL=http://127.0.0.1:8095`
  (host port from `~/.platform-registry/by-service/xindex.json` —
  D#25 doctrine consultation in action).
- Both extensions visible to Goose's tool surface; verified via
  prompt asking Goose to list its tools.

## What did not work — the blocker

**Symptom.** Goose can chat with the model, but cannot complete
tool-using tasks. The model emits its tool-call as TEXT in the
streaming chat content (e.g. `{"name":"read_text_file","arguments":{"path":"…"}}`)
instead of as a structured `tool_calls` array. Goose's executor
never sees a tool-call delta, so the loop terminates before any
tool runs.

**Root cause: Ollama's OpenAI-compat streaming surface drops
tool_calls deltas.** Direct evidence:

1. `POST /v1/chat/completions` to Ollama with `tools=[…]`
   and `stream:false` → returns proper structured
   `tool_calls: [{id,function:{name,arguments}}]`,
   `finish_reason: "tool_calls"` (verified for `devstral`).
2. Same call with `stream:true` → returns ONE chunk with
   `delta:{role:"assistant",content:""}, finish_reason:"stop"`.
   Tool call dropped entirely.
3. Goose's `openai` provider hard-codes
   `supports_streaming: true` and there is no documented config
   key to disable it. Verified by reading
   `crates/goose/src/providers/openai.rs` in the
   `aaif-goose/goose` repo.

The same drop happens through litellm, since litellm proxies
Ollama's streaming surface verbatim.

**Subsidiary finding (exo).** `exo-qwen-coder-7b` (the demo's
4-bit Qwen2.5-Coder-7B-Instruct on exo MLX) does NOT emit
structured `tool_calls` at all — even non-streaming. It returns
the call as `<tools>{json}</tools>` text in the `content` field.
This is exo's OpenAI-compat layer not post-processing Qwen's
native tool-call markers into the OpenAI shape. Adding it to the
exo-cluster.md "Not operational" list (subset of the broader
"OpenAI surface fidelity" gap that already includes the empty
`/v1/models` and other Findings).

## Baseline tasks (incomplete due to blocker)

| # | Task | Outcome |
|---|---|---|
| A | Summarize service registry (read MD, write 3-4 sentences) | **Failed** — devstral via Goose emitted `read_text_file` call as text; Goose terminated without invoking the tool. Took ~78s wall before timeout because Goose retries the prompt. |
| B | Find files referencing seal-vault port 8201 | **Not run** — same block as A. |
| C | Add a small test to compose_parser.py | **Not run** — same block as A. |

Comparison vs Claude Code baseline is therefore moot: Goose can't
get past the first tool call on this stack.

## What would unblock

In rough effort order:

1. **`goose-platform-noschema.sh` — disable streaming in Goose's
   request.** Requires Goose source patch (no env var exposes it)
   OR a litellm middleware that buffers Ollama's stream and
   re-emits as a non-streaming response. Either is real engineering
   (~half a day), and the latter is fragile.
2. **Wait for Ollama upstream to fix tool_calls in streaming.**
   Out-of-platform; no ETA.
3. **Run Goose against an external OpenAI-compatible endpoint
   that streams tool_calls correctly** (e.g., OpenRouter,
   Anthropic via openai-compat shim). Violates LLM Access Doctrine
   (no platform-side cloud LLM routes).

## Demo path decision

For Saturday 2026-05-09:

- **Goose is NOT the autonomous-coding centerpiece.** Its tool
  loop does not reach a working state on the all-local stack as
  configured.
- **Demo centerpiece remains:** Claude Code (the orchestrator)
  with the platform's Ollama models reachable via the existing
  subagent chain (decomposer/implementer/reviewer per
  `~/.claude/agents/`). Tool-calling on this path works because
  Claude Code talks directly to Anthropic in the orchestrator
  shell and to Ollama in the subagent shell — both paths handle
  tool-call protocol natively.
- **Goose stays installed** as a documented evaluation. The
  install + Vault-mediated launcher + MCP wiring is reusable when
  the streaming-tool_calls block lifts.

## Chronicle Finding

Recorded at `docs/architecture-facts/local-tool-calling.md`
(new chronicle, since this affects every local-agent integration,
not just Goose).

## Operator surface-back

- Goose install + config done; demo centerpiece reverted to Claude
  Code + subagents.
- WP-04 baseline tasks not executed against Goose; comparing
  unbacked stack against Claude Code would be misleading. The eval
  instead established the wiring shape and the upstream gap.
- Closing D-17-13 as DONE-with-outcome (not DEFERRED): the
  deliverable was "evaluate", not "adopt". Evaluation conclusion
  is recorded.
