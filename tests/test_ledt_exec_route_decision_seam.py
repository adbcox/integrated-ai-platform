"""Seam tests for LEDT-P4-EXEC-ROUTE-DECISION-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.local_exec_eligibility_contract import LocalExecEligibilityEvaluator, LocalExecEligibilityInput
from framework.local_exec_preflight import LocalExecPreflightEvaluator
from framework.exec_route_decision import ExecRouteDecider, ExecRouteDecision

def _elig(pid="test", fsc=2, ext=False, broad=False, infra=False, vcmds=None):
    return LocalExecEligibilityEvaluator().evaluate(
        LocalExecEligibilityInput(pid, fsc, ext, broad, infra, vcmds or ["make check"])
    )

def _pre(pid="test", fsc=2, vcmds=None):
    return LocalExecPreflightEvaluator().evaluate(pid, fsc, vcmds or ["make check"])

def test_import_decider():
    assert callable(ExecRouteDecider)

def test_decide_returns_decision():
    d = ExecRouteDecider().decide(_elig(), _pre())
    assert isinstance(d, ExecRouteDecision)

def test_eligible_and_ready_gives_local_execute():
    d = ExecRouteDecider().decide(_elig(), _pre())
    assert d.route == "local_execute"
    assert d.fallback_authorized is False

def test_ineligible_gives_claude_fallback():
    d = ExecRouteDecider().decide(_elig(ext=True), _pre())
    assert d.route == "claude_fallback"
    assert d.fallback_authorization_reason is not None

def test_local_execute_has_no_fallback_reason():
    d = ExecRouteDecider().decide(_elig(), _pre())
    assert d.fallback_authorization_reason is None

def test_emit_artifact_local_rate(tmp_path):
    decider = ExecRouteDecider()
    decisions = [
        decider.decide(_elig("a"), _pre("a")),
        decider.decide(_elig("b"), _pre("b")),
        decider.decide(_elig("c"), _pre("c")),
        decider.decide(_elig("d", ext=True), _pre("d")),
        decider.decide(_elig("e", fsc=2, vcmds=[]), _pre("e", vcmds=[])),
    ]
    path = decider.emit(decisions, tmp_path)
    d = json.loads(Path(path).read_text())
    assert d["local_execute_count"] >= 3
    assert d["local_execute_rate"] >= 0.5
    assert all(dec["decision_reason"] for dec in d["sample_decisions"])
