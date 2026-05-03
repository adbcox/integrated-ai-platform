# Goose session pipeline — durable doctrine

The operational pattern for a single Goose execution session
under §18.O migration: prompt construction, invocation, review,
chronicle. Items here outlive any single deliverable; revisions
append to the bottom with date + originating WP.

This chronicle exists because the §18.O framework is only as
trustworthy as the per-session evidence it accrues. A session
without a recorded prompt, recorded output, recorded review state,
and recorded class assignment cannot count toward an N=5 gate —
not because the model didn't do work, but because the *evidence
of clean execution* is what the gate counts. The pipeline fixes
the shape of evidence so promotion claims are checkable.

Sibling chronicles:
- `execution-surface-roles.md` — role boundary (operator approves;
  EXECUTION drafts/edits/runs; AUTONOMOUS doesn't apply here)
- `promotion-criteria.md` — N=5 gate that consumes session
  evidence
- `class-taxonomy.md` — class assignment per session
- `goose-capability-boundary.md` — capability-surface posture
  (what extensions are enabled at session time)
- `migration-telemetry.md` — telemetry the session must record

---

## The five-stage pipeline

Every Goose session under §18.O migration passes through these
five stages. Skipping a stage forfeits the session for promotion
accounting; the work may still be useful, but it doesn't count
toward N=5.

```
1. Brief        →  2. Prompt   →  3. Invoke    →  4. Review    →  5. Chronicle
   (CONTROL)       (CONTROL)      (EXECUTION)     (CONTROL)       (joint)
```

Role attribution per `execution-surface-roles.md`: stages 1, 2, 4
sit on the CONTROL side; stage 3 is EXECUTION; stage 5 is joint
(EXECUTION drafts, CONTROL approves before commit).

### Stage 1 — Brief

CONTROL writes a brief that fixes:

- **Class assignment** — which class from `class-taxonomy.md`
  this session falls under. If no class fits, surface back
  before proceeding (per "How to add a class" in
  `class-taxonomy.md`).
- **Cell identification** — (surface, class) explicitly named.
  This session counts toward this cell's promotion accounting,
  no other.
- **Inputs** — the exact source files, commands, or upstream
  outputs the session reads. Inputs that aren't named in the
  brief don't count as inputs even if the model accesses them;
  unstated input use is a defect at review time.
- **Outputs** — what the session is expected to produce. Net-new
  file? Edit to existing file? Surface-back document only?
  Output shape must match the class's write-shape.
- **Capability scope** — which extensions are in scope for this
  session. Default is `goose-capability-boundary.md` Posture 1
  set; deviations must be justified.
- **Surface-back triggers** — conditions under which the session
  should stop and surface back rather than proceed. Default
  triggers: input ambiguity, scope question, encountered error
  the model can't classify.

The brief is short — a paragraph or two — but every field above
is populated. A brief without explicit class assignment cannot
produce a session that counts toward N=5; the gate criteria
are class-scoped, so unscoped sessions accrue evidence to no
specific cell.

### Stage 2 — Prompt construction

CONTROL composes the prompt from the brief. The prompt structure:

```
[STANDARD PREAMBLE]

[BRIEF — class, cell, inputs, outputs, capability scope]

[INPUTS — explicit file paths or paste-in content]

[SURFACE-BACK TRIGGERS]

[OUTPUT FORMAT EXPECTATIONS]
```

**Standard preamble** (recurring corrective instructions, derived
from observed failure modes and updated as patterns surface):

- *"If uncertain about whether a section is necessary, omit
  rather than pad. Reference docs are concise; sections-because-
  docs-have-them is wrong."* (from D-17-13 WP-06 padding
  observation)
- *"If a failure mode was encountered during the work itself,
  document it explicitly even if it feels like meta-information
  about the run."* (from D-17-13 WP-06 self-blind observation)
- *"If you encounter ambiguity, surface back rather than
  guessing. Surface-back is not failure; it is the correct
  output for under-specified work."* (general — applies to all
  classes)

The preamble is class-agnostic and surface-agnostic. Class- or
cell-specific corrections live in the brief, not the preamble —
the preamble is for failure modes that apply across the
taxonomy.

**Prompt is preserved.** The exact prompt that drives the session
is saved (typically to `docs/phase-NN/d-NN-NN/wpNN-evidence/
prompt.txt`). Without the prompt, post-hoc review can't
distinguish "the model did the wrong thing" from "the prompt
asked for the wrong thing." Evidence retention is part of the
pipeline, not optional.

### Stage 3 — Invoke

