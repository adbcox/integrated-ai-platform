# Local tool-calling — durable findings

Chronicle of facts about how local model-serving stacks
(Ollama, exo, …) handle the OpenAI-compatible function-calling
protocol. Items here outlive any single deliverable; new findings
append to the bottom with date + originating WP.

This chronicle exists because the platform is increasingly hosting
agent surfaces (Claude Code, Goose, Open WebUI, OpenHands, custom
MCP-driven workflows) that all assume "OpenAI-compatible endpoint
+ structured `tool_calls` in the response." That assumption holds
for cloud providers and breaks in non-obvious ways for local
backends. Without a single chronicle, every new agent integration
repeats the same investigation.

---

## Finding 1 — Ollama drops `tool_calls` in streaming mode

**Date:** 2026-05-03
**Originating WP:** D-17-13 (Goose evaluation)
**Severity:** High (blocks any streaming-by-default agent host
talking to Ollama via the OpenAI-compat surface)

### What
Ollama's `/v1/chat/completions` endpoint emits structured
`tool_calls` correctly **only** when `stream: false`. When
`stream: true`, the stream contains a single chunk with
`delta: {role:"assistant", content:""}, finish_reason:"stop"` —
the tool call is dropped on the floor.

Direct evidence:

```bash
# Non-streaming — works
curl -sS -X POST http://127.0.0.1:11434/v1/chat/completions -d '{
  "model":"devstral",
  "messages":[{"role":"user","content":"What time is it?"}],
  "tools":[{"type":"function","function":{"name":"get_time",
    "description":"Returns current time",
    "parameters":{"type":"object","properties":{}}}}],
  "tool_choice":"auto"
}'
# → choices[0].message.tool_calls = [{...get_time...}],
#   finish_reason="tool_calls"

# Streaming — broken
# Same body + "stream":true
# → single chunk: delta:{role:"assistant",content:""}, finish_reason:"stop"
# → tool call gone
```

### Why it bit us
Goose 1.33.1's `openai` provider hard-codes
`supports_streaming: true` (verified in
`crates/goose/src/providers/openai.rs` of the
`aaif-goose/goose` repo). There is no documented config key to
disable it. Therefore Goose-on-Ollama-via-OpenAI-compat cannot
complete a tool-using turn — the model emits the call as text in
the chat content (because the stream surface stripped the
tool_calls field), Goose's executor never sees a tool-call delta,
and the loop terminates.

This is not Goose-specific: any agent host that defaults to
streaming and passes through Ollama via OpenAI-compat will hit
the same wall.

### Doctrine takeaway
**Before integrating any new local agent surface, verify its
tool-calling protocol works against the intended backend in the
streaming mode it will use in production.** Test matrix:

| Backend         | Stream off | Stream on |
|-----------------|------------|-----------|
| Ollama          | ✅ ok       | ❌ drops `tool_calls` (this finding) |
| exo (MLX)       | ❌ text-formatted (Finding 2) | ❌ text-formatted |
| Anthropic API   | ✅ ok       | ✅ ok      |
| OpenAI API      | ✅ ok       | ✅ ok      |

For the local stack, a working agent integration requires either:
1. The agent host can be forced into non-streaming mode, OR
2. The agent host implements its own tool-call shimming
   (parse `<tools>{...}</tools>` or fenced JSON out of streamed
   text content), OR
3. A gateway-side adapter buffers the upstream stream and
   re-emits as a single non-streaming response (fragile;
   currently out of scope for litellm).

### Status
**Upstream-blocked.** Watch:
- Ollama — `tool_calls` in streaming responses. Track the Ollama
  GitHub issues for "stream tool_calls" / "function calling
  streaming."
- Goose — any release that exposes a `streaming: false` or
  `supports_streaming: false` config knob for the openai
  provider.

Either fix unblocks Goose adoption.

---

## Finding 1.B — qwen3-coder family emits structured `tool_calls` in streaming mode (Ollama 0.22.1)

**Date:** 2026-05-03
**Originating WP:** D-17-13 (reopened) WP-03 + WP-06
**Severity:** Resolves D-17-13 reopening blocker — Goose+T3-B path
unblocked.

### What

Finding 1 ("Ollama drops `tool_calls` in streaming mode") was correct
as written for `qwen2.5-coder` family on Ollama 0.20.7. It does **not**
hold for `qwen3-coder` family on Ollama 0.22.1. The dichotomy is along
**(model-family × Ollama-version)** axis, not "Ollama" alone.

Direct evidence — qwen3-coder:30b, Ollama 0.22.1 on Mac Studio
(192.168.10.142:11434), `stream:true`, tools=[get_weather]:

