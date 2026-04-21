# Autonomy Scorecard Specification

**Spec ID**: AUTONOMY-SCORECARD-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation)  
**Authority sources**: ADR-0007, governance/definition_of_done.v1.yaml, governance/cmdb_lite_registry.v1.yaml, P0-01-AUTHORITY-SURFACE-INVENTORY-1

---

## Purpose

The **autonomy scorecard** provides a structured, machine-verifiable assessment of the integrated AI platform's ability to execute coding tasks autonomously — without human escalation, fallback, or external rescue. It governs phase progression decisions and is the primary instrument for detecting autonomy regressions.

The machine-readable form is `governance/autonomy_scorecard.v1.yaml`. This document is the human-readable companion.

---

## Why Autonomy Scoring Matters

The platform's primary goal is real capability gain toward the Codex 5.1 replacement milestone — not infrastructure or benchmarks. The autonomy scorecard measures whether that capability is real by capturing:

1. How often local execution succeeds on the first attempt
2. How often it needs retries
3. How often it needs human or control-window escalation
4. Whether it reliably produces valid artifacts
5. Whether it consistently passes its own validation

Without this measurement, it is impossible to tell whether improvements in one area are causing regressions in another, or whether "success" in benchmarks translates to actual autonomous operation.

---

## Required Metrics

### `first_pass_success`

**What it measures**: Fraction of tasks where the primary execution path produces a valid passing result on the first attempt, without fallback, retry, or escalation.

**Unit**: ratio 0.0–1.0  
**Phase 7 baseline**: 0.889 (18-task benchmark)  
**Target**: ≥ 0.85  
**Blocking**: < 0.50

This is the primary capability indicator. A high `first_pass_success` means the platform is reliably generating correct implementations without needing human guidance. The Phase 7 baseline of 88.9% was achieved on an 18-task real-file benchmark set.

### `retry_count`

**What it measures**: Average retries required per task before a passing result is achieved. Includes fallback model attempts; excludes escalations.

**Unit**: non-negative number (average per task)  
**Phase 7 baseline**: 0  
**Target**: ≤ 0 (all tasks succeed on first attempt)  
**Blocking**: > 3.0

A `retry_count` of 0 means every task succeeded on its first attempt. A high `retry_count` indicates that the primary model is consistently failing to generate correct implementations, and the platform is compensating through retries rather than capability.

### `escalation_rate`

**What it measures**: Fraction of package steps that required escalation to the control window or human review.

**Unit**: ratio 0.0–1.0  
**Phase 7 baseline**: 0.0  
**Target**: 0.0  
**Blocking**: > 0.25

Escalation represents a failure of local autonomy — the platform was unable to complete the task within its declared scope. A `escalation_rate` of 0.0 means no escalations occurred. The caution band (> 0.10) signals that scope or grounding issues are becoming systemic.

### `artifact_completeness`

**What it measures**: Fraction of required artifacts that were produced, present, parseable, and contain the correct `artifact_id`.

**Unit**: ratio 0.0–1.0  
**Phase 7 baseline**: 1.0  
**Target**: 1.0  
**Blocking**: < 0.90 (< 1.0 for governance sessions)

An artifact that exists but cannot be parsed is treated as absent. For governance sessions, `artifact_completeness` must be exactly 1.0 — anything below is an immediate failing score regardless of other metrics.

### `validation_pass_rate`

**What it measures**: Fraction of validation steps (make check, seam tests, runner scripts) that pass on the first execution without requiring a code fix and re-run.

**Unit**: ratio 0.0–1.0  
**Phase 7 baseline**: 0.90  
**Target**: ≥ 0.90  
**Blocking**: < 0.50

A low `validation_pass_rate` indicates that implementations are being committed that fail their own tests on first run — a sign that the generation quality is below the bar for production use.

### `promotion_readiness`

**What it measures**: Binary indicator of whether all phase progression preconditions are satisfied.

**Unit**: boolean  
**Phase 7 baseline**: true  
**Target**: true (at phase transition time)

`promotion_readiness` is not a continuous metric — it is evaluated at phase transition checkpoints. It is true only when every rule in `phase_progression_rules` for the target transition evaluates to satisfied.

---

## Thresholds

Each metric has three threshold bands:

| Band | Meaning | Action |
|------|---------|--------|
| **target** | Operating within design parameters | Proceed normally |
| **warning** | Degrading; action needed | Document in residual_notes; investigate |
| **blocking** | Systemic failure | Hard stop; escalate to control window |

