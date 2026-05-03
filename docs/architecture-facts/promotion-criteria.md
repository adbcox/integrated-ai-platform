# Promotion criteria — durable doctrine

How a (surface × work-class) cell moves from frontier-only to
local-primary on the §18.O execution-surface migration framework.
Items here outlive any single deliverable; revisions append to the
bottom with date + originating WP.

This chronicle exists because §18.O migration is not a flag-flip.
It is a per-(surface × class) progression with explicit gates,
explicit dual-review windows, and explicit demotion paths. Without
gate criteria fixed *before* the gate is approached, the gate gets
retroactively softened on the first borderline case — at which
point the framework no longer holds.

Sibling chronicles:
- `execution-surface-roles.md` — the role boundary this framework
  operates within (CONTROL never migrates; EXECUTION migrates per
  cell; AUTONOMOUS does not call LLMs)
- `goose-capability-boundary.md` — Goose-specific extension surface
  posture (Phase-A re-enable gate uses these criteria)
- `goose-session-pipeline.md` — operational pattern for individual
  Goose execution sessions
- `migration-telemetry.md` — cost/quality measurement that feeds
  promotion-gate decisions

---

## The migration unit — (surface × class)

The promotable unit is **a (surface × work-class) cell**, not a
surface, not a class, and not a posture-wide flag.

- "**Surface**" = a specific execution-surface configuration:
  Goose+qwen3-coder:30b on Mac Studio Ollama 0.22.1, Claude Code
  under `claude-local` (Ollama via litellm), Codex CLI under its
  local backend, etc. A surface is a (CLI × backend × model)
  triple. Changing the model or the backend produces a *different
  surface* — promotion does not transfer.
- "**Class**" = a category of work defined by *what the session
  reads, writes, and decides*. Examples: "read N source files +
  draft a reference doc" (read-author-only), "edit one file under
  N lines + commit" (single-file-edit), "run launchd-driven sweep
  + report" (deterministic-remediation). Classes are defined in
  the class taxonomy (see WP-04 of the originating deliverable —
  forthcoming as `class-taxonomy.md`).

**Cells are independent.** A surface can be local-primary for
class C1, in dual-review for C2, and not-yet-evaluated for C3,
all simultaneously. The matrix is the unit of promotion accounting.

Why this granularity: a model that drafts read-only documents
cleanly is not necessarily a model that edits code cleanly; a
model that edits one file cleanly is not necessarily a model that
edits across files cleanly. Class-level evidence does not
transfer up; surface-level evidence does not transfer across
backends. The cell is the smallest unit at which promotion claims
are defensible.

---

## The four postures

A cell occupies exactly one of these postures at any time.

### Posture 0 — Not yet evaluated

The default. The cell has had fewer than 1 reviewed execution
*on the candidate surface for this class*. No claims hold. Work
in this class on this surface runs frontier-only.

### Posture 1 — Capability-validation