```bash
curl -sN -X POST http://192.168.10.142:11434/api/chat -d '{
  "model": "qwen3-coder:30b",
  "stream": true,
  "messages":[{"role":"user","content":"What is the weather in Paris?
              Use the get_weather tool."}],
  "tools":[{"type":"function","function":{"name":"get_weather",
    "description":"Get current weather for a city",
    "parameters":{"type":"object","properties":{
      "city":{"type":"string"}},"required":["city"]}}}]
}'
```

First SSE chunk:

```json
{"model":"qwen3-coder:30b","created_at":"2026-05-03T21:14:26.570427Z",
 "message":{"role":"assistant","content":"",
   "tool_calls":[{"id":"call_uhvjy6re",
                  "function":{"index":0,"name":"get_weather",
                             "arguments":{"city":"Paris"}}}]},
 "done":false}
```

Structured `tool_calls` array is populated in the streaming chunk.
Refines the Finding 1 matrix:

| Backend × Mode  | Non-streaming | Streaming |
|-----------------|---------------|-----------|
| Ollama 0.20.7 + qwen2.5-coder | ✅ ok | ❌ drops `tool_calls` (F1) |
| Ollama 0.22.1 + qwen3-coder   | ✅ ok | **✅ ok (F1.B)** |
| exo (MLX) + qwen2.5           | ❌ text (F2) | ❌ text |

### Production verification (Goose+T3-B end-to-end)

D-17-13 WP-03 smoke test against Goose 1.33.1 → ollama provider →
qwen3-coder:30b on Mac Studio Ollama 0.22.1: full tool-loop verified
(filesystem-mcp `read_text_file` + `list_allowed_directories`),
structured `tool_calls` round-trip end-to-end. Goose's ollama provider
hard-codes streaming on, so this verification stresses the same code
path that F1 originally identified as broken.

WP-06 first-test deliverable (Goose drafts a runbook from 3 source
files): 6 tool calls, 51s wall-clock, all structurally valid.

### Sub-finding F1.B.1 — qwen3-coder:30b emission noise in extended-prose contexts

During WP-06 the model emitted a stray `<functionI'll draft...` token
prefix that mixed prose continuation with a partial function-call
token. The actual `tool_calls` JSON was structurally valid; the noise
appeared only in the prose stream. Occasional, not a blocking defect.
Track recurrence over Phase-A executions; if rate exceeds ~5% of
sessions, escalate to upstream Ollama issue.

### Implication for adoption

Local-Ollama as the agent backend is unblocked **provided** the
model is qwen3-coder family (or another model the platform later
verifies on the `(family × version)` axis) and Ollama is ≥0.22.1.
Pre-flight check before adopting any new model+version pairing for
agentic use: run the curl probe above against the candidate, confirm
structured `tool_calls` in the streaming chunk.

### Status

**Resolved for the qwen3-coder × 0.22.1 cell.** Cells outside this
require their own probe before adoption — the F1.B unblocking does
not generalize to other model families on the same Ollama version,
or to qwen3-coder on older Ollama versions, until separately verified.

---

## Finding 2 — exo's OpenAI-compat layer does not translate Qwen's native tool-call markers

**Date:** 2026-05-03
**Originating WP:** D-17-13 (Goose evaluation, exo path)
**Severity:** Medium (blocks structured-tool-call agents from
using the exo route; chat-only agents are unaffected)

### What
exo (running `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit`)
returns tool calls as text in the message `content` field, even
in non-streaming mode:

```json
{
  "choices":[{
    "finish_reason":"stop",
    "message":{
      "role":"assistant",
      "content":"<tools>\n  {\n    \"name\": \"get_time\",\n    \"arguments\": {}\n  }\n</tools>",
      "provider_specific_fields":{...}
    }
  }]
}
```

The `<tools>...</tools>` envelope is Qwen's native
chat-template markup for function calling. Qwen IS calling the
tool correctly at the prompt-template level. exo's OpenAI-compat
shim is not post-processing those markers into
`choices[].message.tool_calls`.

### Why it matters
Compounding effect with Finding 1: even if the Ollama streaming
gap is fixed, the exo route still won't surface tool calls to
agents. The exo route works fine for chat (the demo path verified
in D-17-30) but not for tool-using agents.

This is consistent with the broader
"OpenAI surface fidelity gap" theme that exo-cluster.md documents
(empty `/v1/models`, response field shape drift, etc.). exo's
chat path is solid; its agent-surface path is partial.

### Doctrine takeaway
For tool-using agents on the local stack, prefer Ollama-backed
routes (devstral, qwen-coder-32b) once Finding 1 is resolved.
Reserve exo for chat / completion / batch inference where the
OpenAI-compat fidelity gap doesn't bite.

### Status
**Upstream-blocked.** Watch exo for OpenAI-compat surface
hardening — same revisit signal as Findings O / U / V in
exo-cluster.md.

---
