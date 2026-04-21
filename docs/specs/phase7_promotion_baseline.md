# Phase 7 Promotion Baseline Specification

**Spec ID**: PHASE7-PROMOTION-BASELINE-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 7 (full_autonomy_and_promotion)  
**Authority sources**: governance/phase6_local_first_transition_baseline.v1.yaml, governance/phase5_closeout_baseline.v1.yaml, governance/local_run_validation_pack.v1.yaml, governance/definition_of_done.v1.yaml

---

## Purpose

This document specifies the Phase 7 promotion baseline — the surfaces required to ratify Phase 6 closeout and authorize Phase 7 full local-first autonomous operation. Phase 7 is complete when all Phase 6 blockers are addressed, the persistent execution ledger has real evidence, and the promotion decision surfaces emit structured results.

The machine-readable form is `governance/phase7_promotion_baseline.v1.yaml`. This document is the human-readable companion.

---

## Phase Identity

- **Phase ID**: `phase_7`
- **Label**: Phase 7 — Full Local Autonomy and Promotion
- **Status**: `promotion_in_progress`

---

## Required Modules

| Module | Classes |
|--------|---------|
| `framework/persistent_execution_ledger_v1.py` | `PersistentExecutionLedgerV1`, `PersistentLedgerEntryV1` |
| `framework/live_aider_dispatch_v1.py` | `LiveAiderDispatchV1`, `AiderDispatchRecordV1` |
| `framework/local_autonomy_telemetry_bridge_v1.py` | `LocalAutonomyTelemetryBridgeV1`, `TelemetryEvidenceSummaryV1` |
| `framework/escalation_workflow_v1.py` | `EscalationWorkflowV1`, `EscalationEventV1`, `EscalationDecisionV1` |
| `framework/phase6_closeout_ratifier_v1.py` | `Phase6CloseoutRatifierV1`, `Phase6CloseoutResultV1` |
| `framework/phase7_promotion_v1.py` | `Phase7PromotionV1`, `Phase7PromotionResultV1` |

---

## Required Capabilities

| Capability | Module | Description |
|-----------|--------|-------------|
| `persistent_local_execution_ledger` | `persistent_execution_ledger_v1` | JSONL-backed ledger persisting run records across sessions; append_record(), load_records(), summarize() |
| `live_aider_dispatch` | `live_aider_dispatch_v1` | Structured Aider dispatch with dry-run and live modes; returns AiderDispatchRecordV1 with dispatch_status |
| `real_autonomy_evidence_bridge` | `local_autonomy_telemetry_bridge_v1` | Derive 5 autonomy signals from persistent ledger + artifacts |
| `explicit_escalation_workflow` | `escalation_workflow_v1` | Record escalation events with approver_type; enforce Claude exclusion from autonomy progress |
| `phase6_closeout_ratification` | `phase6_closeout_ratifier_v1` | Ratify Phase 6 by checking all 4 P6 blockers; return phase6_closed + blockers_remaining |
| `phase7_promotion_decision` | `phase7_promotion_v1` | Evaluate Phase 7 promotion from closeout + telemetry + regression; return promotion_ready |

---

## Persistent Execution Ledger

`PersistentExecutionLedgerV1` persists to `artifacts/substrate/persistent_execution_ledger.jsonl`:
- `append_record(...)` — write entry to JSONL file
- `load_records()` — reload all entries from file
- `summarize()` — return total_runs, passed_runs, pass_rate, executor_counts

---

## Live Aider Dispatch

`LiveAiderDispatchV1.dispatch()` returns `AiderDispatchRecordV1`:
- `dispatch_status`: `dry_run` (default) | `live` | `completed` | `failed` | `blocked`
- `execution_mode` = `local_first` always
- Dry-run mode: structures command without subprocess; `exit_code = None`
- Live mode: invokes `aider --message <msg> <files>`; returns exit_code, stdout/stderr preview

---

## Local Autonomy Telemetry Bridge

