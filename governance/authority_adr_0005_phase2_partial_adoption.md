# ADR 0005 — Phase 2 Partial Adoption

Status: accepted (RECON-W2)
Owner: governance/phase2_adoption_decision.json
Baseline commit: 53ae4d4f177b176a7bffaa63988f63fa0efa622c

## Context

Phase 2 is the inner-loop autonomous-repair and shared-runtime-adoption phase.
`framework/worker_runtime.py` implements the bounded inner loop, emits
`tool_permission_decision` and `tool_observation` trace kinds, and drives
snapshot/restore on repair failure or cycle exhaustion. These behaviors are
statically visible and extracted into
`governance/inner_loop_contract.json`.

However, tactical families committed to the repository
(`live_bridge_*`, `multi_phase_*`, `ort_*`, `pgs_*`) do not statically import
any of the runtime primitives that define the contract. Adoption coverage for
those surfaces is zero at baseline commit.

Real-capability evidence (a committed `measurement_session` or equivalent that
demonstrates the inner loop closing bounded real tasks) is also not present
in-tree.

## Decision

1. Phase 2 is recorded as `adopted_partial` at baseline commit
   `53ae4d4f177b176a7bffaa63988f63fa0efa622c`.
2. **Phase 2 is explicitly NOT closed by this ADR.** Any claim that Phase 2
   has advanced beyond `adopted_partial` must be ratified by a later
   reconciliation package that provides:
   - runtime-primitive adoption coverage for at least one tactical family
   - committed real-capability measurement evidence
3. The machine-readable contract in
   `governance/inner_loop_contract.json` is authoritative for the inner-loop
   semantics at baseline commit. Any future change to the worker runtime must
   regenerate that file.

## Consequences

- `governance/phase_gate_status.json` records Phase 2 as `adopted_partial`.
- `governance/current_phase.json` records current phase as Phase 2 with
  status `adopted_partial` and `next_allowed_package_class` remains
  `ratification_only`.
- No tactical family may be unlocked on the basis of this ADR.

## Supersedes

- The `partially_adopted_open_governance` status previously assigned to
  Phase 2 in RECON-W1.
