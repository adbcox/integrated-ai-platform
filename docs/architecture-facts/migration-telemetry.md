# Migration telemetry — durable doctrine

The cost / quality measurement framework that feeds §18.O
migration decisions. What gets measured per session, per cell,
per gate; how the measurements roll up; and what arguments they
support. Items here outlive any single deliverable; revisions
append to the bottom with date + originating WP.

This chronicle exists because the §18.O thesis — *progressive
migration of execution-surface work to local AI is a
force-multiplier on operator capacity* — is empirical, not
axiomatic. Without telemetry that resolves at the cell level,
the migration story devolves into vibes ("Goose feels faster").
Promotion decisions and demotion triggers both consume this
telemetry; without it, the framework is open-loop.

Sibling chronicles:
- `execution-surface-roles.md` — the role boundary the
  framework operates within
- `promotion-criteria.md` — N=5 gate, dual-review window,
  demotion paths (consumes telemetry)
- `class-taxonomy.md` — the cells telemetry attributes to
- `goose-session-pipeline.md` — the pipeline that produces
  telemetry

---

## What gets measured

Telemetry is recorded at three resolutions: per-session,
per-cell-rolling, per-gate-decision. Lower resolutions roll up
into higher ones; nothing is recorded at higher resolution that
isn't derivable from the per-session evidence packages.

### Per-session metrics

Recorded for every pipeline session (per `goose-session-
pipeline.md` Stage 5). All metrics are facts about *this one
session*; rollups happen at the cell level, not in the
per-session record.

| Metric | What it is | Why it's recorded |
|---|---|---|
| Wall-clock | End-to-end seconds from invoke to output landed | Force-multiplier signal — local sessions can be faster (no network hop) or slower (smaller model deliberates longer) |
| Tool-call count | Total emitted tool calls in the session | Substrate-validity + work-shape signal |
| Tool-call structural validity | All / partial / none | Substrate stability gate — F1.B regression demotes the cell |
| Output split | Goose-authored % vs frontier-corrected % | Cost/quality core metric — the §18.O thesis is "this trends toward Goose-dominant"; flat/regressing ratio is the demotion signal |
| Review state | clean / defects-corrected / rejected / doctrine-violated | Gate criterion 1 input |
| Defect taxonomy | Categorized list of corrections (padding, hallucination, scope-miss, structure-error, factual-error, surface-back-failure, etc.) | Prompt-engineering feedback + demotion-trigger surveillance |
| Substrate snapshot | Goose version, model version, Ollama version, capability surface | Substrate-change detection per `promotion-criteria.md` Anti-pattern 5 |
| Operator-correction effort | Frontier-time spent on correction (rough — minutes or "trivial/small/medium/large") | Force-multiplier signal — if frontier-correction effort > local-execution savings, the cell isn't a net win |
| Token cost | Frontier tokens consumed (if any), local tokens consumed (if measurable) | Cost-side migration thesis input |

The measurements are deliberately not all-quantitative. "Operator-
correction effort" is fuzzy on purpose — pretending a 4-bucket
classification is a precise float invents precision the
underlying judgment doesn't have. The point is to record signal
the operator can compare across sessions, not to manufacture a
spreadsheet.

### Per-cell rolling metrics

Computed from the last N sessions in the cell (default N=10 or
all sessions if fewer than 10 exist). Recorded in the cell's
section of `promotion-criteria.md` "Empirical evidence" or its
class-specific successor.

| Metric | Computation | Promotion / demotion signal |
|---|---|---|
| Clean-rate | clean + defects-corrected sessions / total | Gate 1 input — N=5 gate needs 5 of these to be in the "clean" subset (defects-corrected with explicit review record) |
| Defect-rate trend | Last-5 average vs prior-5 average | Force-multiplier signal — should be flat or improving; regression triggers extended dual-review |
| Output-split trend | Goose-% trend over last 10 sessions | Migration economics signal — should trend toward Goose-dominant; flat or regressing is the demotion-discretion trigger |
| Wall-clock distribution | Median + spread | Predictability signal — high-variance wall-clock is a UX-side cost on the operator |
| Defect-taxonomy distribution | Recurring defect categories, ranked | Prompt-engineering feedback — recurring categories belong in the standard preamble |
| Substrate-stability | Sessions on current substrate / total | Promotion gate input — N=5 must be on stable substrate per `promotion-criteria.md` |

### Per-gate-decision metrics

Recorded at the moment of a promotion or demotion decision. The
chronicle entry for the decision cites these explicitly so the
decision is auditable post-hoc.

| Metric | Source |
|---|---|
| Sessions counted toward gate | Per-session records, listed by ID/date |
| Substrate baseline at gate time | Per-session substrate snapshots — must be uniform |
| Defect-rate at gate time | Per-cell rolling clean-rate |
| Output-split at gate time | Per-cell rolling Goose-% |
| Cost/quality argument | Operator's narrative summary citing the above |
| Operator decision | Approve / hold / demote, with reason |

---

## How telemetry feeds gates

The N=5 gate (Posture 1 → Posture 2 per `promotion-criteria.md`)
consumes per-session and per-cell-rolling telemetry directly:

