# Runbook: Operating model

**Audience:** the operator (and any future planning/execution Claude
session) approaching a Phase 13+ block of work.
**Authoritative ADRs:** [A-011](../adr/ADR-A-011-ivv-loop-pattern.md),
[A-012](../adr/ADR-A-012-equivalence-harness-doctrine.md),
[A-013](../adr/ADR-A-013-folded-gates-doctrine.md).

This runbook is the practical companion to the three operating-model
ADRs. The ADRs say *what* the doctrine is and *why*; this document
says *how* to apply it in a typical execution window.

---

## 1. Choosing a gate type for a sub-stage

Every block decomposes into sub-stages. Each sub-stage chooses one of
two gate types:

- **Full IV&V** — audit, execution, validation, regression as four
  separable phases with explicit stop-and-surface conditions between
  them.
- **Folded** — a single consolidated step where audit is implicit,
  validation is a re-read of the changed surface, and regression is
  deferred to the end of a chain of folds.

Pick **Full IV&V** when:
- The sub-stage touches a new external surface (new API, new
  schema, new authoritative store).
- The sub-stage is the first application of a pattern in this
  session (the pattern hasn't been load-bearing yet).
- The sub-stage's failure mode is silent (HTTP 200 with no
  mutation, healthcheck flap masked by `restart: unless-stopped`,
  data migration with lossy collapse). Discoveries #14, #15, #16
  in Block 4.C are all silent-failure surfaces; full IV&V is the
  default for any future surface of that shape.
- The sub-stage's blast radius is large (writes against
  authoritative state, e.g., NetBox dcim, Plane issues, Vault
  paths).

Pick **Folded** when **all four** ADR-A-013 conditions hold: pattern
proven in this session, structurally identical application, no
novel surface, stop-and-surface conditions still enforced.

Mark every gate decision in the block plan explicitly. The reviewer
should be able to read the plan and see "Full IV&V" or "Folded
(per A-013, the C5.2a precedent)" against each sub-stage without
having to re-derive it from context.

### A worked decision

> Sub-stage: provision the eighth NetBox custom field needed for
> 4.D's InvenTree cross-reference.
>
> *Folded?* The NetBox custom-field provisioning pattern was
> proven load-bearing in 4.C C5.2a. Subsequent applications in
> C5.2b/c folded cleanly. The eighth field is structurally
> identical (same script, same idempotent provisioning, same
> re-read validation). **Folded.** A surprise during execution
> (e.g., unexpected schema collision with an existing field)
> rescinds the fold and triggers full IV&V for that step.

---

## 2. The audit phase

The audit is read-only investigation that produces a findings
document. It is the load-bearing input to execution planning.

### What an audit produces

A structured findings document at
`docs/phase-13/<block>/<sub>_AUDIT_<date>.md` (or for cross-block
audits, `docs/phase-13/INCREMENT_<N>_<sub>_AUDIT_<date>.md`)
containing:

1. **Surface inventory.** What was read, what was found.
2. **Findings by item.** One entry per discovered issue; each
   names the exact location (file:line, schema field, API
   endpoint), describes the issue, and proposes a remediation.
3. **Risks the audit cannot resolve.** The audit names what it
   doesn't know — what would require execution to discover, what
   would require operator decision.
4. **Scope ratification ask.** If the findings reveal scope
   beyond the brief, the audit *stops* and surfaces that scope to
   the operator before execution begins. The audit document
   itself is the gate.

### Read-only audits parallelise

Multiple audits against unrelated files can run in parallel. In
practice this means: when D-CN audits six connector consumers,
the audit phase reads all six in parallel (parallel tool calls in
a single execution turn), not sequentially. The findings document
is one document covering all six; the work to populate it is
parallelised.

Stateful inspection (querying NetBox, polling Vault status, etc.)
parallelises only if the inspection itself doesn't compete for
rate budget. Plane V1's 60/min budget means audit-time inventory
GETs against Plane must sequence with any other Plane consumer,
not parallelise across consumers.

### When to skip the audit

The audit is skipped only under a folded gate. Skipping the audit
in a full-IV&V gate is a doctrine violation. If the operator
believes a full-IV&V audit is unnecessary, the right move is to
declare the gate folded (per A-013) with explicit reasoning, not
to skip the audit silently.

