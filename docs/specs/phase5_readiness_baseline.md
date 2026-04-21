# Phase 5 Readiness Baseline Specification

**Spec ID**: PHASE5-READINESS-BASELINE-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 5 (live_local_model_integration)  
**Authority sources**: governance/phase4_uplift_baseline.v1.yaml, governance/local_run_validation_pack.v1.yaml, governance/definition_of_done.v1.yaml

---

## Purpose

This document specifies the Phase 5 readiness baseline — the criteria that must be satisfied before Phase 5 (live local model integration) may begin. Phase 5 is the first phase where real model execution (Ollama / Aider) performs real file modifications and patch generation.

The Phase 5 readiness gate is evaluated by `Phase5ReadinessEvaluatorV1` against evidence produced by the Phase 4 uplift surfaces. This document is the human-readable companion to `governance/phase5_readiness_baseline.v1.yaml`.

---

## Phase Identity

- **Phase ID**: `phase_5`
- **Label**: Phase 5 — Live Local Model Integration
- **Status**: `not_started`

---

## Readiness Dimensions

Five dimensions must all be met before Phase 5 entry is authorized:

| Dimension | Threshold | Evaluator Field | Blocking |
|-----------|-----------|----------------|---------|
| `artifact_completeness` | All required fields present | `artifact_complete` | Yes |
| `validation_pass_rate` | ≥ 0.75 | `validation_pass_rate` | Yes |
| `escalation_accounting` | Explicit status in all outputs | `escalation_status_present` | Yes |
| `first_pass_success` | ≥ 50% first-pass success rate | `first_pass_success_signal` | Yes |
| `retry_discipline` | All retries within declared budget | `retries_within_budget` | Yes |

---

## Evidence Requirements

### Required Artifacts

| Artifact | Required Fields | Minimum Values |
|---------|----------------|----------------|
| `artifacts/substrate/phase4_uplift_pack_check.json` | phase4_pack, all_checks_passed, uplift_cases_run, uplift_pass_rate, readiness_evaluated, readiness_ready, blocking_gaps | uplift_cases_run ≥ 4, uplift_pass_rate ≥ 0.75 |

### Required Baselines

- `governance/phase4_uplift_baseline.v1.yaml`
- `governance/phase3_mvp_baseline.v1.yaml`
- `governance/phase2_substrate_baseline.v1.yaml`

### Required Seam Tests

- `tests/test_phase4_uplift_pack_seam.py` (must pass)

---

## Blocking Conditions

The following conditions each independently block Phase 5 entry:

| ID | Condition | Resolution |
|----|-----------|-----------|
| BC-P5-01 | Phase 4 artifact does not exist or does not parse | Re-run uplift runner |
| BC-P5-02 | all_checks_passed is false | Fix failing gate; re-run |
| BC-P5-03 | uplift_pass_rate < 0.75 | Fix failing uplift cases |
| BC-P5-04 | readiness_ready is false with non-empty blocking_gaps | Address each gap |
| BC-P5-05 | escalation_status absent from any Phase 4 output | Add explicit status |
| BC-P5-06 | Phase 4 seam tests fail | Fix test failures |

---

## Promotion Readiness Gate

Phase 5 entry is authorized when **all** of the following are true:

1. All five readiness dimensions are met (`Phase5ReadinessEvaluatorV1.ready = true`)
2. No blocking conditions are active
3. All required evidence artifacts are present and valid
4. `make check` passes
5. Seam tests for Phase 4 pass

**Gate status**: `pending` — not yet cleared. Gate is evaluated at Phase 5 candidate submission time against this baseline.

---

## What Phase 5 Enables

Once the readiness gate is cleared, Phase 5 may:

1. Wire `RoutingDecisionV1` from `RoutingPolicyUpliftV1` into the real `inference_adapter.py` dispatch path
2. Replace synthetic validation steps in `DeveloperAssistantLoopV1` with real patch/apply/commit steps using Aider or Ollama
3. Feed live failure records into `FailureMemoryV1` for persistent cross-session learning
4. Run the benchmark against real file modifications and score actual diffs
5. Activate `CritiqueInjectionV1` data-driven mode using summarized failure memory

---

## Relationship to Governance

| Baseline element | Authority |
|-----------------|-----------|
| Readiness dimensions | governance/phase4_uplift_baseline.v1.yaml |
| Blocking conditions | governance/local_run_validation_pack.v1.yaml |
| Escalation accounting | governance/definition_of_done.v1.yaml |
| Promotion gate | governance/phase_gate_status.json |
