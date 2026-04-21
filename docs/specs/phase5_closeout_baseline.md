# Phase 5 Closeout Baseline Specification

**Spec ID**: PHASE5-CLOSEOUT-BASELINE-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 5 (live_local_model_integration)  
**Authority sources**: governance/phase5_readiness_baseline.v1.yaml, governance/phase4_uplift_baseline.v1.yaml, governance/local_run_validation_pack.v1.yaml, governance/definition_of_done.v1.yaml

---

## Purpose

This document specifies the Phase 5 closeout baseline — the qualification, local autonomy gate, and regression evidence surfaces required to evaluate promotion readiness from Phase 5 toward Phase 6 (full live local model integration).

The machine-readable form is `governance/phase5_closeout_baseline.v1.yaml`. This document is the human-readable companion.

---

## Phase Identity

- **Phase ID**: `phase_5`
- **Label**: Phase 5 — Live Local Model Integration
- **Status**: `qualification_in_progress`

---

## Required Modules

| Module | Classes |
|--------|---------|
| `framework/unified_validation_artifact_v1.py` | `UnifiedValidationArtifactV1` |
| `framework/qualification_readiness_v1.py` | `QualificationReadinessEvaluatorV1`, `QualificationReadinessResultV1` |
| `framework/local_autonomy_gate_v1.py` | `LocalAutonomyGateEvaluatorV1`, `LocalAutonomyGateResultV1` |
| `framework/regression_summary_v1.py` | `RegressionSummaryV1`, `RegressionCaseV1` |
| `framework/phase5_closeout_v1.py` | `Phase5CloseoutV1`, `Phase5CloseoutRecordV1` |

---

## Required Capabilities

| Capability | Module | Description |
|-----------|--------|-------------|
| `unified_validation_artifact` | `unified_validation_artifact_v1` | Bundle validation evidence from a single package run into a serializable record |
| `qualification_readiness` | `qualification_readiness_v1` | Evaluate artifact completeness, pass rate, and escalation accounting; return readiness_ready |
| `local_autonomy_gate` | `local_autonomy_gate_v1` | Evaluate first-pass success, retry discipline, escalation rate, and artifact completeness signals |
| `regression_summary` | `regression_summary_v1` | Summarize regression case outcomes with pass rate and failure modes |
| `phase5_closeout_record` | `phase5_closeout_v1` | Assemble all four surfaces into a structured Phase 5 closeout record |

---

## Unified Validation Artifact

`UnifiedValidationArtifactV1` bundles:
- `package_id`, `package_label`, `generated_at`
- `validations_run` — list of validation step names
- `validation_results` — dict of step name → bool
- `artifacts_produced` — list of artifact paths produced
- `escalation_status` — explicit escalation status string
- `final_outcome` — `"PASS"` or `"FAIL"`
- `all_passed` (derived), `pass_rate` (derived)

---

## Qualification Readiness

`QualificationReadinessEvaluatorV1.evaluate()` checks:

| Dimension | Threshold | Blocking |
|-----------|-----------|---------|
| `artifact_completeness` | all fields present | yes |
| `validation_pass_rate` | ≥ 0.75 | yes |
| `escalation_accounting` | explicit status present | yes |

Returns `QualificationReadinessResultV1` with `readiness_ready` and `blocking_gaps`.

---

## Local Autonomy Gate

`LocalAutonomyGateEvaluatorV1.evaluate()` checks:

| Signal | Threshold | Blocking |
|--------|-----------|---------|
| `first_pass_success_signal` | ≥ 0.50 | yes |
| `retry_discipline_signal` | retries within budget | yes |
| `escalation_rate_signal` | ≤ 0.25 | yes |
| `artifact_completeness_signal` | required fields present | yes |

Returns `LocalAutonomyGateResultV1` with `gate_passed`, `gate_reasons`, `gate_blockers`.

---

## Regression Summary

`RegressionSummaryV1.from_cases()` accepts a list of `RegressionCaseV1` records and returns:
- `regression_cases_run`, `regression_cases_passed`, `pass_rate`
- `failure_modes` — list of failure mode strings from failed cases

---

## Phase 5 Closeout Record

`Phase5CloseoutV1.assemble()` combines:
1. `UnifiedValidationArtifactV1` from package run
2. `QualificationReadinessResultV1` from readiness evaluator
3. `LocalAutonomyGateResultV1` from autonomy gate
4. `RegressionSummaryV1` from regression cases

Emits `Phase5CloseoutRecordV1` with `promotion_readiness_ready = True` only when all three checks pass.

---

## Completion Requirements

| Requirement | Evidence |
|------------|---------|
| `qualification_cases_execute` | qualification_cases_run ≥ 3 in artifact |
| `regression_summary_emitted` | regression_summary present and regression_cases_run ≥ 3 |
| `promotion_readiness_evaluated` | promotion_readiness_ready present as boolean |
| `explicit_escalation_accounting` | escalation_status in all outputs |

---

## Remaining Blockers

### P5-BLOCKER-01 (deferred to Phase 6)
LocalAutonomyGateEvaluatorV1 evaluates signals only; not wired to live Ollama/Aider execution telemetry.

### P5-BLOCKER-02 (deferred to Phase 6)
RegressionSummaryV1 summarizes synthetic cases only; not wired to real file modification outcomes.

### P5-BLOCKER-03 (deferred to Phase 6)
Phase5CloseoutV1 does not persist closeout records to a durable store; in-session only.

---

## Promotion Readiness Gate

Phase 5 promotion to Phase 6 is authorized when **all** of the following are true:

1. `qualification_result.readiness_ready = true`
2. `autonomy_gate_result.gate_passed = true`
3. `unified_artifact.all_passed = true`
4. `regression_cases_run ≥ 3`
5. `escalation_status = NOT_ESCALATED` in all outputs
6. `make check` passes
7. Seam tests for Phase 5 pass

**Gate status**: `pending` — not yet cleared. Gate is evaluated at Phase 6 candidate submission time against this baseline.

---

## Relationship to Governance

| Baseline element | Authority |
|-----------------|-----------|
| Qualification readiness dimensions | governance/phase5_readiness_baseline.v1.yaml |
| Local autonomy gate signals | governance/local_run_validation_pack.v1.yaml |
| Escalation accounting | governance/definition_of_done.v1.yaml |
| Promotion gate | governance/phase_gate_status.json |