---

## 3. The execution phase

Execution is the actual change. Follow these rules:

### One focused commit per addressable change

Pre-commit hooks (`detect-secrets`) must pass without
`--no-verify`. If a hook fails, fix the underlying issue rather
than bypass the check. The commit message conveys the *why*; the
diff conveys the *what*. Co-author tag on every commit per the
git workflow.

### Capture out-of-repo state changes

`~/control-center-stack/stacks/*` is not under git. Any compose
change there must be recorded with pre/post snapshots in the
rewire log (`docs/runbooks/rewire-log/`). This is doctrine
(CLAUDE.md "out-of-repo compose changes"); easy to forget under
time pressure.

### Stop on unexpected behaviour

Any divergence from expectation — a healthcheck that doesn't go
green when it should, a curl that returns an unexpected payload,
a script that exits 0 with no output — is a stop-and-surface.
**Do not retry blindly.** Diagnose first, then either fix the
root cause (preferred) or consciously work around (with the
workaround captured as a discovery).

The Discovery #16 trap (`HTTP 200 ≠ mutation succeeded`) is the
canonical example. Trust requires verification; verification
requires re-read.

---

## 4. The validation phase

Validation is verification the change did what it claimed.

### "Probably works" is not validation

Every claim is verified by command output or cited source. The
validation step's output is the load-bearing evidence; the
execution's success message is not.

Capture validation output in the closeout doc. Examples:

- "Re-read of the patched issue shows `labels: [<label-id>]`."
  → Insufficient. **Cite the actual `curl` output** including the
  full label payload.
- "Healthcheck reports healthy." → Insufficient. **Cite the
  `docker inspect` output** showing the healthcheck history.
- "Tests pass." → Insufficient. **Cite the test runner's output
  with PASS/FAIL counts and run timestamp.**

### Sample-verify after the first batch

For write-heavy operations (back-fills, migrations, bulk
imports), validate after the first batch of writes — not at the
end of the run. This is "first-batch verify" (Discovery #15
codified). Re-GET the first record after PATCH; assert the
mutation took; abort the run if it didn't.

If the validation reveals a divergence after N writes, you have N
records to investigate. If it reveals it after the whole run, you
have the full set. Same diagnosis cost; first-batch surfaces it
~10× sooner.

---

## 5. The regression phase

Regression is the broader check that the change did not break
neighbouring state.

### The canonical instrument

`docs/phase-13/h1-regression-probe.sh <gate-name>`. The script
emits PASS/FAIL/WARN counts. The closeout doc must show:

- Baseline counts (from the start of the increment).
- Final counts (from the regression run at increment close).
- Any new FAILs or WARNs explained.

### What to do with a new WARN

A new WARN in the regression output is **not** automatically a
blocker. It is a stop-and-surface: the operator examines the
WARN's source, decides whether it is expected (e.g., a new
service registered without a deep healthcheck yet) or
unexpected (e.g., a known-healthy service has flipped). Expected
WARNs are documented in the closeout; unexpected ones are
treated as failures of the increment.

### What to do with a new FAIL

A new FAIL is a blocker. The increment cannot close until the
FAIL is resolved or until the operator explicitly accepts the
FAIL with a documented rationale (rare; reserved for cases where
the FAIL is in a side-channel that the increment did not touch
and was already failing in the baseline but newly named by a
probe change).

---

## 6. Designing the execution prompt

Execution prompts (the input to a Claude Code window driving an
increment) should:

### Bound the work to one execution window

The plan's increment proposal sizes each increment to fit in one
~12–18 h window (allowing for compaction overhead and re-context).
The execution prompt restates the scope and the explicit stop
point. **Do not begin Increment N+1 in Increment N's window.**

### Encode the gate structure

Tell the executing session which sub-stages are full IV&V and
which are folded. Cite the ADR that makes the fold legitimate.
The session should not re-derive the gate decisions from context.

### Encode the parallelism plan

Spell out which sub-stages parallelise (read-only audits) and
which serialise (stateful deploys, rate-limited APIs). The
session should not re-derive the parallelism from work shape.

### Encode the stop-and-surface conditions