`LocalAutonomyTelemetryBridgeV1.derive()` returns `TelemetryEvidenceSummaryV1` with 5 signals:

| Signal | Threshold | Description |
|--------|-----------|-------------|
| `first_pass_success_signal` | local pass_rate ≥ 0.50 | At least half of local runs pass without retry |
| `retry_discipline_signal` | retries within budget | All retries within declared budget |
| `escalation_rate_signal` | escalation_rate ≤ 0.25 | Escalation not overused |
| `artifact_completeness_signal` | artifact + qualification pass | Required artifact surfaces passing |
| `routine_local_execution_ready` | all signals + local pass ≥ 0.75 | Combined gate |

---

## Escalation Workflow

`EscalationWorkflowV1` manages `EscalationEventV1` records:
- `record_event(...)` — auto-sets `counts_as_local_autonomy_progress = False` for Claude/remote executors
- `evaluate(failure_count, retry_budget_remaining, task_complexity)` — returns `EscalationDecisionV1`
- Invariant enforced in `__post_init__`: Claude/remote cannot count as local progress

---

## Phase 6 Closeout Ratification

`Phase6CloseoutRatifierV1.ratify()` checks 4 Phase 6 blockers:
- **P6-BLOCKER-01**: persistent ledger has entries
- **P6-BLOCKER-03**: `routine_local_execution_ready = True` in telemetry
- P6-BLOCKER-02 and P6-BLOCKER-04: addressed by structural presence of dispatch/workflow surfaces

Returns `Phase6CloseoutResultV1` with `phase6_closed`, `blockers_remaining`, `closeout_summary`.

---

## Phase 7 Promotion

`Phase7PromotionV1.evaluate()` checks:
1. `phase6_closeout.phase6_closed = True`
2. `telemetry_evidence.routine_local_execution_ready = True`
3. `telemetry_evidence.first_pass_success_signal = True`
4. `telemetry_evidence.artifact_completeness_signal = True`
5. `regression_summary.pass_rate ≥ 0.75`

Returns `Phase7PromotionResultV1` with `promotion_ready`, `promotion_blockers`, `promotion_summary`.

---

## Completion Requirements

| Requirement | Evidence |
|------------|---------|
| `phase6_blockers_closed` | Phase6CloseoutRatifierV1 returns phase6_closed = true |
| `real_local_execution_evidence_present` | live_local_cases_run ≥ 3 in artifact |
| `explicit_escalation_accounting` | EscalationWorkflowV1 records events with approver_type |
| `promotion_decision_emitted` | Phase7PromotionV1 emits promotion_ready boolean |

---

## Remaining Blockers

### P7-BLOCKER-01 (deferred to live execution)
LiveAiderDispatchV1 in dry-run mode only; live dispatch requires installed Aider and real task.

### P7-BLOCKER-02 (deferred to live execution)
LocalAutonomyTelemetryBridgeV1 consumes synthetic ledger; real Aider/Ollama wiring pending.

### P7-BLOCKER-03 (deferred to live execution)
EscalationWorkflowV1 evaluator uses heuristic thresholds; not yet wired to live failure telemetry.

---

## Promotion Gate

Phase 7 promotion is authorized when **all** of the following are true:

1. `phase6_closed = true`
2. `promotion_ready = true`
3. `live_local_cases_run ≥ 3` in promotion artifact
4. `escalation_accounting_checked = true` in promotion artifact
5. `all_checks_passed = true` in promotion artifact
6. `make check` passes
7. Phase 7 seam tests pass

**Gate status**: `pending` — not yet cleared.

---

## Relationship to Governance

| Baseline element | Authority |
|-----------------|-----------|
| Phase 6 blockers | governance/phase6_local_first_transition_baseline.v1.yaml |
| Local autonomy signals | governance/phase5_closeout_baseline.v1.yaml |
| Escalation accounting | governance/definition_of_done.v1.yaml |
| Promotion gate | governance/phase_gate_status.json |
