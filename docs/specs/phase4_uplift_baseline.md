# Phase 4 Self-Sufficiency Uplift Baseline Specification

**Spec ID**: PHASE4-UPLIFT-BASELINE-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 4 (self_sufficiency_uplift)  
**Authority sources**: governance/phase3_mvp_baseline.v1.yaml, governance/local_run_validation_pack.v1.yaml, governance/definition_of_done.v1.yaml

---

## Purpose

This document specifies the Phase 4 self-sufficiency uplift baseline — the set of surfaces that bridge the Phase 3 MVP (bounded inspect/validate loop) toward Phase 5 (live local model integration with real code modifications).

Phase 4 does not wire a live model backend. Instead, it proves that the prompt pack, failure memory, critique injection, routing policy, and readiness evaluation surfaces are present, callable, and emit structured evidence. The evidence these surfaces produce is the Phase 5 entry gate.

The machine-readable form is `governance/phase4_uplift_baseline.v1.yaml`. This document is the human-readable companion.

---

## Phase Identity

- **Phase ID**: `phase_4`
- **Label**: Phase 4 — Self-Sufficiency Uplift
- **Status**: `in_progress` (gate met by P4-01)
- **Scope**: New-file implementation only; no modifications to existing live runtime modules

---

## Required Modules

### Phase 4 (P4-01)

| Module | Classes |
|--------|---------|
| `framework/task_class_prompt_pack_v1.py` | `TaskClassPromptPackV1`, `PromptPackEntryV1` |
| `framework/failure_memory_v1.py` | `FailureMemoryV1`, `FailureRecordV1`, `FailureSummaryV1` |
| `framework/critique_injection_v1.py` | `CritiqueInjectionV1`, `CritiqueResultV1` |
| `framework/routing_policy_uplift_v1.py` | `RoutingPolicyUpliftV1`, `RoutingDecisionV1` |
| `framework/phase5_readiness_v1.py` | `Phase5ReadinessEvaluatorV1`, `Phase5ReadinessResultV1` |

### Phase 3 (inherited)

| Module | Classes |
|--------|---------|
| `framework/developer_assistant_loop_v1.py` | `DeveloperAssistantLoopV1` |
| `framework/mvp_benchmark_runner_v1.py` | `MVPBenchmarkRunnerV1` |

---

## Required Capabilities

| Capability | Module | Description |
|-----------|--------|-------------|
| `task_class_prompting` | `task_class_prompt_pack_v1.py` | Typed prompt guidance for bug_fix, narrow_feature, reporting_helper, test_addition |
| `failure_memory` | `failure_memory_v1.py` | Record and summarize failure records by task class and signature |
| `critique_guidance` | `critique_injection_v1.py` | Structured critique + retry guidance from prior failures (no model call) |
| `routing_uplift` | `routing_policy_uplift_v1.py` | Map task_class/difficulty to model profile and retry posture |
| `readiness_evaluation` | `phase5_readiness_v1.py` | Evaluate five dimensions and emit Phase5ReadinessResultV1 |

---

## Task Class Prompt Pack

`TaskClassPromptPackV1` provides prompt guidance for four default task classes:

| Task Class | Description |
|-----------|-------------|
| `bug_fix` | Minimal targeted correction; read trace first; do not refactor |
| `narrow_feature` | Add only the requested feature; leave interfaces unchanged |
| `reporting_helper` | Produce serializable structured output; no side effects |
| `test_addition` | Deterministic, offline-safe tests; no order dependencies |

Each entry carries `system_guidance`, `execution_guidance`, and `validation_guidance`.

---

## Failure Memory

`FailureMemoryV1` records `FailureRecordV1` entries with:
- `task_id`, `task_class`, `failure_signature`, `correction_hint`, `recorded_at`

`summarize()` returns `FailureSummaryV1` with:
- `total_failures`, `by_task_class`, `most_common_signatures`, `top_correction_hints`

No live persistence is required in Phase 4; memory is in-session only.

---

## Critique Injection

`CritiqueInjectionV1.inject()` accepts `task_class`, `prior_failures`, and `current_objective`, and returns `CritiqueResultV1` with:
- `critique_points` — task-class-specific review points + prior failure signatures
- `retry_guidance` — task-class-specific retry steps + correction hints from prior failures

No model call is required; guidance is rule-based and augmented by failure records.

---

## Routing Policy Uplift

`RoutingPolicyUpliftV1.decide()` maps `(task_class, difficulty)` to a `RoutingDecisionV1`:
- `selected_profile` — one of: `local_fast`, `local_hard`, `local_smart`, `remote_assist`
- `retry_budget` — maximum retry count for this routing decision
- `retry_posture` — `conservative` | `standard` | `aggressive`
- `rationale` — human-readable explanation of the routing choice

Profile names are the Phase 1 canonical identifiers from `model_profiles_contract.v1.yaml`.

---

## Phase 5 Readiness Evaluator

`Phase5ReadinessEvaluatorV1.evaluate()` checks five dimensions:

| Dimension | Threshold | Blocking |
|-----------|-----------|---------|
| `artifact_completeness` | all fields present | yes |
| `validation_pass_rate` | ≥ 0.75 | yes |
| `escalation_accounting` | explicit status present | yes |
| `first_pass_success_signal` | ≥ 50% first-pass success | yes |
| `retry_discipline_signal` | all within retry_budget | yes |

Returns `Phase5ReadinessResultV1` with `ready`, `blocking_gaps`, `evidence_summary`.

---

## Completion Requirements

| Requirement | Evidence |
|------------|---------|
| `uplift_cases_execute` | uplift_cases_run ≥ 4 in artifact |
| `readiness_signal_emitted` | readiness_evaluated = true in artifact |
| `artifact_complete_outputs` | All required fields present; artifact assertion passes |
| `explicit_escalation_accounting` | escalation_status in all outputs |

---

## Completion Gate

Phase 4 uplift is complete when:
1. All completion requirements are met
2. uplift_pass_rate ≥ 0.75 on default synthetic cases
3. Seam tests pass
4. `make check` passes

**Gate status**: Met by P4-01.

---

## Remaining Blockers

### P4-BLOCKER-01 (deferred to Phase 5)
FailureMemoryV1 has no live persistence backend; in-memory only.

### P4-BLOCKER-02 (deferred to Phase 5)
CritiqueInjectionV1 uses static rule tables; not data-driven from failure memory yet.

### P4-BLOCKER-03 (deferred to Phase 5)
RoutingPolicyUpliftV1 returns decisions only; not wired to inference_adapter dispatch.

---

## Relationship to Governance

| Baseline element | Authority |
|-----------------|-----------|
| Required modules | governance/phase3_mvp_baseline.v1.yaml (Phase 4 scope) |
| Completion requirements | governance/local_run_validation_pack.v1.yaml |
| Escalation accounting | governance/definition_of_done.v1.yaml |
| Readiness evaluation | governance/phase5_readiness_baseline.v1.yaml |