EXECUTION runs the session. Default headless invocation pattern:

```bash
GOOSE_MODE=auto goose run --no-session \
    --instructions /path/to/prompt.txt \
    > /path/to/session.log 2>&1
```

- `GOOSE_MODE=auto` — per-invocation override; the config
  default (`smart_approve`) is correct for interactive sessions
  but blocks headless. Do not change the config default. See
  `goose-capability-boundary.md` "Headless invocation gotcha".
- `--no-session` — disables the persistent session storage
  Goose normally keeps. Each pipeline session is a one-shot;
  cross-session memory is a different feature surface that
  hasn't been validated.
- `--instructions /path/to/prompt.txt` — points at the prompt
  file from stage 2. Inline `-t "..."` works for ad-hoc but
  doesn't preserve the prompt for evidence retention; prefer
  the file form.

**Session log preserved.** The invocation captures stdout+stderr
to a session log (typically `session.log` next to `prompt.txt`).
This is the per-session ground truth: what tool calls the model
made, what they returned, what the model emitted as output. The
log is what review reads, not the model's word.

**No mid-session intervention.** EXECUTION runs the session to
completion (or to a surface-back trigger). Operator does not
interject mid-session to redirect the model; that turns the
session into a mixed-authority artifact whose evidence value is
zero (you can't tell which behaviors are the model's and which
are the operator's). If the session is going off-rails, let it
finish and review accordingly — the off-rails behavior is the
evidence.

### Stage 4 — Review

CONTROL reviews the session log + output. Review checks, in order:

1. **Tool-call structural validity.** Every emitted tool call
   parsed cleanly, named a real tool, stayed within declared
   capability scope. Substrate-level malformations (e.g. F1
   regression, garbled JSON, hallucinated tool names) are
   recorded immediately — these forfeit the session for the
   gate but inform substrate stability.
2. **Scope adherence.** All file reads, command runs, network
   calls were within the brief's input scope. Out-of-scope
   access is a defect even if the model didn't act on what it
   read.
3. **Output match.** Did the model produce the output shape the
   brief specified? Net-new doc when net-new was asked? Edit
   when edit was asked? Surface-back when surface-back was the
   correct answer? Output-shape mismatch is a defect.
4. **Output quality.** Is the content correct, well-grounded,
   appropriately structured? Defects here are corrections,
   not gate-failures — corrections are the expected outcome of
   review; the question is the *rate* of correction across N
   sessions.
5. **Doctrine compliance.** No credential exfiltration, no
   fabricated facts presented as observed, no out-of-scope
   recommendations. Doctrine violations are immediate
   demotion triggers per `promotion-criteria.md`, not
   correction-rate noise.

Review state for the session is one of:
- **Clean** — no defects, output committed as-is (rare)
- **Defects-corrected** — defects found, corrections applied,
  output committed (typical — D-17-13 WP-06 was 75/25
  Goose/frontier corrections)
- **Rejected** — defects too extensive to correct, session
  output discarded, brief or prompt revisited
- **Doctrine-violated** — demotion trigger; cell auto-demotes
  per `promotion-criteria.md`

### Stage 5 — Chronicle

Joint stage: EXECUTION drafts the chronicle entry from the
session log + review notes; CONTROL reviews and approves before
commit (per `execution-surface-roles.md` rail #4 — drafts vs
approval split).

The chronicle entry records:

- **Cell** — (surface, class) for promotion accounting
- **Session number toward N** — "session 3 of 5 toward N=5
  gate for cell (Goose+qwen3-coder:30b, C1)"
- **Wall-clock time, tool-call count, structural validity**
- **Output split** — Goose-authored % vs frontier-corrected %
  (the migration-economics datapoint)
- **Review state** — clean / defects-corrected / rejected /
  doctrine-violated
- **Defects observed** — taxonomy of corrections, for
  prompt-engineering feedback and demotion-trigger
  surveillance
- **Substrate state** — Ollama version, model version, anything
  that might have shifted since the previous session

The chronicle entry lands in the cell's promotion record (the
section in `promotion-criteria.md` "Empirical evidence" or its
class-specific successor) and in any deliverable-specific WP-08
chronicle that owns the session.

**Evidence files preserved.** `prompt.txt`, `session.log`, and
the chronicle entry together form the session's evidence
package. They live under `docs/phase-NN/d-NN-NN/wpNN-evidence/`
and are not pruned even after the deliverable closes — they're
the audit trail for any future cell-promotion claim.

---

## Why each stage is in the pipeline

