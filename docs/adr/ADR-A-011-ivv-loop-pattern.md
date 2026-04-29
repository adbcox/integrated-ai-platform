# ADR-A-011 — IV&V loop pattern (audit → execution → validation → regression)

**Status:** Accepted
**Date:** 2026-04-29
**Source:** Block 4.C closeout, Phase 13 Increment 1 D-OP

## Context

Phase 13 Block 4.C (NetBox CMDB authority) ran for ~12 hours and surfaced
17 discoveries. The block's effectiveness — landing in the planned window
with zero post-close FAILs and a clean byte-identical equivalence proof —
came primarily from the gate structure used at every sub-stage, not from
any single technical artifact.

That gate structure is an Independent Verification & Validation (IV&V)
loop: every sub-stage of work decomposes into four phases — **audit,
execution, validation, regression** — with explicit stop-and-surface
conditions between phases. The pattern was applied inconsistently in
Blocks 4.A and 4.B (audits sometimes skipped, regression sometimes
implicit) and the resulting tail of "fix-it-after" rework was visible.
4.C applied it uniformly and the rework tail collapsed.

The pattern is general (applies to any non-trivial change to platform
state) but its application varies by work shape. Without doctrine, every
operator session re-derives "should I audit first?" and "is this big
enough to need a regression?" — wasting time and producing inconsistent
gate quality.

## Decision

Adopt the IV&V loop as the default work pattern for any platform change
that touches state (deployments, schema changes, data migrations,
connector consumers, doctrine artifacts).

### The four phases

1. **Audit** — read-only investigation of current state. Produces a
   findings document. Names the surface, identifies known-unknowns,
   surfaces risks. The audit's output is the input to execution
   planning.
2. **Execution** — the actual change. Each focused commit lands one
   addressable change. Pre-commit hooks (`detect-secrets`, etc.) must
   pass without `--no-verify`.
3. **Validation** — verification the change did what it claimed.
   Requires command output or cited source — "probably works" is
   insufficient. The validation step's output is what proves
   correctness, not the execution's success message.
4. **Regression** — broader check that the change did not break
   neighbouring state. The platform's regression probe
   (`docs/phase-13/h1-regression-probe.sh`) is the canonical
   instrument; PASS counts must not regress.

### When to apply the full loop vs fold

The loop is the default. **Fold** to a single consolidated step when
the work is mechanical application of a pattern that has already been
proven load-bearing in this session. Specifically:

- The pattern was applied with full IV&V at least once in this session.
- The new application is structurally identical (same tool, same shape,
  same risks) — only inputs differ.
- No novel surface is being touched.

Folded gates preserve **stop-and-surface conditions**: if the mechanical
application produces an unexpected result (test failure, schema
mismatch, non-zero diff), revert to full IV&V for that step.

Worked example from 4.C:
- C5.2a (first NetBox custom-field provisioning): full IV&V.
  Audit identified the schema gap, execution provisioned the field,
  validation re-read NetBox to confirm the field was present and
  correctly typed, regression confirmed no other consumer broke.
- C5.2b and C5.2c (additional fields, same provisioning script,
  different inputs): folded. Each was a single execution step with a
  combined validation+regression at the end. Total time saved: ~30
  minutes; risk added: zero (the provisioning script's correctness
  was already proven in C5.2a).

### Parallelism by work shape

The loop's phases parallelise differently depending on what's being
changed. This is doctrine because mis-applying parallelism (e.g.,
running stateful deploys in parallel) is a common failure mode.

- **Read-only audits parallelise aggressively.** Multiple consumers
  can be read simultaneously; the audit is a side-effect-free
  function of repo state. Sub-phase B.1 of Increment 1 (auditing six
  Plane connector consumers) is the canonical example: six file
  reads can run concurrently, producing a single findings document.
- **Stateful deployments serialise.** Bringing up a new compose
  stack against a shared host has compounding failure modes
  (port conflicts, volume collisions, healthcheck flap during
  startup). Block 4.C's C2 sub-stage serialised every container
  startup. Recovery debugging is also dramatically easier when
  only one thing is starting at a time.
- **Rate-limited APIs sequence to avoid contention.** Plane V1's
  60/min per-token budget means two consumers running concurrently
  exhaust the budget in 30 seconds (Discovery #15 documented this
  exactly). The connector test suite must have explicit windows
  during which no other consumer (cron, MCP server, dashboard
  refresh) runs.

### Stop-and-surface conditions

The loop is interruptible at every phase boundary. Specific triggers
for stop-and-surface:

- **Audit surfaces unexpected scope** — the change is bigger than
  the brief. Stop, surface scope, await operator decision.
- **Execution hits unexpected error** — a healthcheck flaps, a
  command returns an unexpected exit code, an idempotent operation
  is suddenly non-idempotent. Stop, do not retry blindly.
- **Validation diverges from expectation** — the change appears to
  have happened (200 OK, exit 0) but the expected state is not
  observable. Discovery #16 is the canonical example of this trap.
- **Regression introduces a new FAIL or WARN** — even if the new
  warning is "harmless," it is unexpected; surface it.

## Consequences

- Every Phase 13 block from 4.D onward applies the IV&V loop by
  default.
- Folded gates are explicitly noted in the gate-structure table of
  each block's plan (see Block 4.C plan §5 for the exemplar).
- Audit findings live in `docs/phase-13/<block>/<sub>_AUDIT_*.md`.
  The audit document is the load-bearing artifact for the gate
  decision; an audit-less execution is a doctrine violation.
- Validation output is captured in the closeout doc, not just
  surfaced in the operator transcript. "Verified that X" without
  cited command output is insufficient.
- Regression baseline is captured at the **start** of the increment
  (PASS/FAIL/WARN counts) and compared at close. Any new FAIL is a
  blocker; any new WARN must be either pre-existing-but-newly-named
  or explained.

This ADR codifies a pattern; it does not introduce a new tool or
runtime requirement. The cost is process discipline; the benefit is
predictability in increments where the platform's blast radius is
high (every Phase 13.4.x block touches authoritative state).
