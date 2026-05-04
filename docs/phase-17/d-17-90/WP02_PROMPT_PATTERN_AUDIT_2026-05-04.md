# D-17-90 WP-02 — Prompt-pattern audit (D-17-53 sessions 2–13) + Anthropic cross-reference

**Date:** 2026-05-04
**Inputs:** `docs/architecture-facts/goose-capability-boundary.md` (1806 lines, full),
11 session evidence dirs (`docs/phase-17/d-17-53/session{2,4,5,6,7,8,9,10,11,12,13}-evidence/`),
Anthropic prompting docs (https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).
**Status:** SURFACE-BACK — operator decision required before WP-03 authoring.

---

## 1. What the chronicle empirically proves about prompt shape

D-17-53 ran an 11-session capability-validation arc on Goose+qwen3-coder:30b × C1 (reference-doc draft). The arc bisects cleanly into **pre-strengthened-preamble** (Sessions 2–8) and **strengthened-preamble** (Sessions 9–13). Five preserve-patterns and five correct-patterns were promoted to standard preamble across the arc.

### 1.1 Five "preserve" patterns — capabilities the prompt should NOT suppress

| # | Pattern | Evidence | Doctrine takeaway |
|---|---|---|---|
| 1 | Cautious-by-default scope check (conditional on prompt path-list shape) | N=7 — Sessions 2–4 fired `list_allowed_directories` autonomously when paths had abstract/directory pointers; Sessions 5–11 skipped when paths were exhaustive absolute | Don't *suppress* — let the model choose by giving it a path-list whose shape matches your intent |
| 2 | Tool-call structural validity | 53/53 across N=5 sessions | F1.B substrate evidence; not prompt-dependent |
| 3 | Honest uncertainty marking ([UNVERIFIED — frontier review]) | Sessions 3 (factual gap) + 4 (failure-mode taxonomy gap) — N=2 across sub-shapes | Preamble must include `[UNVERIFIED]` instruction; treat high-`[UNVERIFIED]` density as *correct output* under substrate gap |
| 4 | Error-recovery shape: detect → probe → re-scope → continue → explicit reporting | Session 5 lidarr-ENOENT decoy | Preamble must explicitly authorize "if a context file does not exist, surface the missing-file fact and continue with remaining sources — do NOT fabricate" |
| 5 | Unprompted staleness detection on cross-referenced docs | Sessions 5+6 both flagged `opnsense-add-host-overrides.md` as Unbound-stale without operator hint — N=2 | Preserve via not-suppressing; reinforce by acknowledging staleness flags as load-bearing output |

### 1.2 Five "correct" patterns — failure modes the prompt SHOULD suppress

| # | Failure mode | Pre-fix shape | Remediation | Outcome |
|---|---|---|---|---|
| 1 | Padding tendency (Security/Backups sections, sibling-concern preamble) | Session 2 first observed; Session 6 sub-shape (opening preamble) | Sub-class-specific *"Skip the preamble. Open with the first procedure step or the when-to-use scope."* | RESOLVED Sessions 7–11 |
| 2 | Self-blind to encountered failure modes | Session 2 omitted `GOOSE_MODE=auto` even though it was the failure mode encountered during the test run | *"If a failure mode was encountered during the work itself, document it explicitly."* | RESOLVED (Session 3 onward, no recurrence) |
| 3 | Misapplied value-leaking heuristic | Session 5 omitted concrete compose snippets "to avoid leaking specifics" | *"The 'do not leak credential values' rule applies to credential VALUES (API keys, passwords, tokens), NOT to configuration STRUCTURE (compose snippets, Caddy blocks, HCL policy shapes, command syntax). Configuration structure is the substance of a runbook; omitting it is under-specification, not security."* | RESOLVED (Session 6 onward) |
| 4 | Over-abstraction on "abstract from N worked examples" sub-shape | Session 5 produced higher abstraction than work-class warranted | *"Concrete examples in code blocks; do not infer abstraction level from the abstract-from-N framing."* | RESOLVED |
| 5 | **Source-file fidelity loss under abstraction pressure** | Sessions 5/7/8 N=3 confirmed; Sessions 11/12/13 (3 of 5 strengthened-preamble sessions) → **CLASS-INTRINSIC for C1a** on this cell | Verbatim-block + source-citation table (Session 9 antidote) | **PROMPT-FIXABLE BUT NOT SUFFICIENT** — strengthens output but doesn't eliminate the failure class on this specific (Goose × qwen3-coder:30b × C1a) cell. Cell DEMOTED Posture 1 → Posture 0; C1a SUSPENDED indefinitely. |

