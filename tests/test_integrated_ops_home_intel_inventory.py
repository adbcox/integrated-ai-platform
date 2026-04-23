"""Tests for integrated ops/home/intel/inventory shared pipeline."""

from framework.integrated_ops_home_intel_inventory import (
    build_integrated_artifact,
    build_ops_queue,
    derive_home_actions,
    derive_intel_recommendations,
)


def test_derive_home_actions_respects_policy_fields():
    actions = derive_home_actions(
        [
            {"domain": "lighting", "intent": "scene", "target": "kitchen"},
            {"domain": "climate", "intent": "pre_cool", "target": "bedroom"},
        ],
        {
            "bounded_actions": {
                "lighting": {"max_actions_per_run": 3, "required_confirmation": False},
                "climate": {"max_actions_per_run": 2, "required_confirmation": True},
            }
        },
    )

    assert len(actions) == 2
    assert actions[0]["required_confirmation"] is False
    assert actions[1]["required_confirmation"] is True
    assert actions[1]["bounded_max_actions"] == 2


def test_intel_recommendations_sorted_and_filtered():
    recs = derive_intel_recommendations(
        [
            {"name": "A", "category": "tool", "recommendation_class": "watch"},
            {"name": "B", "category": "tool", "recommendation_class": "adopt-now"},
            {"name": "C", "category": "tool", "recommendation_class": "reject"},
        ],
        {"adopt-now": 4, "watch": 2, "reject": 1},
        {"reject"},
        5,
    )

    assert [row["name"] for row in recs] == ["B", "A"]


def test_build_integrated_artifact_contains_four_item_links():
    procurement_result = {
        "procurement_decisions": [{"part_number": "X"}],
        "summary": {"total_procurement_cost": 10.0},
    }
    queue = build_ops_queue(
        [{"action_id": "home-action-1", "required_confirmation": False}],
        [{"recommendation_class": "adopt-now"}],
        procurement_result,
    )

    artifact = build_integrated_artifact(
        runtime_session={"session_id": "s", "job_id": "j", "objective": "o", "allowed_files": [], "forbidden_files": []},
        control_window_state={"current_lane": "control_window", "current_branch": "exec-lane", "route_decision": {"selected_lane": "control_window"}},
        home_actions=[{"action_id": "home-action-1"}],
        intel_recommendations=[{"name": "Tool"}],
        procurement_result=procurement_result,
        ops_queue=queue,
        policy_path="governance/integrated_ops_home_intel_inventory_policy.v1.yaml",
    )

    assert set(artifact["roadmap_items"]) == {"RM-OPS-006", "RM-HOME-005", "RM-INTEL-003", "RM-INV-003"}
    assert artifact["ops_execution"]["queue_size"] >= 3
