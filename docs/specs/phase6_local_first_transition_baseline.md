# Phase 6 Local-First Transition Baseline Specification

**Spec ID**: PHASE6-LOCAL-FIRST-TRANSITION-BASELINE-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 6 (local_first_routine)  
**Authority sources**: governance/phase5_closeout_baseline.v1.yaml, governance/phase5_readiness_baseline.v1.yaml, governance/local_run_validation_pack.v1.yaml, governance/definition_of_done.v1.yaml

---

## Purpose

This document specifies the Phase 6 local-first transition baseline — the surfaces required to establish Aider/Ollama as the routine execution path, remove Claude Code from the routine implementation path, and enforce explicit escalation accounting.

The machine-readable form is `governance/phase6_local_first_transition_baseline.v1.yaml`. This document is the human-readable companion.

---

## Phase Identity

- **Phase ID**: `phase_6`
- **Label**: Phase 6 — Local-First Routine
- **Status**: `transition_in_progress`

---

## Required Modules

| Module | Classes |
|--------|---------|
| `framework/local_execution_ledger_v1.py` | `LocalExecutionLedgerV1`, `LedgerEntryV1` |
| `framework/aider_execution_adapter_v1.py` | `AiderExecutionAdapterV1`, `AiderHandoffRecordV1` |
| `framework/local_autonomy_evidence_bridge_v1.py` | `LocalAutonomyEvidenceBridgeV1`, `LocalAutonomyEvidenceSummaryV1` |
| `framework/escalation_record_v1.py` | `EscalationRecordV1`, `EscalationRegistryV1` |
| `framework/phase6_transition_v1.py` | `Phase6TransitionV1`, `Phase6TransitionResultV1` |

---

## Required Capabilities

| Capability | Module | Description |
|-----------|--------|-------------|
| `local_execution_ledger` | `local_execution_ledger_v1` | Record and serialize local execution runs with executor, route, validation results, and escalation status |
| `aider_local_first_handoff` | `aider_execution_adapter_v1` | Structure local-first Aider handoffs with allowed_files, validation_sequence, and execution_mode = local_first |
| `autonomy_evidence_bridge` | `local_autonomy_evidence_bridge_v1` | Derive routine_local_execution_ready, explicit_escalation_required, and claude_removed_from_routine_path_signal from execution surfaces |
| `explicit_escalation_accounting` | `escalation_record_v1` | Record escalations and enforce that Claude/remote executor runs never count as local autonomy progress |
| `local_first_transition_result` | `phase6_transition_v1` | Assemble all four surfaces into a Phase6TransitionResultV1 with transition_ready boolean |

---

## Local Execution Ledger

`LocalExecutionLedgerV1` records `LedgerEntryV1` entries with:
- `run_id`, `package_id`, `package_label`, `executor`, `route`
- `validations_run`, `validation_results`, `artifacts_produced`
- `escalation_status`, `final_outcome`, `recorded_at`

`to_dict()` returns total_runs, passed_runs, pass_rate, and all entries.

---

## Aider Execution Adapter

`AiderExecutionAdapterV1.build_handoff()` returns `AiderHandoffRecordV1` with:
- `package_id`, `allowed_files`, `validation_sequence`
- `adapter_status` — `ready` if allowed_files non-empty, else `blocked`
- `execution_mode` = `local_first`
- `task_class`, `difficulty` (optional)

`is_ready()` checks `adapter_status == "ready"` and `execution_mode == "local_first"`.

---

## Local Autonomy Evidence Bridge

`LocalAutonomyEvidenceBridgeV1.derive()` returns `LocalAutonomyEvidenceSummaryV1` with:
- `routine_local_execution_ready` — True when: local runs present, local pass_rate ≥ 0.75, qualification ready, artifact passing
- `explicit_escalation_required` — always True in Phase 6 governance
- `claude_removed_from_routine_path_signal` — True when no Claude-executor runs in ledger
- `evidence_gaps` — list of blocking evidence gaps

---

## Escalation Record

`EscalationRecordV1` captures:
- `run_id`, `package_id`, `executor`
- `escalation_requested`, `escalation_approved`, `escalation_reason`
- `counts_as_local_autonomy_progress` — **invariant: always False when executor is Claude/remote**

The invariant is enforced at construction time in `__post_init__`. Claude rescue is structurally excluded from local autonomy progress accounting.

`EscalationRegistryV1.record()` auto-sets `counts_as_local_autonomy_progress` based on executor name.

---

## Phase 6 Transition Result

`Phase6TransitionV1.assemble()` combines:
1. `LocalExecutionLedgerV1` — ledger of all runs
2. `AiderHandoffRecordV1` — structured local-first handoff
3. `LocalAutonomyEvidenceSummaryV1` — derived evidence
4. `EscalationRegistryV1` — escalation accounting

Emits `Phase6TransitionResultV1` with `transition_ready = True` only when both `autonomy_evidence.routine_local_execution_ready` and `aider_handoff.adapter_status == "ready"`.

---

## Completion Requirements

| Requirement | Evidence |
|------------|---------|
| `routine_local_execution_ready` | routine_local_execution_ready = true in transition artifact |
| `explicit_escalation_required_for_claude` | explicit_escalation_required = true in autonomy evidence |
| `claude_not_counted_as_local_autonomy_progress` | EscalationRecordV1 invariant enforced structurally |
| `transition_artifact_emitted` | artifacts/substrate/phase6_transition_pack_check.json present, all_checks_passed = true |

---

## Remaining Blockers

### P6-BLOCKER-01 (deferred to Phase 7)
LocalExecutionLedgerV1 is in-memory only; no cross-session durable persistence.

### P6-BLOCKER-02 (deferred to Phase 7)
AiderExecutionAdapterV1 structures handoffs only; no live Aider subprocess dispatch.

### P6-BLOCKER-03 (deferred to Phase 7)
LocalAutonomyEvidenceBridgeV1 uses synthetic ledger entries; not wired to real Aider/Ollama telemetry.

### P6-BLOCKER-04 (deferred to Phase 7)
EscalationRegistryV1 records synthetic escalation events; not wired to real approval workflow.

---

## Transition Gate

Phase 6 transition is complete and Phase 7 entry is authorized when **all** of the following are true:

1. `routine_local_execution_ready = true` in transition artifact
2. `claude_removed_from_routine_path_signal = true` in autonomy evidence
3. `explicit_escalation_required = true` in autonomy evidence
4. `local_execution_cases_run ≥ 3` in transition artifact
5. `escalation_accounting_checked = true` in transition artifact
6. `all_checks_passed = true` in transition artifact
7. `make check` passes
8. Phase 6 seam tests pass

**Gate status**: `pending` — not yet cleared.

---

## Relationship to Governance

| Baseline element | Authority |
|-----------------|-----------|
| Local-first readiness signals | governance/phase5_closeout_baseline.v1.yaml |
| Escalation accounting | governance/definition_of_done.v1.yaml |
| Local run validation | governance/local_run_validation_pack.v1.yaml |
| Promotion gate | governance/phase_gate_status.json |