**Critical nuance for D-17-90 doctrine:** correct-pattern #5's prompt remediation works on *substrate that is line-aligned and amenable to verbatim-block extraction* (Python argparse blocks, struct literals — Session 9 substrate). It fails on structured-document substrate (XML plists, multi-script orchestration — Sessions 11/12/13). This is the substrate-shape-correlation hypothesis. The prompt-library design must NOT assume verbatim-block instructions are a universal antidote — they're a high-leverage tool whose effectiveness varies by substrate-shape × model cell.

---

## 2. The verbatim Session 9 strengthened-preamble (canonical reference)

**Source:** `docs/phase-17/d-17-53/session9-evidence/prompt.txt` lines 25–60.

### 2.1 Two "strengthened constraints" (the remediation test)

```
A. Verbatim-block instruction. For every concrete fact in the
   runbook (function name, CLI flag, file path, env var, exit code,
   command shape), copy the relevant block from the source file
   VERBATIM into the runbook code block before paraphrasing. Do not
   paraphrase first. Do not "simplify" command syntax. Do not change
   function names, paths, or flag names. If the source file does
   not contain the fact, the runbook must say so explicitly — do
   NOT autocomplete from training data.

B. Source-grounded self-check. After drafting, append a
   "Source-citation table" section listing every concrete fact in
   the runbook in the form:

   | Fact | Source file | Line(s) | Verbatim quote |

   This is not optional. Each row's verbatim quote must match the
   source file at the cited line(s). Any fact in the runbook you
   cannot cite this way is a self-flagged defect — list it in
   self-flagged defects with the reason you couldn't cite.
```

### 2.2 Standing constraints (canonical — used in every Session 6+ prompt)

```
- Read-only filesystem-mcp + xindex only.
- Surface back drafts; do NOT write to disk.
- Mark "[UNVERIFIED — frontier review]" inline for facts you cannot
  ground in source files.
- Skip preamble. Open with one-line scope sentence.
- If a context file does not exist, surface back the missing-file
  fact and continue with remaining sources — do NOT fabricate.
```

### 2.3 Strengthened-line-number constraint (added Session 11; ineffective on its own)

```
LINE NUMBERS MUST BE VERIFIED via the same read_text_file call that
read the cited content. Do not generate line numbers from memory.
```

**Empirical result:** Session 11 produced fabricated line numbers despite this constraint. The model can game the source-citation table end-to-end — verbatim quotes are easy to copy, line numbers come from "looks-about-right" recall. Frontier-review checklist must independently verify line numbers; the prompt cannot guarantee them on this cell.

---

## 3. Cross-reference to Anthropic canonical prompting hierarchy

**Source:** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### 3.1 Anthropic's recommended technique order (verbatim section sequence)

1. **Be clear and direct** — Golden rule: a colleague with minimal context should be able to follow it. Be specific about output format. Use sequential numbered steps when order matters.
2. **Add context to improve performance** — Explain *why* a constraint matters. Claude generalizes from the explanation.
3. **Use examples effectively** — 3–5 relevant + diverse + structured examples in `<example>` tags.
4. **Structure prompts with XML tags** — Wrap each content type (`<instructions>`, `<context>`, `<input>`) in its own tag.
5. **Give Claude a role** — Single-sentence system-prompt role assignment focuses behavior.
6. **Long context prompting** — (a) Put long-form data at the TOP, queries at the bottom (up to 30% quality gain on multi-doc inputs). (b) Wrap each document in `<document>` with `<source>` and `<document_content>` subtags. (c) **Ground responses in quotes**: "ask Claude to quote relevant parts of the documents first before carrying out its task." ← This is the Anthropic-canonical version of D-17-53's verbatim-block instruction.

### 3.2 Where D-17-53's empirical findings align with Anthropic canon

