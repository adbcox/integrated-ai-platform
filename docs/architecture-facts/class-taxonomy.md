# Class taxonomy — durable doctrine

The initial work-class taxonomy for the §18.O execution-surface
migration framework. Each class is defined by a (read-shape,
write-shape, decision-shape) triple plus an initial migration
tier (Phase-A / Phase-B / Phase-C / Never). Items here outlive
any single deliverable; revisions append to the bottom with date
+ originating WP.

This chronicle exists because promotion claims accrue at the
*class* level, not the surface level (per
`promotion-criteria.md`). Without a fixed taxonomy, "Goose handles
documentation work" becomes a folk claim that no evidence
disproves and no evidence proves. The taxonomy fixes the unit of
account so every promotion claim can be checked against it.

Sibling chronicles:
- `execution-surface-roles.md` — the role boundary (CONTROL /
  EXECUTION / AUTONOMOUS) within which classes sit
- `promotion-criteria.md` — N=5 gate, dual-review window,
  demotion paths (the framework that operates on this taxonomy)
- `goose-capability-boundary.md` — capability-surface posture
  (separate axis: what a surface is *allowed to do* regardless of
  class assignment)

---

## How classes are defined

A class is a (read-shape, write-shape, decision-shape) triple:

- **Read-shape** — what the session ingests. "1 file", "N files",
  "1 directive + context", "M deliverables", "service config +
  spec". Read-shape captures input volume and structure.
- **Write-shape** — what the session produces on disk. "1 new
  doc", "1 existing doc", "M files", "1 script", "approval /
  rejection". Write-shape captures the consequence surface.
- **Decision-shape** — what the session *reasons about*.
  "Structure only", "local logic only", "cross-file consistency",
  "causal reasoning", "architectural judgment", "trust-bearing
  review". Decision-shape captures judgment intensity.

Two sessions are in the same class iff all three shapes match.
Sessions where any shape differs belong to different classes.

The triple is not a complete characterization — language, domain,
codebase familiarity all matter — but it is enough to keep
promotion claims defensible. Per-cell evidence accrues only
within a class; class-level claims do not transfer across the
taxonomy.

---

## Migration tiers

Each class is assigned an initial tier. The tier is the *earliest*
migration target for the class; a class can be held at frontier
beyond its tier on operator discretion, but it cannot be migrated
ahead of its tier without a re-classification pass.

- **Phase-A** — first migration targets. Read-only or
  low-judgment authoring with reviewable output. Net-new artifacts
  or single-file edits where defects are visible at review time
  and operator review is the rail. Phase-A cells are where the
  §18.O thesis gets its earliest empirical answer.
- **Phase-B** — structured authoring or bounded code editing.
  Output has a larger consequence surface (scripts that run,
  doctrine that becomes authoritative, single-file edits that
  ship). Phase-B promotion requires both N=5 evidence in the
  cell *and* operator confidence that the consequence surface
  is acceptable for thinned review.
- **Phase-C** — multi-file or cross-deliverable work where
  reasoning shape is causal or architectural. Even with bounded
  output-shape, the *reasoning-shape* is judgment-heavy. Phase-C
  cells are deferred until Phase-A and Phase-B classes have
  produced a cost/quality argument that justifies extending the
  framework.
- **Never** — CONTROL-role work per
  `execution-surface-roles.md` rail #1. These classes appear in
  the taxonomy for completeness (and to prevent accidental
  reclassification later) but are explicitly excluded from the
  migration framework. They are listed so a future deliverable
  cannot "discover" them as Phase-D candidates.

Migration tier is a *property of the class*. It is not a property
of any specific (surface × class) cell — a Phase-A class on a
poorly-validated surface still has to clear the N=5 gate before
that cell promotes. Tier sets the *ceiling* on how aggressively
the cell can migrate, not the *floor*.

---

## The taxonomy

### C1 — Reference-doc draft from N sources

- **Read:** N files (typically 2–5 source docs/configs)
- **Write:** 1 new doc (markdown reference, runbook, chronicle)
- **Decide:** Structure only — what sections, in what order, at
  what grain
- **Tier:** **Phase-A**
- **Status:** First active cell on the matrix. Goose+qwen3-coder:
  30b on Mac Studio Ollama 0.22.1 — Posture 1, sessions 2/5
  toward N=5 gate (D-17-13 WP-03 + WP-06).
- **Reference cell:** see `goose-capability-boundary.md`
  "Observed behavior" + `promotion-criteria.md` "Empirical
  evidence — first measured cell".

### C2 — Runbook / doc update from observation

- **Read:** 1–N files (existing doc + observed state)
- **Write:** 1 existing doc (edit-in-place)
- **Decide:** Structure + ordering — where the new content fits,
  what existing content it supersedes
- **Tier:** **Phase-A**
- **Notes:** Same risk profile as C1 because frontier reviews
  before commit. Existing-doc edit is not materially riskier than
  net-new draft when output is reviewed; the rail is the review,
  not the file shape.

### C3 — Single-file code edit, ≤50 lines, bounded scope

- **Read:** 1 file + bounded context (imports, called-from sites)
- **Write:** 1 file (edit-in-place)
- **Decide:** Local logic only — within-file correctness, no
  cross-file invariants
- **Tier:** **Phase-B**
- **Notes:** Output runs on a runtime, so consequence surface is
  larger than C1/C2. The "≤50 lines" bound is the gate that
  keeps this distinct from C5 (multi-file refactor); operator
  review can hold the edit in working memory at this size.

### C4 — ADR / doctrine drafting

- **Read:** N files (precedent doctrine, source artifacts,
  related chronicles)
