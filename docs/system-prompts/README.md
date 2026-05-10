# Local LLM system prompt library

**Status:** Repo-managed library of system-prompt documentation for
the platform's local LLM stack. D-17-11 deliverable.

**Scope (per 2026-05-11 consolidation audit §14).** This directory is
canonical for the **documentation/doctrine layer** — `tiers/` (T1-T4
capability classes) and `consumers/` (descriptive integration prose).
The **runtime preset layer** is canonical at
`config/prompts/library/v1.0.0/` (D-17-90), where the operational
prompts are loaded by `bin/persona_loader.py` and referenced by
`scripts/aider-task.sh`. The 4 mode prompts originally housed at
`docs/system-prompts/modes/` were merged into the runtime layer and
retired in the 2026-05-11 cleanup commit; the `capability-permission`
mode (D-17-23 slot fill) was migrated to
`config/prompts/library/v1.0.0/08-capability-permission.md`. See
`docs/_audit/system-prompts-consolidation-audit-2026-05-11.md` for the
merge provenance and per-pair semantic comparison.

**What this library now contains (post-2026-05-11 consolidation).**

- **Tiers** — *which model class* the prompt is being run on
  (T1 general-purpose, T2 throughput, T3 specialty, T4 distributed).
  Tier hints adjust verbosity, tool-use expectations, and the model's
  self-framing of its capabilities. **CANONICAL HERE.**
- **Consumers** — descriptive integration prose for
  `consumers/litellm-routing.md` and `consumers/open-webui-integration.md`.
  **CANONICAL HERE** (Library B's `v1.0.0/05-persona-routing.yaml` is
  the runtime config; this directory's consumer docs are the
  descriptive overview).
- **Modes** — *what kind of work* the prompt is for (voice-fast,
  deliberate-analysis, code-review, decomposition-planning,
  capability-permission). **MIGRATED to**
  `config/prompts/library/v1.0.0/` (presets 01-04 + 08).

A consumer (litellm-gateway, Open WebUI, or operator paste) composes
one mode (from Library B presets) + one tier (from this directory)
into the running system prompt. See `consumers/litellm-routing.md`
and `consumers/open-webui-integration.md` for the integration patterns.

**What this library is NOT.**

- Not a model-router. Routing decisions live in litellm
  (`/Users/admin/control-center-stack/stacks/gateways/litellm_config.yaml`)
  and in operator shell aliases (`claude-local`, `claude-pro`).
- Not a tool-use spec. Tool surfaces are owned by the consumer
  (Claude Code, Goose, Open WebUI extension, MCP server roster); this
  library only acknowledges that tools may be present and frames the
  AI's expectation accordingly.
- Not a benchmark suite. Model evaluation is D-17-12.
- Not a finished product. Initial fill matches the slot specification
  D-17-23 set. Operators are expected to extend the library when a
  recurring task pattern surfaces a missing prompt — see "Extending"
  below.

---

## Why a library at all

Three forces converge:

1. **D-17-23 (capability self-knowledge)** identified that local
   models inherit different default postures than Claude — and that
   operators repeatedly hit the same friction surfaces (cautious
   framing, over-constraint inference). The capability-permission
   mode is the durable answer: pre-grant permissions for capabilities
   the operator commonly wants and the model commonly hedges on,
   instead of negotiating per-session.
2. **D-17-19 tier definitions** (T1/T2/T3/T4) categorize models by
   capability-and-cost class, not by name. The system prompt should
   set expectations consistent with the tier — a T2 throughput model
   gets framing that respects its lower context budget; a T4
   distributed model gets framing that acknowledges its multi-node
   coordination cost.
3. **Compaction survives the repo, not chat.** Per D#22, prompt
   content lived as scattered chat history and inline consumer
   configs would not survive compaction. Centralizing in the repo
   means future operators (and future Claude sessions) can find the
   canonical version.

---

## Library shape

```
docs/system-prompts/
├── README.md                                 (this file)
├── tiers/                                    (CANONICAL HERE)
│   ├── T1-general-purpose.md                 (default-class chat models)
│   ├── T2-throughput.md                      (smaller / quantized fast models)
│   ├── T3-specialty.md                       (code-fine-tunes, domain-specific — D-17-12 evaluation)
│   └── T4-distributed.md                     (multi-node, exo-cluster — D-17-14)
└── consumers/                                (CANONICAL HERE — descriptive prose)
    ├── litellm-routing.md                    (how litellm-gateway composes prompts)
    └── open-webui-integration.md             (how Open WebUI selects prompts)
```

Modes have moved to the runtime preset layer (2026-05-11):

```
config/prompts/library/v1.0.0/                (CANONICAL there)
├── CATALOG.md
├── 00-standard-preamble.md
├── 01-voice-fast.md                          (was modes/voice-fast.md)
├── 02-deliberate-analysis.md                 (was modes/deliberate-analysis.md)
├── 03-code-review.md                         (was modes/code-review.md)
├── 04-decomposition.md                       (was modes/decomposition-planning.md)
├── 05-persona-routing.yaml                   (runtime routing config)
├── 06-aider-tier1-presets.md                 (D-17-95)
├── 07-deepseek-verifier-prompt.md            (D-17-110)
├── 08-capability-permission.md               (was modes/capability-permission.md; D-17-23)
└── personas/                                 (D-17-121 runtime layer)
```

---

## How to use the library (operator)

**For a one-off task in Open WebUI or Claude Code:**
1. Pick a mode based on what you're doing.
2. Pick a tier based on which model you're running on.
3. Concatenate the two files (mode first, tier second) and paste as
   the system prompt.

