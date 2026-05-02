## Consumer integration: Open WebUI

**Status of this document.** Descriptive. D-17-11 does NOT modify
Open WebUI runtime configuration. The wiring described here is what
an operator would do to connect Open WebUI to the system-prompt
library; the actual wiring is a follow-on operational task with its
own framework row when scoped.

**Why this consumer matters.** Open WebUI is the platform's
human-facing chat surface for direct interaction with local models
(versus Claude Code, which is the agent-facing surface). Operators
running ad-hoc tasks tend to start in Open WebUI; consistency between
"what you get in Open WebUI" and "what an agent gets via litellm" is
a usability property worth maintaining.

---

### Current Open WebUI state (as of 2026-05-02)

- Container `open-webui` healthy on the platform (verified via
  `docker ps`).
- Talks to litellm-gateway as its LLM backend (per platform's
  service inventory).
- Has a built-in concept of "Models" (per-model defaults) and
  "Prompts" (saved prompt templates the operator can pick from a
  menu).
- System prompts are configurable per-model at the Open WebUI
  admin level, and also overridable per-conversation by the operator.

---

### Proposed integration shape

Two compatible surfaces; pick one or both:

**Surface A — Per-model system prompts (admin-side).**
- For each model exposed in Open WebUI, set its system prompt to
  the appropriate (mode + tier) composition from the library.
- Example:
  - "Coder Fast" model → qwen-coder-7b backend → voice-fast + T2
  - "Coder Deliberate" model → qwen-coder-32b backend →
    deliberate-analysis + T1
  - "Code Review" model → qwen-coder-32b backend → code-review + T1
  - "Decomposer" model → qwen-coder-14b backend →
    decomposition-planning + T2
  - "Capability Permission" model → qwen-coder-32b backend →
    capability-permission + T1
- Operators pick the right "model" for what they're doing. The
  underlying backend is still one of the litellm-gateway routes;
  the model-name is now a (backend + framing) bundle.

**Surface B — Saved Prompts (per-conversation override).**
- Add each library mode as a saved Prompt in Open WebUI's prompt
  picker.
- Operators starting an ad-hoc conversation can pick a Prompt from
  the menu to override the model's default framing for that
  conversation only.
- Useful for one-off mode switches without creating a new "Model"
  for every combination.

**Sync source.** In both surfaces, the library files
(`docs/system-prompts/modes/*.md`, `docs/system-prompts/tiers/*.md`)
are the canonical text. Open WebUI's stored prompts are copies; if
the library changes, the operator (or a small sync script) re-pastes
the updated text. A periodic check that Open WebUI's stored copies
match the repo would catch drift.

---

### Operator UX expectations

- The active mode and tier should be visible in the conversation
  (Open WebUI's UI surfaces system-prompt content in a panel; that's
  where the operator sees what's loaded).
- Switching mode mid-conversation should be straightforward (Open
  WebUI's saved-prompt picker handles this if Surface B is wired).
- Switching tier mid-conversation usually means switching model
  (since tier maps to model class), which is also a built-in Open
  WebUI workflow.

---

### What this integration does NOT do

- Does NOT bypass litellm-gateway. Open WebUI still talks to local
  models through the gateway; the library is layered on top of
  whatever routing the gateway provides.
- Does NOT replace Open WebUI's own prompt-template system. The
  library is a *content source* for the templates; the templates
  themselves are owned by Open WebUI's storage.
- Does NOT mandate a particular Open WebUI workflow. Operators who
  prefer to type their own system prompt per conversation can keep
  doing that; the library is an option, not a requirement.

---

### Open questions to resolve at wiring time

- Should library text be sync'd into Open WebUI manually (paste-on-
  change) or via a small script reading the repo and writing to
  Open WebUI's API? Latter is more robust, costs a small write of
  code; former is zero-code but invites drift.
- Should Surface A and Surface B coexist, or pick one to keep the
  UX simple? Probably both — Surface A is the default path
  (operator picks the right model), Surface B is the override path
  (operator wants something different for this conversation).
- How does the operator know which mode is active in a given
  conversation? Open WebUI's system-prompt panel shows the text;
  if mode/tier names are at the top of each library file (they are,
  in `## Mode:` / `## Tier:` headings), the operator can read them
  directly.

### See also

- `docs/system-prompts/README.md` — library overview
- `docs/system-prompts/consumers/litellm-routing.md` — companion
  consumer doc (gateway-side integration)
- Open WebUI documentation (upstream) for the per-model and saved-
  Prompts feature surfaces