| D-17-53 finding | Anthropic canon | Convergence |
|---|---|---|
| Verbatim-block instruction (correct-pattern #5 remediation) | "Ground responses in quotes — ask Claude to quote relevant parts of the documents first before carrying out its task" | **Strong convergence.** D-17-53 derived this empirically from Sessions 5/7/8 fabrication; Anthropic recommends it as canonical pattern for long-context. The pattern is sound; cell-specific limits are about the model executing it, not the pattern. |
| Source-citation table self-check | "Place these in `<quotes>` tags. Then, based on these quotes, list all information that would help…" | Convergence. Anthropic uses XML tags; D-17-53 used a markdown table. Functional equivalent. |
| Sub-class-specific opening preamble suppression | "Be clear and direct. Be specific about the desired output format and constraints." | Convergence — D-17-53 sharpened "concise" → "skip preamble; open with one-line scope" which is exactly the specificity Anthropic recommends. |
| Honest uncertainty marking ([UNVERIFIED]) | "Add context to improve performance" + "Be clear and direct" | Implicit in canon; D-17-53 made the convention explicit + named. |
| Error-recovery shape (detect → probe → re-scope) | Agentic systems / "Minimizing hallucinations in agentic coding" | Aligned framing; D-17-53 gave specific worked-example shape. |
| Path-list shape conditions cautious-by-default scope check | (no direct match) | D-17-53-specific — model behavior under exhaustive-vs-abstract path lists is empirical not canon. Promote as platform-specific finding. |

### 3.3 Anthropic canon NOT yet in D-17-53 prompts (gaps to address in WP-03)

| Anthropic canon | D-17-53 status | WP-03 implication |
|---|---|---|
| **XML-tag structuring** of prompts (not just inputs) | D-17-53 used markdown headers (`STRENGTHENED CONSTRAINTS`, `STANDING CONSTRAINTS`, `TASK`) | **Migrate to `<role>`, `<context>`, `<constraints>`, `<task>`, `<deliverable>` XML structure.** Improves parser-level disambiguation across model families (works for Claude AND many local models that have absorbed Anthropic conventions during training). |
| **Explicit role assignment in system-prompt position** | D-17-53 prompts used implicit role (Class C1 reference-doc draft inferred from preamble) | **Library templates must declare role explicitly** — "You are a runbook author for an autonomous AI platform" / "You are a code reviewer" / "You are a task decomposer" |
| **Examples (3–5 in `<example>` tags)** | D-17-53 prompts had ZERO examples — relied on model's training-data autocomplete (which is exactly the failure mode for cells that fabricate) | **WP-03 templates must include 1–3 anchor examples per persona where possible.** Especially load-bearing for cells in the failure-mode-class identified by D-17-53. |
| **Explanation of WHY a constraint exists** | D-17-53 added some why-context (e.g. failure-mode reason) but inconsistently | **Standardize:** every constraint includes a `<rationale>` line. Claude generalizes from explanation; matters more for non-frontier models where rote rule-following is weaker. |
| **Long-context: data at TOP, query at BOTTOM** | D-17-53 prompts put CONTEXT (sources) before TASK — already aligned | Preserve. |

---

## 4. Four canonical personas — derived from D-17-53 + Anthropic canon

The brief specified four personas: **voice-fast**, **deliberate-analysis**, **code-review**, **decomposition**. Mapping each to evidence + canon:

### 4.1 voice-fast — short conversational responses, voice-output-aware

**Use case:** Quick lookups, status queries, confirmations. Response will be read aloud or rendered in a voice-output context.

**D-17-53 evidence base:** none directly — D-17-53 was C1 reference-doc work; voice-fast is a new persona class for chat / voice-routed work.

**Anchored in Anthropic canon:**
- "Be specific about constraints" → output length cap (e.g. "≤3 sentences")
- "Add context — your response will be read aloud, so never use ellipses…" (verbatim Anthropic example for TTS)
- Skip preamble (sub-class-specific from D-17-53 correct-pattern #1)

**Persona shape draft:**
- Role: "Concise assistant for short voice-routed queries."
- Output: 1–3 sentences. No headers. No code blocks unless requested.
- Constraints: No ellipses (TTS hostile). No padding sections. If the answer is "I don't know" — say so.
- No preamble. Open with the answer.

### 4.2 deliberate-analysis — multi-step reasoning, written output

**Use case:** Audit work, drift detection, multi-step decisions, "what's next" decisions.

**D-17-53 evidence base:** Indirect — Sessions 9-10 had analysis-shaped sub-tasks (deciding which flags to draft as `[UNVERIFIED]`, which sections to omit). The cautious-by-default + honest-uncertainty patterns map here.

**Anthropic canon anchors:**
- Role assignment focuses behavior
- Long-context: ground in quotes when source docs exceed ~5k tokens
- Chain-of-thought (canonical "let Claude think")
- Examples for output structure

**Persona shape draft:**
- Role: "Analyst examining {topic}. Multi-step reasoning expected; surface intermediate findings."
- Output: structured (headers + tables OK). Length governed by complexity.
- Constraints: cite sources by `path:line` for any concrete claim. Mark `[UNVERIFIED]` for any claim you cannot cite. Honest-uncertainty over confident-fabrication. Surface intermediate reasoning steps.
- Pattern: source-citation block at end (D-17-53 source-grounded self-check, simplified).

### 4.3 code-review — review existing code, identify defects, suggest fixes

**Use case:** Pre-commit review, dual-review of agent output (Goose / Codex / external), audit of legacy code.

**D-17-53 evidence base:** None directly — D-17-53 was authoring not reviewing. But the *frontier-review checklist* documented in chronicle Session 10 ("verify Source-citation table line numbers against the cited source file before commit. Verbatim-quote matching is necessary but not sufficient") is canonical reviewer behavior.

**Anthropic canon anchors:**
- "Code review harnesses" subsection of best-practices doc (lines 148-164 of fetched doc)
- Examples of good vs bad review output
- Role: "Code reviewer focused on {correctness, safety, drift}"

**Persona shape draft:**
- Role: "Code reviewer. Identify defects; do not author."
- Output: defect list with file:line + severity + suggested fix. Cite source verbatim when claiming a defect.
- Constraints: distinguish CORRECTNESS defects (logic errors), SAFETY defects (credential exposure, F6 violations, destructive ops), and DRIFT defects (vs documented doctrine). Don't recommend fixes you can't justify from the source. Don't pad.
- Verbatim-block requirement for every claimed defect: quote the offending lines.

### 4.4 decomposition — break complex problems into sub-specs

**Use case:** Multi-step work where the orchestrator wants to delegate sub-tasks to subagents (claude-local subagent pattern: decomposer→implementer→reviewer).

**D-17-53 evidence base:** None directly — but `~/.claude/agents/decomposer` already exists and the persona is well-anchored in the platform's autonomous-coding doctrine.

**Anthropic canon anchors:**
- "Subagent orchestration" (best-practices §)
- "Chain complex prompts"
- Examples of well-vs-poorly decomposed specs

**Persona shape draft:**
- Role: "Task decomposer. Convert problem statement into N independently-executable specs."
- Output: structured list of specs, each with: goal, success criteria, inputs, expected outputs, no cross-dependencies.
- Constraints: each spec must be independently executable (no shared mutable state). Cite source for any concrete fact (file path, function name) referenced in a spec. If a spec needs information you don't have, the spec includes a "verify first" step rather than guessing.

---

## 5. Library design proposal (WP-03 scope)

### 5.1 Filesystem layout

```
config/prompts/library/
├── README.md                       # Index + version policy + contribution guide
├── _common/
│   ├── preamble-standing.md        # Standing constraints (read-only, surface-back, [UNVERIFIED] convention)
│   ├── preamble-source-fidelity.md # Verbatim-block + source-citation table (Session 9 canonical)
│   ├── preamble-honest-uncertainty.md
│   └── preamble-no-padding.md      # "Skip preamble. Open with X."
├── voice-fast.md                   # Persona template
├── deliberate-analysis.md
├── code-review.md
└── decomposition.md
```

**Versioning:** Each persona file declares `version: vX.Y.Z` in YAML frontmatter. Preamble snippets versioned similarly. Bumping a preamble version does not auto-bump consumer personas — explicit ref required, so personas can pin to a tested-stable preamble version.

**Composition pattern:** Each persona file `<include>`s the standing-preamble snippets it requires (markdown-include style or explicit copy-with-pin) rather than duplicating verbatim. This is how D-17-53 evolved the strengthened preamble — substituting one component (verbatim-block instruction) into existing standing constraints — and the library should preserve that compositional shape.

### 5.2 XML-tag structure (per Anthropic canon)

Each persona template emits a system prompt of shape:

```xml
<role>
  {one-sentence role assignment}
</role>

<context>
  {project-specific framing — what platform, which authority docs apply}
</context>

<constraints>
  <constraint id="standing">{verbatim from _common/preamble-standing.md}</constraint>
  <constraint id="source-fidelity" optional="true">{verbatim from _common/preamble-source-fidelity.md}</constraint>
  <constraint id="no-padding">{verbatim from _common/preamble-no-padding.md}</constraint>
</constraints>

<output_format>
  {persona-specific output format spec}
</output_format>

<examples>
  <example index="1"><input>...</input><output>...</output></example>
  <!-- 1-3 anchor examples -->
</examples>
```

The user prompt is then layered on top with `<task>` + `<sources>` (long-context: sources at top, task at bottom).

### 5.3 Persona × cell × work-class matrix

The library is *persona-keyed* but D-17-53 proves persona effectiveness varies by **(model cell × work-class)**. WP-05 doctrine should document the matrix:

| Persona | Cell where validated | Status |
|---|---|---|
| voice-fast | claude-pro (Anthropic API) | UNVALIDATED — first deployment |
| deliberate-analysis | claude-pro | UNVALIDATED |
| code-review | claude-pro | UNVALIDATED |
| decomposition | claude-local (qwen2.5-coder:32b) via existing `~/.claude/agents/decomposer` | INDIRECTLY validated by autonomous-coding workflow |
| (any persona) | Goose+qwen3-coder:30b × C1a | **C1a SUSPENDED indefinitely** per D-17-53 Session 13 demotion. Library can route work to this cell only on C1b sub-class (narrative chronicle/doctrine notes without quote citations). |

The library design respects this — personas are templates, but the **router** (WP-04) is what makes the cell-routing decision. A persona alone doesn't fix a cell-class mismatch.

---

## 6. Open questions for operator decision (gating WP-03)

### Q1. Library compositional shape — markdown-include vs explicit-copy-with-pin?

- **Option A (markdown-include):** preamble snippets live in `_common/`; persona files reference them via `{{include: _common/preamble-standing.md@v1.0}}` syntax. Library tooling resolves at build-time. **Pro:** single source of truth; easy preamble bumps. **Con:** new build tooling required; debugging is one indirection deeper.
- **Option B (explicit-copy-with-pin):** persona files contain the verbatim preamble text plus a `# pinned: _common/preamble-standing.md@v1.0` comment. **Pro:** no new tooling; the persona file is self-contained and readable. **Con:** preamble changes require touching every persona file. Drift risk.
- **Recommendation:** **Option B for v0.1.0** (faster to ship; no tooling investment); migrate to Option A if drift becomes a real cost. The library is currently 4 files; copy-pin overhead is negligible at this scale.

### Q2. Persona routing target — litellm vs Open WebUI?

- **litellm-gateway** is the platform's canonical LLM proxy; supports `model_alias` mapping + per-route system-prompt injection. Routing pattern: define `voice-fast`, `deliberate-analysis`, etc. as model aliases that map to (model + persona system prompt). Consumers call `litellm.completion(model="voice-fast", ...)`. **Single touchpoint.**
- **Open WebUI** is a chat UI; persona routing there is per-conversation-template, not per-API-call. Useful for chat workflows but not for programmatic consumers (subagents, scripts).
- **Recommendation:** **Both. Primary: litellm aliases (programmatic + subagent path). Secondary: Open WebUI templates for operator chat workflows.** WP-04 covers both surfaces.

### Q3. Source-fidelity preamble — gate on substrate-shape?

D-17-53 Session 11 substrate-shape correlation: verbatim-block instruction works on line-aligned source (Python argparse), fails on structured-document source (XML plists). WP-05 doctrine should document this. **Question for operator:** should the library *itself* differentiate (e.g. `code-review-line-aligned-source.md` vs `code-review-structured-source.md`) or should this be a runtime decision documented in the doctrine but not surfaced as separate templates?
- **Recommendation:** runtime decision documented in doctrine. Two near-identical templates differing only by a footnote add maintenance burden and surface a distinction the persona-layer is the wrong place to encode. The substrate-shape distinction belongs in the work-class taxonomy (D-17-53 class-taxonomy.md), and the operator/router applies the gate.

### Q4. Anchor examples — how strict is the "must include" recommendation?

Anthropic canon: 3–5 examples for best results. D-17-53 pre-strengthened sessions (2-8) had ZERO examples and worked acceptably for 4 of them, failed for the other 4 in shape #5 (source-fidelity). After strengthening, Session 9 had ZERO examples and was clean; Sessions 10-13 had ZERO examples and 4-of-4 had failures.
- **Question:** should each WP-03 persona ship with example(s)? voice-fast and decomposition can ship with examples easily. deliberate-analysis and code-review require example construction work that may double WP-03 scope.
- **Recommendation:** **Examples for voice-fast and decomposition in v0.1.0; deliberate-analysis and code-review ship example-less in v0.1.0 with a backlog item to add examples after first measured deployment.** Don't gate v0.1.0 on perfect-example construction; do gate v1.0.0 (post-validation) on example presence.

### Q5. Library scope — does this replace the existing CLAUDE.md doctrine blocks?

CLAUDE.md currently embeds doctrine at the project level (e.g. "Container Hardening", "DNS Authority Doctrine (D-17-21)") that subagents/sessions read on load. The prompt library is *operational personas* — different layer. They do not conflict.
- **Recommendation:** library is additive. CLAUDE.md doctrine remains the project-context layer. Personas reference doctrine where applicable but don't replicate it. WP-05 doctrine clarifies the layer split.

---

## 7. WP-03 work estimate

| Task | Estimate | Confidence |
|---|---|---|
| Author 4 persona files (`config/prompts/library/{voice-fast,deliberate-analysis,code-review,decomposition}.md`) with frontmatter + role + XML structure | 60 min | High |
| Author 4 `_common/` preamble snippets | 30 min | High |
| Author `config/prompts/library/README.md` (index + version policy + composition pattern) | 20 min | High |
| Construct 1–3 anchor examples for voice-fast + decomposition | 30 min | Medium (writing examples is fiddly) |
| Surface back to operator | 10 min | High |
| **Total WP-03** | **~150 min** | Medium-high |

WP-04 (litellm + Open WebUI routing) ~60 min. WP-05 (doctrine) ~45 min. Within the 4h cap with comfortable margin.

---

## 8. Surface-back: operator decisions required

Before WP-03 begins, please decide:

1. **Q1 (compositional shape):** Option A (markdown-include + tooling) or Option B (explicit-copy-with-pin)? **Recommendation: B for v0.1.0.**
2. **Q2 (routing target):** litellm aliases primary + Open WebUI templates secondary, or one-or-the-other? **Recommendation: both.**
3. **Q3 (source-fidelity gate):** runtime decision via doctrine or two-template split? **Recommendation: runtime decision.**
4. **Q4 (anchor examples):** v0.1.0 ships examples for which personas? **Recommendation: voice-fast + decomposition only; deliberate-analysis + code-review example-less in v0.1.0 with backlog.**
5. **Q5 (library scope vs CLAUDE.md):** confirm library is additive operational personas, not a replacement for project-context doctrine? **Recommendation: confirm additive.**

If all five recommendations land, WP-03 proceeds with: copy-pin preamble shape, both routing surfaces in WP-04, runtime-decision substrate-shape gating, examples for 2-of-4 personas, library-as-additive-layer. Estimated WP-03+04+05 closure within 4h cap.

---

## 9. Out of scope for D-17-90 (parking lot)

- **D-17-91 (model benchmark):** Gemma 4 vs Qwen3-Coder-Next is a separate deliverable. The persona library does not depend on model choice — the library is *what to ask for*; model selection is *who to ask*. Library can ship and be deployed with current cell roster (claude-pro, claude-local, Goose) and absorb new cells as D-17-91 lands.
- **D-17-92 (Cisco Provenance Kit):** model provenance gate; sibling to D-17-91. Independent path.
- **C1a re-enablement on Goose:** parked in chronicle; re-attempt requires either class redefinition (C1b sub-class only) or a different model cell (D-17-91 outcome). Library handles this via the cell-routing matrix in §5.3, not by changing the persona templates.
- **Library evolution to v1.0.0:** post-WP-04 measured deployment; v1.0.0 gate is N=5 successful uses per persona without operator-flagged defect.
