"""Unit tests for the Codex 5.1 replacement benchmark calibration."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bin"))

from bin.codex51_replacement_benchmark import PlanRun, evaluate_pass_fail, summarize_metrics


def _run(
    *,
    plan_id: str,
    success: bool,
    failure_signature: str,
    rescue_count: int = 0,
    escalation_count: int = 0,
    guard_count: int = 0,
) -> PlanRun:
    return PlanRun(
        plan_id=plan_id,
        timestamp="2026-05-05T12:00:00Z",
        query="test query",
        class_id="retrieval_orchestration",
        class_label="B. Retrieval + orchestration changes",
        ranking_version="rag10-v1-execution-cohort-cluster",
        state="succeeded" if success else "failed",
        failure_code=0 if success else 1,
        total_subplans=1,
        first_attempt_success=1 if success else 0,
        first_attempt_quality_rate=1.0 if success else 0.0,
        first_attempt_quality_score=1.0 if success else 0.0,
        first_to_final_improvement=0.0,
        final_success_rate=1.0 if success else 0.0,
        first_code_outcome_rate=0.0,
        final_code_outcome_rate=0.0,
        code_outcome_coverage_rate=0.0,
        code_diff_integrity_rate=0.0,
        rescue_count=rescue_count,
        escalation_count=escalation_count,
        guard_count=guard_count,
        success=success,
        failure_signature=failure_signature,
        attribution_profile="normal",
        attribution_primary="mixed_gain",
    )


def test_recurrence_is_insufficient_data_below_three_distinct_failed_tasks() -> None:
    metrics = summarize_metrics(
        [
            _run(plan_id="p1", success=False, failure_signature="deferred_worker_budget"),
            _run(plan_id="p2", success=True, failure_signature=""),
            _run(plan_id="p3", success=True, failure_signature=""),
            _run(plan_id="p4", success=True, failure_signature=""),
        ]
    )
    pass_fail = evaluate_pass_fail(metrics, {"min_success_rate": 0.7, "max_recurrence_rate": 0.35})

    assert metrics["recurrence_status"] == "insufficient_data"
    assert metrics["recurrence_rate"] is None
    assert pass_fail["overall_pass"] is True
    assert pass_fail["checks"]["recurrence_rate"]["pass"] is True
    assert pass_fail["checks"]["recurrence_rate"]["status"] == "insufficient_data"


def test_recurrence_computes_normally_at_three_distinct_failed_tasks() -> None:
    metrics = summarize_metrics(
        [
            _run(plan_id="p1", success=False, failure_signature="deferred_worker_budget"),
            _run(plan_id="p2", success=False, failure_signature="deferred_worker_budget"),
            _run(plan_id="p3", success=False, failure_signature="other_failure"),
        ]
    )
    pass_fail = evaluate_pass_fail(metrics, {"min_success_rate": 0.0, "max_recurrence_rate": 0.35})

    assert metrics["recurrence_status"] == "computed"
    assert metrics["recurrence_rate"] == 0.667
    assert pass_fail["checks"]["recurrence_rate"]["pass"] is False