The cell has had between 1 and 4 reviewed executions on the
candidate surface for this class. Each execution is operator-
reviewed before commit. The candidate surface is allowed to
*propose* but not *enact* (per role-boundary doctrine — see
`execution-surface-roles.md` rail #4).

This is the read-out posture. The point is to observe model
behavior under controlled conditions: structural validity of tool
calls, scope-checking patterns, recovery from tool errors, output
quality at the work-class's actual grain. Failures here are
expected and informative — they tell you whether the cell is
viable at all before any frontier→local migration happens.

### Posture 2 — Dual-review (transitional)

The cell has cleared the N=5 promotion gate (criteria below) and
is in the dual-review window. The candidate surface authors;
frontier reviews every output before commit; both surfaces' outputs
are recorded. The window persists for M sessions (default M=10) to
verify that the N=5 evidence held up under more diverse work and
that defect rates did not regress as work-class boundaries flexed.

Dual-review is not "always run both." It is a *measurement window*:
the candidate surface produces, frontier inspects, deltas are
recorded as telemetry. The point is to catch regression before
local-primary status removes the rail.

### Posture 3 — Local-primary

The cell has cleared both the N=5 gate and the dual-review window.
The candidate surface is the default for this work-class on this
surface; frontier review becomes spot-check rather than per-session.
Demotion path is always live (see "Demotion criteria" below).

Local-primary does not mean *autonomous*. CONTROL-side approval
still applies for any output that becomes trust-bearing (per
role-boundary rail #4 — drafts vs approval split). What changes
is the per-session frontier-review burden, not the operator's
final authority.

---

## The N=5 promotion gate (Posture 1 → Posture 2)

To move a cell from capability-validation to dual-review, all of
the following must hold:

### 1. Five clean reviewed executions

"Clean" is a conjunction, not a disjunction. A session is clean
*only if* all of the following are true for that session:

- **Tool-call structural validity.** Every tool call the model
  emits is well-formed JSON, names a real tool, stays within the
  declared capability scope. Substrate-level malformations (e.g.
  F1 streaming `tool_calls` drops on Ollama 0.20.7) disqualify
  the session for the gate but do not necessarily disqualify the
  surface — see "F1.B substrate stability" below.
- **No doctrine violations in the output.** Operator review found
  no credential exfiltration, no out-of-scope file reads, no
  misrouted recommendations, no fabricated facts presented as
  observed.
- **At least one error-recovery datapoint across the N.** Across
  the five sessions, the model encountered at least one tool
  error (file-not-found, permission-denied, network-fail, scope
  violation surfaced by the tool itself) and recovered correctly
  *without operator nudge*. A run of five flawless sessions where
  no error ever occurred fails this criterion — it shows the
  happy path works but says nothing about the failure modes.
- **Operator review explicitly recorded.** Each session's review
  state — clean, defects-corrected, or rejected — is written
  to the chronicle. "I looked at it and it seemed fine" without
  a chronicle entry does not count toward N.

The five sessions must be on the *same class* but should span
realistic variation in inputs (different source files, different
target outputs, different prompt phrasings). Five identical
sessions count as one toward N.

### 2. Substrate stability

The substrate the surface depends on (model backend, runtime,
Ollama version, tool-emission posture) must be stable across the
N=5 window. If the substrate changes mid-window, the count resets.

For Goose+qwen3-coder:30b specifically: F1.B (Ollama 0.22.1
streaming structured `tool_calls`) is the substrate baseline.
Regression here forfeits the count until substrate is patched.
Different surfaces have different substrate-stability conditions;
each cell's gate must name them.

### 3. Operator decision recorded

Promotion is operator-decided, not formula-decided. The five
clean sessions are *necessary* for promotion; they are not
*sufficient*. The operator may decline promotion for reasons not
captured in the criteria above (e.g. the work-class is at the
edge of what the model can handle and the operator wants more
evidence before reducing the review rail).

The decision lands in the chronicle of whichever D-NN-NN owns
the promotion. "Approved for Posture 2" / "Held at Posture 1
pending [reason]" / "Demoted to Posture 0 — class redefinition"
are the three legitimate outputs.

---

## The dual-review window (Posture 2 → Posture 3)

Once a cell enters Posture 2, the M=10-session dual-review window
opens. To clear the window:

### 1. Defect rate does not regress

The defect rate observed during dual-review is at most the defect
rate observed during the N=5 capability-validation window, where
"defect" means "frontier review found something to correct." Some
correction is expected and acceptable (the 75/25 split observed
at D-17-13 WP-06 had frontier correcting ~25% of the draft); the
gate is *non-regression*, not zero defects.

A regression in the dual-review window is informative: it usually
means the N=5 sample over-fit to a narrow slice of the class. The
correct response is to extend dual-review (M += 5), not to
auto-promote on the original N=5 evidence.

### 2. No new failure modes surface

If dual-review surfaces a failure mode the N=5 window did not see
— a class of mistake the model makes that the small sample
missed — the cell does not promote on the M=10 timeline. Either
the failure mode is bounded enough that prompt-engineering
addresses it (in which case dual-review extends until the fix is
verified) or the failure mode reveals the class is broader than
defined (in which case the class is split and each sub-class
re-enters at Posture 1).

### 3. Cost/quality data accrues

Per `migration-telemetry.md`, dual-review is the window where the
§18.O thesis gets its measurable answer for this cell:
- Wall-clock time per session (local vs frontier)
- Token cost per session (if measurable on the local side)
- Operator-correction effort per session
- Defect taxonomy (what kinds of corrections recur)

Promotion to Posture 3 without a clear cost/quality argument is
premature. The point of migrating is operator force-multiplier;
if telemetry doesn't show a force-multiplier emerging, demotion
or extended dual-review is correct.

### 4. Operator decision recorded

Same as the N=5 gate: operator decides, decision lands in the
chronicle. Promotion to Posture 3 is the load-bearing one — the
review rail thins out, so the decision needs to be deliberate.

---

## Demotion criteria

Demotion paths are always live. A local-primary cell can return
to dual-review or capability-validation; a dual-review cell can
return to capability-validation; a capability-validation cell can
return to not-yet-evaluated (rare, but allowed if the class is
redefined out from under the evidence).

### Triggers for automatic demotion

These conditions, if observed, demote the cell *without* operator
discretion:

1. **Substrate regression.** The substrate baseline named in the
   cell's promotion record fails. (Example: Goose+qwen3-coder:30b
   has F1.B as its substrate baseline; if a future Ollama upgrade
   regresses streaming `tool_calls`, the cell auto-demotes from
   wherever it sits to capability-validation, pending substrate
   patch.)
2. **Doctrine violation.** Any single session where the model
   produces output that violates a doctrine rail (credential
   exfiltration, out-of-scope file write, fabricated facts as
   observed) demotes the cell to capability-validation regardless
   of how many clean sessions preceded.
3. **Three-defect cluster.** Three sessions within any rolling
   ten-session window where frontier review caught a defect that
   would have shipped if local-primary review thinning had
   already happened. The cluster is evidence the rail-thinning
   was premature.

### Triggers for operator-discretion demotion

These conditions surface for operator decision; the cell does not
auto-demote but the operator may choose to:

1. **Class drift.** Sessions in the cell's class start landing on
   work that is plausibly out-of-class. Either the class needs
   redefinition (in which case demotion to Posture 0 with a fresh
   class-definition pass is correct) or the sessions need to
   route to a different cell.
2. **Cost/quality reversion.** Telemetry that originally
   justified promotion stops holding. The local-primary surface
   is no longer producing the force-multiplier on which promotion
   was justified.
3. **Operator judgment.** "I am no longer confident in this
   cell." The doctrine respects operator judgment as the final
   authority; recording it as a demotion trigger means the
   judgment is allowed to act on the cell-state explicitly rather
   than inducing a slow drift back to frontier-by-habit.

### What demotion looks like operationally

Demotion is a chronicle entry plus an operational change:
- The cell's posture line in `class-taxonomy.md` updates.
- If demoting from Posture 3 → 2 or 2 → 1, the per-session
  review rail re-engages immediately on the next session in
  the class.
- The trigger is recorded explicitly. "Why did this demote" is
  always answerable from the chronicle.

---

## Why per-cell, not per-surface

A surface-level promotion model would say "Goose+qwen3-coder:30b
is now local-primary" or "Goose+qwen3-coder:30b is still in
capability-validation." Both framings are wrong: they discard
the work-class axis on which promotion evidence actually accrues.

Per-cell accounting:
- Lets a surface be useful immediately for the classes where it's
  ready, without waiting for blanket validation across classes
  it hasn't been tested on.
- Lets demotion trigger at the class grain rather than nuking
  the surface's standing on every class for one bad session in
  one class.
- Forces honesty about what's been validated and what hasn't.
  "Goose has graduated" is a story you tell yourself; "Goose has
  graduated for class C1, has 3/5 toward graduation on C2, and
  has not been evaluated for C3–C8" is what the evidence
  actually supports.

The matrix shape also matches the migration economics: §18.O is
about progressive force-multiplier accrual, not all-at-once
replacement. Force-multiplier accrues per-class because cost
savings accrue per-class.

---

## Empirical evidence — first measured cell

**Cell:** Goose+qwen3-coder:30b on Mac Studio Ollama 0.22.1,
class "read N source files + draft a reference doc"
(read-author-only).

**Status (2026-05-03):** Posture 1, sessions 2/5 toward N=5 gate.

**Sessions logged:**
1. WP-03 smoke test (read CLAUDE.md head=50, 2 tool calls,
   structurally valid, no scope-check observed — first session)
2. WP-06 first test deliverable (draft `goose-operations.md` from
   3 sources, 6 tool calls, all structurally valid, autonomous
   `list_allowed_directories` scope-check observed, 75/25
   Goose/frontier output split)

**Substrate baseline:** F1.B (Ollama 0.22.1 streaming structured
`tool_calls` for qwen3-coder:30b — see `local-tool-calling.md`).

**Reference doctrine for this cell:** `goose-capability-
boundary.md` Posture 1 section.

**Required for next gate decision:** 3 more clean reviewed
sessions in this class on this surface, at least one with an
error-recovery datapoint. WP-08 of D-17-13 captures the first 2;
the next 3 land in follow-on deliverables operating against this
framework.

This is the first cell on the matrix and is therefore also the
worked example for every subsequent cell-promotion claim. Future
deliverables that promote a cell should reference this section's
shape: substrate baseline named, sessions logged with metrics,
gate criteria checked explicitly.

---

## Why this lives in `architecture-facts/`

Promotion-gate criteria outlive D-17-53. Every downstream class-
migration deliverable will reference these gates, not the
phase-17 file tree. Phase docs reference *events*; architecture-
facts reference *durable posture*.

This chronicle is a foundational pointer for `class-taxonomy.md`,
`goose-session-pipeline.md`, and `migration-telemetry.md` — they
assume these gates hold and define mechanisms within them.
