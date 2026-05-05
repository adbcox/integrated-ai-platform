"""Unit tests for stage7_manager strategy selection."""

from __future__ import annotations

from bin.stage7_manager import _apply_manager14_budget_fallback_shaping, _choose_subplan_strategy


def _base_inputs() -> dict:
    return {
        "subplan": {
            "size": 1,
            "risk_score": 0.0,
            "yield_score": 9.0,
            "targets": ["bin/stage6_manager.py"],
        },
        "task_class": "multi_file_orchestration",
        "scorecard": {"grouped_rate": 0.5, "split_rate": 0.5},
        "family_memory": {"escalation_rate": 0.0, "failure_rate": 0.0, "samples": 10},
        "qualification_posture": {"worker_pressure": False, "caution_mode": False},
        "budget_forecast": {"remaining": 1},
        "learning_priors": {
            "active": True,
            "weak_classes": ["multi_file_orchestration"],
            "recurrence_pressure": False,
            "benchmark_escalation_rate": 0.0,
            "benchmark_first_attempt_quality_rate": 0.52,
        },
        "trusted_guidance": {
            "active": False,
            "use_first_trusted_patterns": [],
            "avoid_trusted_patterns": [],
            "preferred_complexity_level": "medium",
        },
        "success_memory": {"preferred_strategy": "", "confidence": 0.0, "total_samples": 0},
        "resume_source_status": "",
    }


def test_weak_single_target_multi_file_tasks_split_first_under_learning_priors() -> None:
    result = _choose_subplan_strategy(**_base_inputs())

    assert result["strategy"] == "split_first"
    assert result["reason"] == "learning_priors_single_target_weak_class_split"


def test_manager14_retrieval_singleton_quota_cap_increases_under_replay_pressure() -> None:
    strategy_decisions = {"subplan-1": {"decision_tags": []}}
    result = _apply_manager14_budget_fallback_shaping(
        subplans=[{"subplan_id": "subplan-1", "targets": ["bin/stage6_manager.py"]}],
        strategy_decisions=strategy_decisions,
        recurrence_memory={
            "replay_pressure": True,
            "recent_bad_rate": 0.4,
            "strategy_bad_rates": {"grouped_subplan": 0.0},
        },
        task_class="retrieval_orchestration",
    )

    assert result["enabled"] is True
    assert result["singleton_quota_cap"] == 2
    assert strategy_decisions["subplan-1"]["manager14_singleton_quota_cap"] == 2