Name the specific conditions that warrant stop-and-surface.
"Stop if the audit finds unexpected scope" is more useful than
"stop if anything seems off" because the former gives the session
a concrete trigger to test against.

### Confirm pre-flight

Every execution prompt opens with a pre-flight: HEAD at expected
commit, working tree clean, baseline regression run. Only then
does it advance to phase A.

---

## 7. Capturing discoveries

Anything surprising during the increment is a discovery. Capture
in the increment's closeout doc (or in a per-block discoveries
doc when the volume warrants it, as in Block 4.C C2 with 17
discoveries).

### What counts as a discovery

- A pattern that didn't behave as the plan assumed (e.g., the
  Plane V1 cursor-based pagination terminating on
  `next_page_results` rather than `next_cursor`).
- A silent failure mode (HTTP 200 with no mutation;
  healthcheck flapping under PID-1 env that isn't inherited).
- An upstream image's behaviour that contradicts assumed
  conventions (housekeeping script path drift in netbox-docker
  4.0.2).
- A doctrine implication (memory files with plaintext
  credentials are a load-bearing surface; "deliberate" lossy
  migrations defer regressions to the deprecation gate).

### How to record it

- Number the discovery (continuing from the last numbered one in
  the increment's predecessor).
- Title it concisely (one line).
- Capture: what surfaced it, severity, root cause, resolution,
  and the C6 follow-up (if any) it generates.
- Cross-reference any commits that landed the resolution.

The discovery doc is the load-bearing record. The closeout's
discovery section can be a one-line index pointing at the
discovery doc; the discovery doc itself carries the depth.

---

## 8. Handing off between windows

### Planning → execution

The planning window produces an execution-ready prompt
(per §6) and a closeout-doc target. Operator ratification of
the plan's scope and the increment's blocking questions is the
gate before execution opens.

### Execution → audit / review

The executing window produces:
- The closeout doc with phase-by-phase deliverables, commit
  hashes, validation evidence, regression baseline-vs-final.
- All discoveries surfaced during the increment, numbered and
  captured.
- The C6 follow-up list (items deferred to subsequent blocks).

A separate audit window (or an audit pass at the start of the
next execution window) consumes the closeout doc to verify the
increment's claims hold under independent re-read.

### Window-to-window context

Every increment closeout is named with the date. The handoff
guide (`docs/HANDOFF_GUIDE.md`) lists the canonical sequence
for picking up where the prior window left off:
1. `git log --oneline -20` to read recent commits.
2. Read the most-recent closeout doc for the prior increment.
3. Read the closeout campaign plan for the next increment.
4. Confirm pre-flight readiness for the next increment.

### Memory writes

Sticky context that survives across windows belongs in
`~/.claude/projects/.../memory/` (per CLAUDE.md). The closeout
doc is canonical; memory writes index the closeout, never
duplicate it.

---

## 9. Common pitfalls (and how doctrine avoids them)

| Pitfall | Doctrine that catches it |
|---|---|
| `HTTP 200 ≠ mutation succeeded` | A-011 validation phase + Discovery #15 first-batch verify pattern |
| Lossy migration silently deferred to deprecation | A-012 equivalence harness at migration time |
| Mechanical step audited unnecessarily | A-013 folded gates |
| Mechanical step folded incorrectly | A-013 fold-rescind on unexpected re-read |
| Audit done sequentially when parallel is safe | A-011 §parallelism by work shape |
| Discovery captured in chat, not in doc | §7 above (record in discoveries doc) |
| Increment N+1 begun in Increment N's window | §6 (execution prompt encodes stop point) |
| Pre-flight skipped, baseline never captured | §6 (pre-flight is mandatory opener) |

---

## 10. When this runbook is wrong

This runbook codifies what worked in Block 4.C and Increment 1.
It is not exhaustive. Future increments will surface patterns this
runbook does not yet describe. When they do:

1. Capture the pattern in the closeout discoveries.
2. If the pattern recurs, lift it into a new ADR and update
   the runbook with a §11+ entry.
3. If the pattern contradicts an existing ADR, supersede the
   ADR rather than amending the runbook to match the new
   pattern silently.

Doctrine evolves through ADRs. The runbook is the navigation
layer; the ADRs are the load-bearing decisions.
