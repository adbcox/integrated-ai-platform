# ADR 0004 — Phase 1 Closure

Status: accepted (RECON-W2)
Owner: governance/phase1_ratification_decision.json
Baseline commit: 53ae4d4f177b176a7bffaa63988f63fa0efa622c

## Context

Phase 1 (Runtime Contract Foundation) is materially implemented in code. The
runtime primitive set established in RECON-W1
(`governance/runtime_contract_version.json`) is:

- `framework/worker_runtime.py`
- `framework/job_schema.py`
- `framework/session_schema.py`
- `framework/tool_system.py`
- `framework/workspace.py`
- `framework/permission_engine.py`
- `framework/sandbox.py`

`framework/worker_runtime.py` directly imports `tool_system`,
`permission_engine`, `sandbox`, and `workspace` and exercises them through its
inner-loop execution. `bin/framework_control_plane.py` further exercises these
primitives as static adoption evidence.

RECON-W1 did not yet ratify the contract version as closed. RECON-W2 evaluates
whether the static evidence is sufficient for closure.

## Decision

1. Phase 1 is ratified closed at baseline commit
   `53ae4d4f177b176a7bffaa63988f63fa0efa622c`.
2. The ratified contract version is
   `governance/phase1_ratification_decision.json#ratified_contract_version`,
   computed deterministically from the runtime primitive set.
3. Closure requires static self-adoption completeness
   (`runtime_primitive_callgraph.json#self_adoption_complete == true`) and at
   least one external adoption consumer
   (`bin/framework_control_plane.py`).
4. Closure does not authorize any tactical family unlock. Tactical unlock is
   governed by ADR 0006.

## Consequences

- `governance/phase_gate_status.json` records Phase 1 as `closed_ratified`.
- Future changes to any runtime primitive advance the ratified contract
   version. A ratification regression must be reviewed by a later
   reconciliation package.
- Phase 2 remains open under ADR 0005.

## Supersedes

- The `materially_implemented_open_governance` status previously assigned to
  Phase 1 in RECON-W1.
