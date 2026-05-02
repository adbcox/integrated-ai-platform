## Consumer integration: litellm-gateway

**Status of this document.** Descriptive. D-17-11 does NOT modify
litellm_config.yaml. The wiring described here is what an operator
would do to connect litellm-gateway to the system-prompt library;
when that wiring lands operationally, it will be its own deliverable
with its own framework row.

**Why this consumer matters.** litellm-gateway is the platform's
LLM API surface (per CLAUDE.md "LLM Access Doctrine"). Anything
that talks to a local model — Open WebUI, sub-agents, MCP servers,
operator scripts — typically routes through it. A library prompt
attached at the gateway level is consistent across consumers
without each consumer having to know about it.

---

### Current litellm-gateway state (as of 2026-05-02)

- Config at
  `/Users/admin/control-center-stack/stacks/gateways/litellm_config.yaml`.
- Five model entries: qwen-coder-32b, qwen-coder-14b, qwen-coder-7b,
  devstral, deepseek-coder. All point to local Ollama via
  `host.docker.internal:11434`.
- No system prompt is set in config; system prompts come from the
  caller per-request (Open WebUI sends its own; Claude Code
  injects its own; etc.).

---

### Proposed integration shape

litellm supports per-model `litellm_params.system_prompt` (or a
`pre_call_hook`) that injects a system prompt server-side. The
library integration would:

1. Map each litellm model to a (mode-default, tier) pair. Example:
   - `qwen-coder-32b` → tier T1; default mode = `deliberate-analysis`
   - `qwen-coder-14b` → tier T2; default mode = `deliberate-analysis`
   - `qwen-coder-7b` → tier T2; default mode = `voice-fast`
   - `devstral` → tier T3; default mode = `code-review`
   - `deepseek-coder` → tier T3; default mode = `decomposition-planning`
2. Pre-call: read `docs/system-prompts/modes/<mode>.md` +
   `docs/system-prompts/tiers/<tier>.md`, concatenate (mode first,
   blank line, tier second), prepend to the user's system prompt
   (or replace it if no caller-supplied prompt).
3. Allow per-request override via a header (e.g.,
   `X-System-Prompt-Mode: capability-permission`) so an operator
   can pick a different mode without changing the model.

**File-watch vs cold-reload.** The library files change rarely.
Cold-reload (re-read on container restart) is sufficient. A
file-watch is overkill and adds failure modes (partial reads
during write, etc.).

**Caller-supplied prompts.** When a caller (Open WebUI, Claude Code,
operator script) supplies its own system prompt, the integration
should append rather than replace — caller intent first, library
framing second. This avoids surprising callers who depend on their
own prompt.

---

### Open questions to resolve at wiring time

- Does the platform want the library injection at the gateway level
  (one place, applies to everyone) or at each consumer (each tool
  picks its own composition)? Trade-off: gateway-level is
  consistent but masks per-tool customization; consumer-level is
  flexible but invites drift.
- Should mode/tier selection move into the request body (caller
  picks per-call) or stay in the gateway config (caller picks the
  model, gateway picks the prompt)? Latter is simpler; former is
  more expressive.
- Where should the per-request override header be documented?
  Probably the gateway's own README (which lives next to the
  config in the control-center-stack repo, not this repo).

---

### What this integration does NOT do

- Does NOT change which models exist in litellm. Routing is still
  about model class / size; the library is about framing.
- Does NOT introduce Anthropic API or any cloud route. Per CLAUDE.md
  doctrine, platform services are local-only; cloud LLM access
  flows through `claude-pro` shell directly to Anthropic, not
  through litellm.
- Does NOT replace the per-tool system prompts in Claude Code,
  sub-agents, or MCP servers. Those tools have their own surfaces
  and may keep their own prompts; the library exists to share
  framing between tools that want to share, not to mandate
  uniformity.

### See also

- `/Users/admin/control-center-stack/stacks/gateways/litellm_config.yaml`
  — current model registry
- `docs/system-prompts/README.md` — library overview
- `docs/system-prompts/consumers/open-webui-integration.md` — companion
  consumer doc
- CLAUDE.md "LLM Access Doctrine" — local-first posture, cloud
  routing rules
