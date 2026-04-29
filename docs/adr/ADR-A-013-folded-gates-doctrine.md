# ADR-A-013 — Folded gates for mechanical applications of proven patterns

**Status:** Accepted
**Date:** 2026-04-29
**Source:** Block 4.C C5.2a–c, Phase 13 Increment 1 D-OP

## Context

ADR-A-011 establishes the IV&V loop (audit → execution → validation
→ regression) as the default work pattern. Applied uniformly, the
loop is expensive: every sub-stage incurs the full four-phase
sequence including the regression run. For sub-stages that are
mechanical applications of an already-proven pattern, the cost
exceeds the value.

Block 4.C's C5.2 sub-stage demonstrated this concretely:

- **C5.2a** (first NetBox custom-field provisioning,
  `health_expect_extra`): full IV&V. Audit confirmed the schema
  gap, execution provisioned the field, validation re-read
  NetBox to confirm field presence and type, regression
  confirmed no consumer broke. ~30 minutes.
- **C5.2b** (second field, `port_is_internal`): the provisioning
  script was now load-bearing. The pattern was identical:
  `scripts/netbox-custom-fields.py` provisions one field
  idempotently. The audit phase added no information (we already
  knew the script worked), the validation step was a one-line
  `curl /api/extras/custom-fields/?name=...` re-read, and the
  regression was the same probe sequence. Folding C5.2b into a
  single execution+validation step (no separate audit, regression
  combined with C5.2c at the end) saved ~20 minutes with no
  loss of correctness.
- **C5.2c** (third field, similar shape): same fold. Combined
  regression after C5.2c covered both b and c.

Without doctrine, every operator session re-decides "is this
mechanical enough to fold?" — answers vary, and the wrong answer
in either direction is expensive (over-fold and a real bug
escapes; under-fold and the increment runs long).

## Decision

A gate may be **folded** to a single consolidated review when **all**
of the following hold:

1. **The pattern has been load-bearing in this session.** "This
   session" means the same execution increment, not historical
   precedent. A pattern proven six months ago in a different block
   does not unlock folding today; a pattern proven 30 minutes ago
   in the current block does.
2. **The application is structurally identical** to the proven
   one. Same tool, same shape of inputs, same shape of outputs.
   Differences are limited to the input data, not the workflow
   or invocation.
3. **No novel surface is touched.** A mechanical re-application
   of the canonical pattern, against an already-known target,
   with already-known authentication and rate budgets.
4. **Stop-and-surface conditions remain enforced.** A folded
   gate does not relax the conditions under which work pauses.
   The fold reduces process overhead, not correctness checks.

When all four hold, the audit phase may be skipped, the validation
phase may collapse to a re-read of the changed surface (no full
regression probe), and the regression may be deferred to the end of
the chain of folded steps.

When **any** of the four fail to hold, the gate reverts to full
IV&V for that step. Folding is a discipline, not a default.

### Stop-and-surface within a folded chain

If a folded step produces an unexpected result — a mutation that
re-reads as not having taken effect, an exit code that doesn't
match the proven step, output that includes a warning the proven
step didn't emit — the operator stops the fold immediately and
escalates **that** step (and only that step) back to full IV&V.

Specifically:

- The expected re-read confirms the change. **Unexpected re-read
  state is not a folded-gate exception** — it is a stop-and-surface
  that demands the same audit and regression treatment any novel
  step would receive. The mechanical pattern's correctness has not
  been proven for this input, so the fold is rescinded.
- If the stop-and-surface escalation reveals a pattern bug (the
  "proven" step was incorrect for some inputs), every prior
  folded application of the pattern in this session must be
  validated retrospectively. The fold's transitive trust is
  contingent on the foundation.

### Worked example from C5.2

C5.2a: full IV&V for the first custom-field provisioning.

C5.2b: folded. The provisioning command ran, the re-read
confirmed the field was provisioned, no audit, no separate
regression. Time saved: ~20 minutes.

C5.2c: folded. Same shape as b. Combined regression at the end
of c covered the b+c chain.

If C5.2c had failed (e.g., the field name had a typo, or the
custom-field type didn't match what the loader expected),
the operator would have stopped, audited the discrepancy as
if for a fresh sub-stage, and either fixed the input or
revealed a bug in the provisioning script that retroactively
required validating C5.2a and C5.2b.

In fact, both held — the provisioning script was correct, the
inputs were correct, the consumer's round-trip was clean. The
folded gates landed cleanly and the regression at end-of-c
(the byte-identical equivalence proof) was the load-bearing
validation for the whole sub-stage.

### Worked example from D-CN (Increment 1)

The audit phase of D-CN (sub-phase B.1) needed full IV&V even
though the audit's *targets* (six connector consumers) are
six instances of "read a Python file." The reason: the audit's
*output* (the findings document) is a load-bearing input to
the execution phase, and we have not previously audited these
six consumers against the connector's fixed contract. The
output is novel even though the activity per file is mechanical.

D-CN's execution phase, by contrast, is foldable per consumer:
once the first consumer's fix lands and is verified, subsequent
consumers' fixes following the same pattern (e.g., "wrap broad
`except Exception` with explicit `except RateLimitError`") fold
to a single execution+validation step per consumer with combined
regression at the end of the chain.

## Consequences

- Every block plan from Phase 13 onward must declare its gate
  structure explicitly, marking each sub-stage as "Full IV&V" or
  "Folded" with reasoning. Block 4.C plan §5 is the exemplar.
- Operators applying folded gates must surface the foldable
  pattern explicitly ("Following the C5.2a pattern, folding C5.2b
  to a single execution+validation step.") in the execution
  transcript so the closeout reviewer can verify the fold was
  legitimate.
- Closeout docs must list which gates were folded vs full. The
  closeout reviewer can then assess whether the folds were
  appropriate without re-deriving the gate decisions from
  context.
- A folded chain that escalates back to full IV&V mid-chain is
  not a doctrine violation — it is the doctrine working
  correctly. The fold's contingent trust was rescinded the
  moment the assumption broke.
- Doctrine work itself (D-OP) folds gates aggressively because
  the artifact is the gate (peer review of the ADR is the
  validation; no separate regression applies because the doctrine
  doesn't change runtime state). This ADR is one of three D-OP
  artifacts produced under a single folded gate.
