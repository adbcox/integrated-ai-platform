# Capability self-knowledge

**Status:** Canonical reference for the platform's pattern around AI
capability discovery and false-negative blockers. D#22
architecture-fact: this is the canonical reference; if this file
disagrees with any other doc, this file wins.

**Doctrine ID:** D#23 (added in this deliverable)

## Related canonical refs

For canonical per-agent role definitions (work-class, default LiteLLM tier, default model, capability boundaries, posture) for the six verified Track 2 agents (Aider / Goose / Serena / OpenCode / Continue / OpenHands), see **ADR-A-020 §2** (`docs/adr/ADR-A-020-track2-agent-roles.md`).

This doctrine doc remains the substrate for *capability-self-knowledge methodology* (the four flavors of false-negative blockers + the unblock patterns); ADR-A-020 §2 is the substrate for *per-agent role state* (who routes what at which tier). Cross-reference symmetry: this doc describes the discovery pattern; ADR-A-020 records the resulting agent-identity decisions.

## Pattern observed

AI systems (Claude across surfaces; eventually local models like
Qwen3-Coder, Gemma 4) declare blockers that are not actual blockers.
The capability exists, the tool surface is available, the work is
achievable — but the AI's default response is "I can't do that."
The operator only catches the false negative if they have prior
empirical knowledge of the capability OR happen to surface external
evidence.

**Operator quote (verbatim, 2026-05-02):**
> "I want it's capabilities and not be lazy or quit after it
> [previews] something as blocker when it isn't"

**Cost:** the operator becomes the capability-discovery engine for
every system they use. Every novel task carries a friction tax of
"did I already verify this works, or do I need to go Google evidence?"

## Four diagnostic flavors

The same observable behavior ("I can't do that") has four distinct
causes with different fixes. Operators must distinguish them to
apply the right unblock — Flavor A's fix doesn't unblock Flavor C,
and so on.

### Flavor A — Training-data gap

> **Pattern shape**
> Operator: "Do task X."
> AI: "I don't know how to do X."
> Operator: [surfaces evidence article(s) showing AI/peers doing X]
> AI: "Oh, yes — let me proceed."

The AI genuinely doesn't know about the specific application even
though the underlying capability exists. The model can generate SVG,
JSON, Ruby, HTML — but the application "use these primitives to
build a floor plan" wasn't well-represented in training. Article
injection bridges the gap by giving the model a concrete pattern it
hadn't generalized to.

**Why the unblock works:** the model updates its self-model from the
in-context evidence. The capability was always there; only the
self-knowledge was missing.

**When the unblock DOESN'T work:** when the capability genuinely
isn't there (e.g., model lacks a specific output format the article
assumes). Surfacing evidence won't manufacture the capability.
Distinguish: does the article describe the SAME model class doing
the task, or a different one?

**Canonical example.** Floor-plan generation, claude.ai +
Claude Code. See
`/Users/admin/intake-parking/2026-05-02-d-17-23-capability-self-knowledge.md`
§"Example 1" for the source articles operator used.

### Flavor B — Tool-surface gap