Each stage is non-negotiable because each one prevents a specific
failure mode. Removing any one of them produces a class of
sessions that look like work but don't accrue trustable evidence.

| Stage | Failure prevented if present | What happens if skipped |
|---|---|---|
| Brief | Unscoped session | Session evidence has nothing to attribute to |
| Prompt | Lost causality | Can't distinguish "model wrong" from "ask wrong" |
| Invoke | Mixed authority | Mid-session operator nudges contaminate evidence |
| Review | False-positive promotion | Defects ship; gate criterion 1 (clean) is unverifiable |
| Chronicle | Unconsumable evidence | Sessions don't roll up into promotion accounting |

The pipeline is structurally identical to the worked-example
pattern that produced D-17-13 WP-06 (Goose drafts → operator
reviews → frontier corrects → operator approves → chronicle
records). The pipeline is the pattern, generalized.

---

## Anti-patterns

These are sessions that *look like* pipeline runs but don't
qualify for promotion accounting. Each is named so future
deliverables don't accidentally count them.

### Anti-pattern 1 — The unprompted session

Operator types a question into Goose interactively, gets a
useful answer. No `prompt.txt`, no class assignment, no review
record. This is fine as a development affordance; it does not
count toward N=5 for any cell.

### Anti-pattern 2 — The mid-session redirect

Operator sees Goose going off-rails, interrupts, redirects.
Goose finishes the redirected work successfully. The output is
now a mixed-authority artifact — it captures neither "what
Goose would have done" nor "what frontier would have done."
The session does not count.

### Anti-pattern 3 — The retroactive class assignment

Session ran without an explicit class in the brief. Reviewer
later decides "that was a C2 class session" and counts it
toward C2's gate. Retroactive assignment is unfalsifiable —
any session can be labeled in hindsight to fit a desired
narrative. Sessions count toward the class assigned *in the
brief*, before the work started.

### Anti-pattern 4 — The unrecorded clean session

Goose ran cleanly, output landed, no chronicle entry was
written. The session may have produced useful work, but
without a chronicle record there is no evidence package to
audit. The session does not count.

### Anti-pattern 5 — The substrate-changed run

Substrate (model version, Ollama version, Goose version)
changed since the previous session in the cell. The new session
may be clean, but it's not on the same substrate the previous
sessions were on — it can't roll up into the same N=5 evidence.
Substrate changes reset the count for the affected cell per
`promotion-criteria.md`.

---

## Worked example — D-17-13 WP-06 mapped to the pipeline

The first measured cell session, retroactively mapped to confirm
the pipeline shape:

- **Stage 1 — Brief.** CONTROL identified class C1 (read N
  source files + draft a reference doc), cell (Goose+qwen3-
  coder:30b, C1), inputs (`config/goose/config.yaml`,
  `scripts/goose/README.md`, `goose-capability-boundary.md`),
  output (net-new `docs/runbooks/goose-operations.md`),
  capability scope (Posture 1), surface-back triggers (input
  ambiguity, scope question).
- **Stage 2 — Prompt.** Composed prompt was saved to
  `docs/phase-17/d-17-13/wp06-evidence/prompt.txt`.
- **Stage 3 — Invoke.** `GOOSE_MODE=auto goose run --no-session
  --instructions ...` produced
  `docs/phase-17/d-17-13/wp06-evidence/session.log` (51
  seconds, 6 tool calls, all structurally valid).
- **Stage 4 — Review.** CONTROL reviewed the session log + draft
  output. Five defects identified (padding sections, missing
  GOOSE_MODE failure mode, hang-cause shallowness, redundant
  capability list, missing operator-review section). Review
  state: defects-corrected.
- **Stage 5 — Chronicle.** Frontier EXECUTION drafted
  `goose-capability-boundary.md` "Observed behavior" section and
  `WP08_CHRONICLE_NOTES.md` entries. CONTROL approved. Output
  split (75/25) recorded to the cell's promotion record.

The session counts as session 2 of 5 toward N=5 gate for cell
(Goose+qwen3-coder:30b, C1). The pipeline ran cleanly; the
evidence package is preserved; the chronicle entry is approved.

---

## Why this lives in `architecture-facts/`

Session pipeline outlives D-17-53. Every downstream cell-promotion
deliverable will reference these stages, not the phase-17 file
tree. Phase docs reference *events*; architecture-facts reference
*durable posture*.

This chronicle is a foundational pointer for `promotion-
criteria.md` (which counts pipeline-clean sessions toward gates)
and for any deliverable that runs Goose sessions for promotion
accounting.