See `governance/autonomy_scorecard.v1.yaml::thresholds` for exact values per metric.

---

## Interpretations

### Good (Grade A)

All metrics at or above target. Phase progression unblocked. Record scorecard in session artifact bundle and proceed.

### Caution (Grade B/C)

One or more metrics in the warning band but none in the blocking band. Continued operation is permitted but the degraded metric must be documented and investigated before the next capability session.

### Failing (Grade D/F)

One or more metrics at or below the blocking threshold. Hard stop. Do not attempt further capability sessions until the failing metric is resolved. Escalate to control window.

### Regression Detected (Grade F)

Any metric is worse than the Phase 7 baseline by more than the warning band. This is treated as a regression regardless of absolute values. Hard stop; regression must be resolved before any further execution.

---

## Phase Progression Rules

### `phase_1_complete`

Phase 1 (runtime_contract_foundation) may close when:
- `runtime_contract_version.json` is ratified by a governance ADR
- `framework/job_schema.py` conforms to ADR-0001
- `framework/permission_engine.py` satisfies ADR-0005 Layers 1–3
- `framework/inference_adapter.py` implements ADR-0004 contract
- `first_pass_success` ≥ 0.85
- `regression_detected` = false

### `phase_2_ready`

Phase 2 capability sessions may begin when Phase 1 is closed_ratified and the `local_autonomy_gate` is satisfied. (Phase 2 is already closed_ratified in this repository.)

### `local_autonomy_gate`

The local-autonomy gate determines whether LOCAL-FIRST execution is reliable enough to be the primary route:
- `first_pass_success` ≥ 0.70 on LOCAL-FIRST benchmark
- `retry_count` ≤ 1.0 average
- `escalation_rate` ≤ 0.10
- No `claude_rescue_not_local_autonomy` violations in last 5 LOCAL-FIRST packages

If this gate fails, LOCAL-FIRST packages require SUBSTRATE review before execution.

---

## Exceptions

### Claude escalation not counted as local autonomy

When a LOCAL-FIRST package is resolved by SUBSTRATE (Claude) execution — whether via approved escalation or a `claude_rescue_not_local_autonomy` violation — the result is not credited to the LOCAL-FIRST scorecard. The task is recorded as escalated.

**Why**: Counting SUBSTRATE rescues as LOCAL-FIRST successes would mask the true capability level of local execution and undermine the autonomy development goal.

### Missing artifact bundle blocks positive scoring

If a session's artifact bundle is missing or `bundle_valid=false`, `artifact_completeness` is forced to 0.0 for that session, regardless of how many artifacts are on disk.

**Why**: Unverifiable artifacts provide no auditability guarantee. Partial credit for unverifiable artifacts creates false confidence.

### Hard stop is escalation, not retry

A hard stop (validation script exit 1, gate failure, scope violation) increments `escalation_rate`, not `retry_count`. These are qualitatively different failure modes.

### Governance session floor

For `governance_session` type runs, `artifact_completeness` < 1.0 forces the overall grade to F, regardless of other metrics.

---

## Relationship to ADRs

| Scorecard element | ADR |
|-------------------|-----|
| `first_pass_success` | ADR-0007 (semantic_generation_rate dimension) |
| `retry_count` | ADR-0007 (retry dimension) |
| `escalation_rate` | ADR-0005 (permission model — escalation triggers) + ADR-0007 |
| `artifact_completeness` | ADR-0006 (artifact bundle — bundle_valid) + ADR-0007 |
| `validation_pass_rate` | ADR-0007 (validation_pass_rate dimension) |
| `promotion_readiness` | ADR-0001 (session schema — blockers_resolved) + ADR-0007 |
| Exceptions | ADR-0006 (artifact_completeness floor), ADR-0004 (LOCAL-FIRST routing) |

---

## Relationship to Definition of Done

The autonomy scorecard is the measurement instrument for the `governance_conformance` dimension of ADR-0007. It feeds into the Definition of Done as follows:

- `artifact_completeness` enforces `required_artifacts.required_runtime_artifacts`
- `validation_pass_rate` enforces `required_validation.make_check_required`
- `escalation_rate` enforces `telemetry_completeness.escalation_status`
- `promotion_readiness` evaluates `acceptance_rules` per session label

See `governance/definition_of_done.v1.yaml` for the full acceptance policy.

---

## Example

See `governance/cmdb_lite_registry.v1.yaml::autonomy_scorecard` for the Phase 7 baseline scorecard values that established the current performance floor.
