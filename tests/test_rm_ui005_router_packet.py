from __future__ import annotations

from framework.rm_ui005_control_window import build_aider_packet, classify_lane


def test_route_classification_control_window():
    decision = classify_lane("Build RM-UI-005 control window dashboard with OpenHands path")
    assert decision.selected_lane == "control_window"
    assert decision.score_by_lane["control_window"] >= decision.score_by_lane["bugfix"]


def test_route_classification_bugfix():
    decision = classify_lane("Fix regression bug in runtime executor validation")
    assert decision.selected_lane == "bugfix"


def test_route_classification_repo_audit():
    decision = classify_lane("Audit roadmap consistency and blocker registry status sync")
    assert decision.selected_lane == "repo_audit"


def test_route_classification_bounded_feature_fallback():
    decision = classify_lane("add support for a new local command")
    assert decision.selected_lane in {"bounded_feature", "control_window"}


def test_aider_packet_contains_required_fields():
    decision = classify_lane("Implement bounded feature for parser")
    packet = build_aider_packet("Implement bounded feature for parser", decision)

    required_keys = {
        "selected_lane",
        "objective",
        "bounded_scope",
        "allowed_files",
        "forbidden_files",
        "preload_context_files",
        "drop_candidates",
        "validations_to_run",
        "completion_criteria",
        "truth_surfaces_to_update",
        "stop_conditions",
        "context_pressure",
    }
    assert required_keys.issubset(packet.keys())
    assert packet["selected_lane"] in {"bounded_feature", "bugfix", "control_window", "repo_audit"}
    assert packet["validations_to_run"]
    pressure = packet["context_pressure"]
    assert "narrowing_recommendations" in pressure
    assert isinstance(pressure["narrowing_recommendations"], list)
    assert pressure["narrowing_recommendations"]
    assert "must_retain_context" in pressure
    assert "safe_to_drop_context" in pressure


def test_aider_packet_item_complete_wording_tracks_canonical_contract():
    decision = classify_lane("Build RM-UI-005 control window dashboard with OpenHands path")
    packet = build_aider_packet("RM-UI-005 closure validation", decision)
    criteria = packet["completion_criteria"]["item_complete"]
    criteria_text = " ".join(criteria).lower()
    assert "canonical rm-ui-005 item completion contract" in criteria_text
    assert "all planned slices and dod evidence" in criteria_text
    assert "first slice is runnable" not in criteria_text