- **Write:** 1 new chronicle / ADR / doctrine entry
- **Decide:** Structured authoring — fitting the new content to
  the chronicle pattern, naming the doctrine rule, citing
  evidence
- **Tier:** **Phase-B**
- **Notes:** Per `execution-surface-roles.md` rail #4 (drafts vs
  approval split): drafting is EXECUTION-side, approval is
  CONTROL-side. The Phase-B tier is on the *drafting* axis;
  approval never migrates. Worked example pattern: D-17-13
  WP-06 runbook — drafted by Goose, corrected by frontier
  EXECUTION, approved by operator.

### C5 — Multi-file refactor, single concern

- **Read:** N files (the refactor's blast radius)
- **Write:** M files (typically the same set, modified)
- **Decide:** Cross-file consistency — invariants that span
  files, rename propagation, signature alignment
- **Tier:** **Phase-C**
- **Notes:** "Single concern" is the gate that keeps this
  distinct from broader rewrites. The judgment-heavy part is
  *what counts as the same concern*; once that's fixed, the
  edits are mechanical, but fixing it is Phase-C reasoning.

### C6 — Bug investigation + fix proposal

- **Read:** N files + tool output (logs, repros, stack traces)
- **Write:** 1 file (proposed fix) OR surface-back document
- **Decide:** Causal reasoning — root cause vs symptom, fix vs
  workaround, regression-risk of the proposed change
- **Tier:** **Phase-C**
- **Notes:** Surface-back-only output (no file write) does not
  reduce the reasoning-shape — the causal chain is the
  judgment-heavy part regardless of whether the session enacts.
  Reclassifying based on output-shape (no write → Phase-B)
  conflates output-shape with reasoning-shape. The reasoning is
  what's being migrated, not the typing.

### C7 — Cross-deliverable synthesis

- **Read:** M deliverables (chronicles, plans, framework rows)
- **Write:** 1 chronicle / PM artifact / decision record
- **Decide:** Architectural judgment — what spans which boundary,
  which deliverables conflict, which precedent governs
- **Tier:** **Never** (CONTROL role)

### C8 — Operator-directive interpretation

- **Read:** 1 directive + project context
- **Write:** Decomposed work plan (which D-NN-NN, which WPs,
  which classes)
- **Decide:** Scope-setting — what's in, what's out, what's
  deferred, what blocks what
- **Tier:** **Never** (CONTROL role)

### C9 — Correctness review of EXECUTION output

- **Read:** 1 EXECUTION artifact + the spec it claims to satisfy
- **Write:** Approval / rejection / corrections-required
- **Decide:** Trust-bearing review — does this output match the
  spec, does it violate doctrine, is it safe to commit
- **Tier:** **Never** (CONTROL role)
- **Notes:** This is the rail that *enables* migration of
  Phase-A/B/C classes elsewhere. Migrating it would collapse
  the framework — see `execution-surface-roles.md` rail #1.

### C10 — Deterministic remediation script authoring

- **Read:** Service config + remediation spec
- **Write:** 1 script (shell, Python, launchd plist)
- **Decide:** Mechanical translation — spec → executable
- **Tier:** **Phase-B**
- **Notes:** Authoring is mechanical (Phase-A-shaped) but the
  *consequence surface* is larger: scripts run autonomously
  post-deploy (typically via launchd), so a defect that
  bypasses review surfaces in production rather than at commit.
  Phase-B is the consequence-surface adjustment, not a
  reasoning-shape adjustment. Promote to Phase-A only after
  script-class produces N=5 clean executions in Phase-B.

---

## Excluded from taxonomy

These are **capability-surface boundaries**, not work-classes.
They appear here so future deliverables don't "discover" them
as missing taxonomy entries:

- **Vault-touching work** — read or write secret/* paths
- **Credential-handling work** — render to disk, hash, rotate
- **SSH-cross-host work** — drive a session that lands on
  another host
- **docker-socket-touching work** — anything that mutates
  container state via the host docker socket

These are gated by capability-surface posture (see
`goose-capability-boundary.md`). A surface either has the
capability enabled or doesn't; class taxonomy doesn't override
that gating. A class that *appears* to be Phase-A by its
(read, write, decide) triple but requires Vault access to
execute is gated at the capability surface, regardless of class
tier.

The clean way to think about it: classes are about *what work
the model is doing*; capability surface is about *what tools
the model has available*. A Phase-A class can be unimplementable
on a given surface because that surface doesn't have the
capability; that's a surface-side gate, not a class-side
question.

---

## How to add a class

When a session reveals work that doesn't fit any existing class
in the taxonomy, the correct response depends on the gap:

1. **The work fits an existing class but the triple needs
   slight refinement.** Update the class's read/write/decide
   shape inline. Do not bump the tier without operator
   decision.
2. **The work is genuinely a new class.** Add it as Cn (next
   integer). Default initial tier is one tier *more* conservative
   than the closest existing class — error on the side of more
   review, not less. Tier upgrades require operator decision.
3. **The work straddles two existing classes.** Either split
   the existing classes (preferred — keeps taxonomy crisp) or
   acknowledge the straddle and route the session to the more
   conservative tier of the two. Don't invent a hybrid class
   without splitting; hybrids accumulate and the taxonomy stops
   being usable.

Class additions land in this chronicle with date + originating
WP, same revision pattern as the rest of `architecture-facts/`.

---

## Why this lives in `architecture-facts/`

Class taxonomy outlives D-17-53. Every downstream cell-promotion
deliverable will reference these classes, not the phase-17 file
tree. Phase docs reference *events*; architecture-facts reference
*durable posture*.

This chronicle is a foundational pointer for `promotion-
criteria.md`, `goose-session-pipeline.md`, and `migration-
telemetry.md` — they assume these classes exist and define
mechanisms within them.
