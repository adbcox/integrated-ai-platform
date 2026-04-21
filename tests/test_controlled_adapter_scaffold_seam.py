"""Conformance tests for framework/controlled_adapter_scaffold.py (LARAC2-CONTROLLED-ADAPTER-SCAFFOLD-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.controlled_adapter_scaffold import (
    ScaffoldGate, AdapterScaffoldPlan, ControlledAdapterScaffold, emit_scaffold_plan
)
from framework.adapter_readiness_stress import StressHarnessResult, StressCheck
from framework.adapter_campaign_pre_authorizer import PreAuthorizationArtifact


def _stress_result(verdict="stable", blocking_failures=0):
    return StressHarnessResult(
        verdict=verdict,
        checks=[],
        blocking_failures=blocking_failures,
        quality_score=0.75,
        analyzed_at="2026-01-01T00:00:00+00:00",
        artifact_path=None,
    )


def _pre_auth(decision="authorized", all_gates_passed=True, campaign_id="camp-1"):
    return PreAuthorizationArtifact(
        campaign_id=campaign_id,
        decision=decision,
        gates=[],
        all_gates_passed=all_gates_passed,
        defer_reasons=[],
        next_steps=[],
        generated_at="2026-01-01T00:00:00+00:00",
        artifact_path=None,
    )


# --- import and type ---

def test_import_scaffold():
    assert callable(ControlledAdapterScaffold)


def test_returns_adapter_scaffold_plan():
    plan = ControlledAdapterScaffold().build()
    assert isinstance(plan, AdapterScaffoldPlan)


# --- all-none returns blocked ---

def test_all_none_blocked():
    plan = ControlledAdapterScaffold().build()
    assert plan.scaffold_decision == "blocked"


def test_all_none_gates_all_fail():
    plan = ControlledAdapterScaffold().build()
    assert plan.gates_passed == 0


# --- stress gate ---

def test_stress_stable_gate_passes():
    plan = ControlledAdapterScaffold().build(stress_result=_stress_result("stable"))
    stress_gate = next(g for g in plan.gates if g.gate_name == "stress_stable")
    assert stress_gate.passed is True


def test_stress_unstable_gate_fails():
    plan = ControlledAdapterScaffold().build(stress_result=_stress_result("unstable", 2))
    stress_gate = next(g for g in plan.gates if g.gate_name == "stress_stable")
    assert stress_gate.passed is False


def test_stress_unknown_gate_fails():
    plan = ControlledAdapterScaffold().build(stress_result=_stress_result("unknown", 1))
    stress_gate = next(g for g in plan.gates if g.gate_name == "stress_stable")
    assert stress_gate.passed is False


# --- pre-auth gate ---

def test_pre_auth_authorized_gate_passes():
    plan = ControlledAdapterScaffold().build(pre_auth=_pre_auth("authorized", True))
    auth_gate = next(g for g in plan.gates if g.gate_name == "pre_auth_authorized")
    assert auth_gate.passed is True


def test_pre_auth_deferred_gate_fails():
    plan = ControlledAdapterScaffold().build(pre_auth=_pre_auth("deferred", False))
    auth_gate = next(g for g in plan.gates if g.gate_name == "pre_auth_authorized")
    assert auth_gate.passed is False


def test_pre_auth_gates_not_all_passed_fails():
    plan = ControlledAdapterScaffold().build(pre_auth=_pre_auth("authorized", False))
    auth_gate = next(g for g in plan.gates if g.gate_name == "pre_auth_authorized")
    assert auth_gate.passed is False


# --- proceed / defer ---

def test_proceed_when_all_gates_pass():
    plan = ControlledAdapterScaffold().build(
        stress_result=_stress_result("stable"),
        pre_auth=_pre_auth("authorized", True),
    )
    assert plan.scaffold_decision == "proceed"
    assert plan.gates_passed == 2
    assert plan.defer_reasons == []


def test_defer_when_stress_fails():
    plan = ControlledAdapterScaffold().build(
        stress_result=_stress_result("unstable", 1),
        pre_auth=_pre_auth("authorized", True),
    )
    assert plan.scaffold_decision == "defer"
    assert len(plan.defer_reasons) >= 1


def test_defer_when_pre_auth_fails():
    plan = ControlledAdapterScaffold().build(
        stress_result=_stress_result("stable"),
        pre_auth=_pre_auth("deferred", False),
    )
    assert plan.scaffold_decision == "defer"


# --- campaign_id propagation ---

def test_campaign_id_propagated():
    plan = ControlledAdapterScaffold().build(pre_auth=_pre_auth(campaign_id="my-campaign"))
    assert plan.campaign_id == "my-campaign"


def test_campaign_id_none_when_no_pre_auth():
    plan = ControlledAdapterScaffold().build()
    assert plan.campaign_id is None


# --- gates structure ---

def test_gates_list_length():
    plan = ControlledAdapterScaffold().build()
    assert len(plan.gates) == 2


def test_gates_are_scaffold_gate():
    plan = ControlledAdapterScaffold().build()
    for g in plan.gates:
        assert isinstance(g, ScaffoldGate)


# --- artifact ---

def test_artifact_written(tmp_path):
    plan = ControlledAdapterScaffold().build()
    path = emit_scaffold_plan(plan, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable(tmp_path):
    plan = ControlledAdapterScaffold().build()
    path = emit_scaffold_plan(plan, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "scaffold_decision" in data
    assert "gates" in data
    assert "defer_reasons" in data


def test_artifact_path_set(tmp_path):
    plan = ControlledAdapterScaffold().build()
    path = emit_scaffold_plan(plan, artifact_dir=tmp_path)
    assert plan.artifact_path == path


# --- no live adapter code ---

def test_no_live_adapter_introduced():
    import framework.controlled_adapter_scaffold as m
    src = Path(m.__file__).read_text()
    assert "live_bridge_adapter" not in src
    assert "ClaudeCodeExecutor" not in src


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "ControlledAdapterScaffold")
    assert hasattr(framework, "AdapterScaffoldPlan")
    assert hasattr(framework, "ScaffoldGate")
    assert hasattr(framework, "emit_scaffold_plan")
