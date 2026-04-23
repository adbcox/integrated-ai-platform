from __future__ import annotations

import json
from pathlib import Path

import framework.rm_ui005_control_window as cw


def test_planning_and_completion_panels(monkeypatch, tmp_path: Path):
    next_pull = {
        "status": "has_eligible_targets",
        "chosen_next_item": "RM-XYZ-001",
        "next_pull_candidates": [{"id": "RM-XYZ-001", "reasons": ["top_score"]}],
        "nodes": {"RM-XYZ-001": {"reasons": ["top_score", "deps_clear"]}},
    }
    blockers = {
        "summary": {"true_blocker_count": 0},
        "true_blockers": [],
        "blocked_external_dependency_items": [],
        "blocked_placeholder_items": [],
    }

    next_pull_path = tmp_path / "next_pull.json"
    blocker_path = tmp_path / "blockers.json"
    validation_path = tmp_path / "validation_state.json"
    artifact_root = tmp_path / "rm_ui005"

    next_pull_path.write_text(json.dumps(next_pull), encoding="utf-8")
    blocker_path.write_text(json.dumps(blockers), encoding="utf-8")
    validation_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-04-22T00:00:00Z",
                "results": {
                    "make_check": {"status": "pass"},
                    "make_quick": {"status": "pass"},
                    "make_test_offline": {"status": "pass"},
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(cw, "PLANNING_NEXT_PULL", next_pull_path)
    monkeypatch.setattr(cw, "PLANNING_BLOCKERS", blocker_path)
    monkeypatch.setattr(cw, "VALIDATION_STATE", validation_path)
    monkeypatch.setattr(cw, "ARTIFACT_ROOT", artifact_root)
    monkeypatch.setattr(cw, "_canonical_rm_ui005_item_contract_satisfied", lambda: True)
    monkeypatch.setattr(
        cw,
        "build_openhands_plan",
        lambda **_: {
            "selected_mode": "serve",
            "selected_plan": {
                "mode": "serve",
                "ready": False,
                "reason": "openhands_module_missing",
                "command": ["python3", "-m", "openhands", "serve", "--workspace", "/tmp/repo"],
            },
            "available_modes": {"serve": {"mode": "serve", "ready": False}},
            "ready": False,
            "dry_run_ready": True,
            "integration_ready": False,
            "sandbox_posture": "host",
            "authority_model": "subordinate_to_control_window_route_and_completion_contract",
        },
    )

    state = cw.build_control_window_state(task_input="implement control window", objective="obj", openhands_mode="serve")

    assert state["planning"]["next_eligible_target"] == "RM-XYZ-001"
    assert state["planning"]["why_selected"]
    assert "completion_ladder" in state
    assert set(state["completion_ladder"].keys()) == {
        "substep_complete",
        "bounded_slice_complete",
        "item_complete",
        "blocker_chain_cleared",
        "objective_achieved",
    }
    assert state["openhands"]["selected_mode"] == "serve"
    assert "available_modes" in state["openhands"]
    assert "serve" in state["openhands"]["available_modes"]
    assert "integration_ready" in state["openhands"]
    assert state["completion_ladder"]["item_complete"] is True
    assert state["completion_ladder"]["objective_achieved"] is True


def test_emit_control_window_state(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(cw, "ARTIFACT_ROOT", tmp_path / "out")
    state = {
        "generated_at": "2026-04-22T00:00:00Z",
        "current_objective": "x",
        "current_lane": "control_window",
        "current_branch": "main",
        "route_decision": {},
        "aider_run_packet": {},
        "planning": {},
        "context_token_pressure": {},
        "validation_panel": {},
        "artifact_panel": {},
        "completion_ladder": {},
        "openhands": {},
    }
    out = cw.emit_control_window_state(state, artifact_root=tmp_path / "out")
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["current_lane"] == "control_window"


def test_dry_run_readiness_does_not_elevate_item_completion_without_openhands_contract():
    validation_panel = {
        "required_validations": [
            {"id": "make_check", "status": "pass"},
            {"id": "make_quick", "status": "pass"},
            {"id": "make_test_offline", "status": "pass"},
        ]
    }
    artifact_panel = {"missing_evidence": []}
    planning = {"blocker_chain": []}

    ladder = cw.build_completion_ladder(
        validation_panel=validation_panel,
        artifact_panel=artifact_panel,
        planning=planning,
        openhands_contract_satisfied=False,
        canonical_item_contract_satisfied=True,
    )

    assert ladder["bounded_slice_complete"] is True
    assert ladder["item_complete"] is False
    assert ladder["objective_achieved"] is False


def test_canonical_contract_must_be_satisfied_for_item_completion():
    validation_panel = {
        "required_validations": [
            {"id": "make_check", "status": "pass"},
            {"id": "make_quick", "status": "pass"},
            {"id": "make_test_offline", "status": "pass"},
        ]
    }
    artifact_panel = {"missing_evidence": []}
    planning = {"blocker_chain": []}

    ladder = cw.build_completion_ladder(
        validation_panel=validation_panel,
        artifact_panel=artifact_panel,
        planning=planning,
        openhands_contract_satisfied=True,
        canonical_item_contract_satisfied=False,
    )

    assert ladder["bounded_slice_complete"] is True
    assert ladder["item_complete"] is False
    assert ladder["objective_achieved"] is False


def test_openhands_contract_satisfied_requires_authority_and_command():
    bad = {
        "authority_model": "wrong",
        "dry_run_ready": True,
        "selected_plan": {"command": ["python3", "-m", "openhands", "serve"]},
    }
    assert cw._openhands_contract_satisfied(bad) is False

    good = {
        "authority_model": "subordinate_to_control_window_route_and_completion_contract",
        "dry_run_ready": True,
        "selected_plan": {"command": ["python3", "-m", "openhands", "serve"]},
    }
    assert cw._openhands_contract_satisfied(good) is True