> **Pattern shape**
> Operator: "Do task X using tool Y."
> AI: "I don't have access to Y."
> Operator: [configures Y in the AI's tool surface]
> AI: "Now I see Y — proceeding."

The AI knows how to do task X in principle, but the specific tool
or MCP server or extension needed isn't loaded in the current
session. Different sessions of the same model, with different tool
configurations, will give honest-but-opposite answers about whether
they can do the same task. The "I can't see Gmail" in one session
and "Here's your inbox" in another session, both from the same
model class, are both truthful — for their respective tool surfaces.

**Why the unblock works:** the AI's "I can't" was scoped to
"with my current tools." Configuring the tool changes the input
to the same scoped check.

**When the unblock DOESN'T work:** when the operator configures the
wrong tool, or when the AI's framework doesn't actually wire newly
configured tools into the running session (a real product gap, not a
self-knowledge gap). Verify the tool is actually loaded, not just
configured at the OS level.

**Canonical example.** Gmail integration in Claude Code (web)
declined access until operator opened the Chrome extension; same
session subsequently engaged with the work. See
`/Users/admin/intake-parking/2026-05-02-d-17-23-capability-self-knowledge.md`
§"Example 2". Empirical contrast captured in
`/Users/admin/intake-parking/2026-05-02-d-17-23-transcript-analysis.md`
Pattern 3 — same model class, different surface state, different
answer.

### Flavor C — Cautious framing

> **Pattern shape**
> Operator: "Do task X."
> AI: "I should not advise on X — consult a professional."
> Operator: "You're being lazy/cautious. Look specifically at <anchor>."
> AI: "You're absolutely right — I was being overly cautious." [proceeds]

The AI knows it could attempt the task and has the tools, but
defaults to "I shouldn't help with this" out of caution. Common on
sensitive-adjacent tasks (legal, medical, professional design,
financial advice). The capability is present; the framing
suppresses it.

**Why the unblock works:** naming the behavior + providing a
specific prompt anchor + explicitly granting non-stamping
permission ("you're not the architect of record; you're reasoning
about geometry I'll verify with one") repositions the task outside
the cautious frame. The model engages with what it could always do.

**When the unblock DOESN'T work:** when the caution is correct.
Sometimes "consult a professional" is the right answer. Distinguish:
is the operator asking for a stamped decision, or for analysis the
operator will verify? The unblock is for the latter case only.

**Canonical example.** Spatial reasoning over architectural plans —
Claude initially declined ("I should not fabricate specifics about
exact dimensions") and offered the deflection workaround "send to
the architect"; engaged fully after operator named the behavior and
provided a more specific anchor. See
`/Users/admin/intake-parking/2026-05-02-d-17-23-transcript-analysis.md`
Pattern 1 (transcript lines 70–86 — the pivot moment).

### Flavor D — Over-constraint inference

> **Pattern shape**
> Operator: "Functional requirement: X."
> AI: "Got it — so the design must include specific-property-Y, and
> dimension-Z, and feature-W…" [adds constraints not stated]
> Operator: "No, that's a false constraint. I didn't ask for that."
> AI: "You're right — I was collapsing too early."
> [Repeats next turn with a different premature collapse.]

The AI translates loose operator intent into specific premature
commitments and treats those commitments as fixed. The translation
is well-intentioned (it's trying to be helpful by moving from
abstract requirement to concrete spec) but each translation adds
constraints the operator hadn't actually stated. The operator must
repeatedly walk back the AI's helpful additions; cost is
de-confliction work every iteration.

**Why the unblock works:** explicit "treat this as exploration, not
design" framing grants the AI permission to NOT lock in inferred
constraints. Reframing requirements as a list-to-research rather
than a spec-to-implement removes the pressure to commit.

**When the unblock DOESN'T work:** when the operator actually does
want a spec proposal and the AI's collapses are the proposal. The
unblock is for the discovery phase; later a different framing
("now propose the design") is the right prompt.

**Canonical example.** Design iteration where loose "I want a three
car garage" was inferred as "must store three vehicles
simultaneously and remain functional for vehicle work" — operator
walked back both inferences. See
`/Users/admin/intake-parking/2026-05-02-d-17-23-transcript-analysis.md`
Pattern 2 (transcript lines 220–270, multiple constraint-walkback
cycles).

## What this doctrine does NOT claim

- **Does not claim Claude's hedging is always wrong.** Sometimes
  the caution is correct. The doctrine is about distinguishing
  false-negative caution from genuine limitation.
- **Does not claim local models close all four flavors.** Open-weight
  models like Qwen3-Coder and Gemma 4 don't carry the same
  caution-tuning Claude has, so they directly close Flavor C
  (different tradeoffs — less safe in some cases, but that's the
  trade). Flavors A (training-data gap), B (tool-surface gap), and
  D (over-constraint inference) still apply to local models.
- **Does not claim a registry can map every possible capability.**
  Anthropic ships features faster than the operator can map. The
  registry (`docs/architecture-facts/known-capabilities.md`) is the
  operator's working set, not exhaustive truth.
- **Does not try to "fix" Claude's hedging.** That's an Anthropic
  product-side concern. The doctrine is operator-facing: how to
  detect and unblock false negatives in the systems we already use.

## Local-system relevance

The deeper question is: can the local AI stack (Goose on
Qwen3-Coder-Next via exo, per D-17-13/14) avoid this pattern?

Partial answer:
- Open-weight models lack Claude's caution-tuning → **closes
  Flavor C directly.** Different tradeoffs (e.g., model will attempt
  a task it shouldn't), but the false-negative cost is gone.
- Tool-surface gaps (Flavor B) **still apply** — local model only
  knows tools it's exposed to via Goose / xindex-mcp / etc.
- Training-data gaps (Flavor A) **still apply** — local model has
  its own knowledge boundaries, and they're often narrower than
  Claude's.
- Over-constraint inference (Flavor D) **still applies** — every
  helpful AI is at risk of premature collapse; this isn't
  caution-tuning specific.

So the local-system answer is: closes C, doesn't close A/B/D. The
known-capabilities registry helps with all four.

## When operators trust "I can't do that" as final

Per the diagnostic runbook
(`docs/runbooks/capability-discovery.md`), operators work through
six steps before accepting a blocker:

1. Registry hit?
2. Tool-surface gap (Flavor B)?
3. Training-data gap (Flavor A)?
4. Cautious framing (Flavor C)?
5. Over-constraint inference (Flavor D)?
6. If none of the above: real limitation, document as
   confirmed-blocker in the registry with date, attempted unblocks,
   current workaround.

Only after step 6 does "I can't do that" become canonical for that
capability + surface combination.

## Hand-off to D-17-11 (system prompt library)

D-17-23 defines a slot in the local LLM system prompt library that
D-17-11 fills. Slot specification: prompt content that pre-grants
permission for capabilities the operator commonly wants and Claude
or local models commonly hedge on. Initial fill is informed by the
known-capabilities registry — entries flagged Flavor C/D map most
naturally to permission-granting prompt content; Flavor A/B entries
map to surface/tool documentation rather than prompt content.

The slot is mandatory in D-17-11's library; specific prompt content
is D-17-11's authorship. See PROJECT_FRAMEWORK.md Phase 17 plan,
D-17-11 entry, for the slot's binding contract.

## D#23 — capability self-knowledge is suspect by default

AI capability self-knowledge is unreliable. False negatives
("I can't do that" when the AI in fact can) are common across at
least four distinct failure modes — training-data gaps, tool-surface
gaps, cautious framing, over-constraint inference. Operators MUST
verify before accepting a declared blocker as real, working through
the six-step diagnostic in
`docs/runbooks/capability-discovery.md`. The cost of a wasted
five-minute diagnostic is much smaller than the cost of accepting a
false blocker as canonical and rebuilding around a phantom
limitation.

## See also

- `docs/architecture-facts/known-capabilities.md` — operator-facing
  working registry of empirically-confirmed capabilities and their
  unblock patterns
- `docs/runbooks/capability-discovery.md` — six-step operator
  diagnostic flow
- `docs/PROJECT_FRAMEWORK.md` §3.5 — D#23 doctrine entry
- `/Users/admin/intake-parking/2026-05-02-d-17-23-capability-self-knowledge.md` —
  original intake (goals, scope, three flavors, non-goals)
- `/Users/admin/intake-parking/2026-05-02-d-17-23-transcript-analysis.md` —
  empirical pattern extraction; introduced Flavor D