**For routine work:**
- The consumer integration docs document the standing routing — most
  routine work runs on a default mode + tier combination so operators
  don't have to think about it. Override by hand only when a task
  pattern doesn't match the default.

**Order matters.** Mode-then-tier reads as "here's what we're doing,
here's what model is doing it." The mode sets the task framing; the
tier sets the capability framing. Reversing order tends to make
the capability framing read as the primary instruction, which it
isn't.

---

## How to use the library (consumer service)

A consumer (litellm-gateway preset, Open WebUI prompt-template,
Goose system instruction, etc.) reads the relevant mode + tier files
at start-of-session and concatenates them into the system prompt
sent to the model.

**Integration contract:**
- Read raw markdown — no templating, no preprocessing.
- Concatenate in mode-then-tier order with a single blank line
  between them.
- Surface the active mode and tier in the consumer's UI so operators
  can see what's loaded.
- Hot-reload on file change is optional; cold reload at process
  restart is sufficient.

`consumers/litellm-routing.md` and `consumers/open-webui-integration.md`
describe the per-consumer specifics. Both documents are
**descriptive** as of D-17-11 — they document what the integration
should look like when the consumer is wired. D-17-11 does NOT
modify litellm_config.yaml or Open WebUI runtime config. That
wiring is a follow-on operational task, scoped separately when an
operator actually wants the integration live.

---

## Mode index — MIGRATED to `config/prompts/library/v1.0.0/`

The 5 mode prompts (voice-fast / deliberate-analysis / code-review /
decomposition-planning / capability-permission) were merged into the
runtime preset layer in the 2026-05-11 consolidation cleanup. See
`config/prompts/library/v1.0.0/CATALOG.md` for the runtime-loaded
preset library; the per-pair semantic comparison and merge provenance
is at
`docs/_audit/system-prompts-consolidation-audit-2026-05-11.md` §14.

## Tier index

| Tier | Class | Notes |
|---|---|---|
| T1 | General-purpose default | Qwen-Coder-32B-class; Claude-class on cloud |
| T2 | Throughput | 7B–14B class; smaller context; fast |
| T3 | Specialty (code-fine-tune, domain-specific) | D-17-12 evaluates which models live here |
| T4 | Distributed (multi-node via exo) | D-17-14 cluster; coordination cost is real |

---

## Slot-binding contract (D-17-23) — MIGRATED to Library B

The slot-binding contract previously documented `modes/capability-permission.md`
as the D-17-23 slot fill. As of the 2026-05-11 consolidation, the
slot fill lives at
`config/prompts/library/v1.0.0/08-capability-permission.md`.
The original slot specification at
`docs/architecture-facts/capability-self-knowledge.md` "Hand-off to
D-17-11" section is unchanged; D-17-11's contractual obligation is
satisfied (the content was authored and delivered) but the runtime
home of the prompt content is now Library B. The slot specification:

> Prompt content that pre-grants permission for capabilities the
> operator commonly wants and Claude or local models commonly hedge
> on. Initial fill informed by the known-capabilities registry —
> entries flagged Flavor C/D map most naturally to permission-
> granting prompt content; Flavor A/B entries map to surface/tool
> documentation rather than prompt content.

D-17-11's scope: author the mode-prompt content for Flavors C and D
specifically. Flavor A (training-data gap) and Flavor B (tool-surface
gap) are NOT addressed by prompt content — they're addressed by
in-context evidence injection (Flavor A) and tool configuration
(Flavor B), neither of which is a system-prompt concern.

When the registry grows new Flavor C/D entries, the
capability-permission mode should be revisited so the prompt
content reflects the current operator-friction set.

---

## Extending the library

**When to add a new mode.** A recurring task pattern surfaces that
doesn't fit any existing mode. Indicators: operators paste the same
ad-hoc framing into multiple sessions; a consumer wants to wire a
new preset; a new doctrine point lands that needs prompt-level
expression.

**When to add a new tier.** A new model class lands that doesn't fit
T1–T4. Most routine model additions just slot into an existing tier;
only meaningfully different capability/cost classes warrant a new
tier.

**Process.**
1. Write the new mode/tier file in the same shape as existing ones
   (front-matter is optional; lead with the framing instructions).
2. Update the index table in this README.
3. If the new mode/tier changes the consumer integration story,
   update the relevant `consumers/*.md`.
4. If the addition is doctrine-shaped (e.g., a new
   capability-permission flavor), reference the architecture-fact
   that motivated it.

**What NOT to add.**
- Per-task prompts (e.g., "for refactoring authentication"). Those
  belong in operator notes or the calling consumer's prompt
  template, not here.
- Model-specific prompts (e.g., "for qwen2.5-coder:32b"). Use a
  tier instead; a tier is the right granularity.
- Anthropic-API-specific prompt patterns. The platform is local-
  first per CLAUDE.md "LLM Access Doctrine"; cloud routes flow
  through `claude-pro` shell directly to Anthropic, not through
  this library.

---

## See also

- `docs/architecture-facts/capability-self-knowledge.md` — D#23
  doctrine; defines the capability-permission slot
- `docs/architecture-facts/known-capabilities.md` — operator
  registry that informs capability-permission content
- `docs/architecture-patterns/observed-patterns.md` — D-17-19
  patterns that may inform future modes
- `docs/architecture-patterns/candidate-tools.md` — D-17-19 tool
  candidates
- `docs/PROJECT_FRAMEWORK.md` Phase 17 D-17-11 entry — slot-binding
  contract
- `/Users/admin/control-center-stack/stacks/gateways/litellm_config.yaml`
  — litellm-gateway model registry; consumer integration target
