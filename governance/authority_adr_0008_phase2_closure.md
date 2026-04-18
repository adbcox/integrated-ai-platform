# ADR 0008 — Phase 2 Closure via Bounded Capability Evidence

Status: accepted (CAP-P2-CLOSE-1)
Owner: governance/phase2_closure_evidence.json
Baseline commits:
- RECON-W1: `53ae4d4f177b176a7bffaa63988f63fa0efa622c`
- RECON-W2A: `595dc8750ed671fb23d3cec0be434c76dad818f5`

## Context

ADR 0005 recorded Phase 2 as `adopted_partial` at the RECON-W1 baseline.
Closure was blocked on the absence of committed real-capability evidence
(a `measurement_session` or equivalent that demonstrates the bounded
inner loop converging on a real task). The tactical families were — and
remain — locked; ADR 0005 made clear that any later flip to `closed`
must be ratified by a reconciliation package that provides concrete
runtime evidence.

CAP-P2-CLOSE-1 consumes the narrow `ratification_only -> capability_session`
transition recorded in `governance/next_package_class.json` solely to
capture that missing evidence. It does not unlock any tactical family,
does not modify `framework/`, and does not alter the scope of Phase 2
contract extraction.

## Decision

1. Phase 2 is closed and ratified. `governance/phase2_adoption_decision.json`
   records `decision == "closed"`; `governance/current_phase.json` records
   `phase2_status == "closed_ratified"`; `governance/phase_gate_status.json`
   records the Phase 2 row as `closed_ratified`.
2. The closure rests entirely on bounded runtime evidence captured in
   `governance/phase2_closure_evidence.json`. That evidence was produced
   by the deterministic recorder
   `bin/governance_phase2_evidence_recorder.py`, which drives
   `framework.worker_runtime.WorkerRuntime._execute_inner_loop` against a
   tmp-path `victim.py` through two failing validate cycles and a
   successful third cycle, and separately through two non-converging
   cycles capped at `max_cycles = 2`. The capability tests that back the
   evidence are:
   - `tests/capability/test_phase2_innerloop_closure.py` (positive)
   - `tests/capability/test_phase2_innerloop_closure_negative.py` (negative)
3. **No tactical family is unlocked by this closure.** LOB-W3 remains
   paused under ADR 0003. `governance/tactical_unlock_criteria.json`
   is byte-identical to the RECON-W2A baseline and every family remains
   `locked`.
4. **`framework/` is not modified by this packet.** The evidence
   recorder and capability tests only invoke public/internal runtime
   APIs via dependency injection against a tmp-path workspace.
5. The narrow `ratification_only -> capability_session` transition in
   `governance/next_package_class.json` is marked consumed by this
   packet. The next allowed package class returns to
   `ratification_only`.

## Consequences

- `governance/phase2_adoption_decision.json` carries
  `closure_evidence_ref` and `closure_adr_ref` pointers to this ADR and
  to the evidence JSON. The file's `decision` field is the authoritative
  post-closure statement and supersedes the `adopted_partial` snapshot
  previously written by the Phase 2 extractor.
- The Phase 2 extractor (`bin/governance_phase2_extractor.py`) remains
  untouched under the packet's forbidden-scope invariant. If the
  extractor is re-run to regenerate inner-loop contract content, any
  resulting mutation of `phase2_adoption_decision.json` must be
  re-consolidated against this ADR before recommitting.
- No new tactical-family work is authorized. Any attempt to expand
  beyond the bounded capability scope of CAP-P2-CLOSE-1 requires a
  fresh ratification or tactical-review packet.

## Bounded scope

The capability evidence is narrow by design:
- no learning-loop closure
- no inference quality evaluation
- no manager / stage / RAG / tactical-family path
- no capability-generation claims
- no framework behavior changes

## Validation evidence

- positive capability test: passed (see
  `governance/phase2_closure_evidence.json#positive_test_outcome`)
- negative capability test: passed (see
  `governance/phase2_closure_evidence.json#negative_test_outcome`)
- observed inner_loop_cycle trace count: >= 2
  (see `governance/phase2_closure_evidence.json#observed_cycle_count`)
- final WorkerOutcome.status: `completed`
  (see `governance/phase2_closure_evidence.json#final_worker_outcome_status`)

## Supersedes

- The `adopted_partial` snapshot of `phase2_adoption_decision.json` that
  ADR 0005 last ratified. ADR 0005 remains the canonical account of the
  RECON-W2 decision; this ADR is the narrow closure layered on top.