1. **Five clean sessions** — counted from per-session review
   states, filtered to `clean` and `defects-corrected`.
2. **Substrate stability** — counted from per-session substrate
   snapshots; must be uniform across the five.
3. **Error-recovery datapoint** — at least one of the five
   sessions has a `defect-taxonomy` entry that includes a
   tool-error category the model recovered from without
   operator nudge.

The dual-review window (Posture 2 → Posture 3) consumes
per-cell-rolling and per-gate-decision telemetry:

1. **Defect-rate non-regression** — last-5 average ≤ prior-5
   average across the M=10 dual-review sessions.
2. **No new failure modes** — defect-taxonomy distribution
   covers categories already seen in the N=5 window. New
   categories surfacing extends dual-review.
3. **Cost/quality argument** — operator's narrative, rooted in
   wall-clock, output-split, and operator-correction-effort
   trends. The argument is checked against the data, not a
   replacement for it.

Demotion triggers consume per-session telemetry directly:

- **Substrate regression** — substrate snapshot in any session
  diverges from the cell's promotion baseline.
- **Doctrine violation** — review state of `doctrine-violated`
  on any session.
- **Three-defect cluster** — three sessions in any rolling
  ten-session window have review state `defects-corrected`
  with defect categories that "would have shipped if review
  thinning had already happened" (recorded as a flag on the
  per-session record, set by the reviewer).

---

## How telemetry argues the §18.O thesis

The thesis is: *progressive migration of execution-surface
work to local AI is a force-multiplier on operator capacity.*
For the thesis to hold for a given cell, the telemetry must
support all four legs:

1. **Local-side wall-clock comparable to or better than
   frontier.** Falsified by: persistent wall-clock regression
   that doesn't recover with prompt engineering.
2. **Output-split trending Goose-dominant.** Falsified by:
   flat or regressing Goose-% across the dual-review window.
3. **Operator-correction effort trending down or flat.**
   Falsified by: correction effort growing as Goose-% grows
   (output bigger but quality worse — net effort unchanged or
   worse).
4. **Defect taxonomy bounded.** Falsified by: defect categories
   proliferate across the dual-review window — the model
   produces a wider variety of mistakes as the work-shape
   varies, suggesting the cell over-fit to a narrow slice.

A cell that fails any one leg of this argument should not promote
to Posture 3 even if the N=5 gate cleared. The gate is necessary;
the argument is sufficient. Both are required for promotion.

The thesis is *cell-local*. A cell that fails the argument
demotes; it does not falsify the thesis for other cells. The
framework's whole point is class-by-class evidence accrual —
generalization across cells is not claimed and not needed.

---

## What gets recorded where

Evidence is path-conventional so future deliverables can find it
without explicit cross-references in every WP brief.

```
docs/phase-NN/d-NN-NN/wpNN-evidence/
    prompt.txt                # Stage 2 of pipeline
    session.log               # Stage 3 of pipeline
    chronicle-notes.md        # Stage 5 of pipeline (per-session record)

docs/architecture-facts/
    promotion-criteria.md     # Per-cell rolling + per-gate-decision records
    class-taxonomy.md         # Cell list (referenced by per-session records)
    goose-capability-boundary.md   # Substrate snapshots roll up here for the Goose surface
    migration-telemetry.md    # This file — the schema that connects them
```

Per-session records live in their owning deliverable's evidence
directory; per-cell records live in the architecture-facts
chronicles. The asymmetry is intentional: per-session evidence
is bounded to the deliverable that produced it (audit trail
scope); per-cell evidence rolls up across deliverables (the
cell outlives any one D-NN-NN).

---

## What is *not* measured

- **Aggregate productivity.** "How much work did Goose ship this
  week" is not a §18.O metric. The framework is class-by-class;
  aggregating across classes loses the per-cell signal that
  promotion decisions depend on.
- **Surface-level "graduation."** "Has Goose graduated from
  capability-validation" is not a question the telemetry
  answers, because the unit of promotion is the cell, not the
  surface. Per `execution-surface-roles.md` rail #2, this
  question is mis-shaped.
- **Frontier-vs-local quality on identical prompts.** The
  comparison is tempting but expensive (run every prompt
  twice) and largely uninformative — the cells where local is
  worse stay frontier-only, and the cells where local is
  comparable get migrated. The output-split metric captures
  the comparison post-hoc at zero extra cost.
- **Token cost as primary metric.** Token cost is recorded but
  not load-bearing. The §18.O thesis is about operator
  force-multiplier (operator capacity, predictability, review
  ergonomics), not raw inference cost. A cell that saves
  tokens but increases operator-correction effort fails the
  thesis even if the token savings are real.

---

## Why this lives in `architecture-facts/`

Telemetry schema outlives D-17-53. Every downstream cell-promotion
deliverable will record sessions against this schema, and every
gate decision will cite metrics defined here. Phase docs reference
*events*; architecture-facts reference *durable posture*.

This chronicle is the foundational pointer for what the §18.O
framework actually measures — the rest of the framework
chronicles reference these metric names without redefining them.
