"""Seam tests for AiderPromotionReratifier (AIDER-FINAL-PROMOTION-RERATIFIER-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.aider_promotion_reratifier import (
    AiderPromotionDecision,
    AiderPromotionReratifier,
    emit_aider_promotion_decision,
)


def _all_true():
    return {
        "gate_passed": True,
        "wired_checker_called": True,
        "propagation_verified": True,
        "subprocess_isolation_verified": True,
        "blocking_reason": None,
    }


def _with(**overrides):
    d = _all_true()
    d.update(overrides)
    return d


def test_import_reratifier():
    assert callable(AiderPromotionReratifier)


def test_all_true_yields_aider_done():
    d = AiderPromotionReratifier().decide(live_gate_proof=_all_true())
    assert d.decision == "aider_done"


def test_gate_false_yields_aider_partial():
    d = AiderPromotionReratifier().decide(live_gate_proof=_with(gate_passed=False))
    assert d.decision == "aider_partial"


def test_checker_not_called_yields_aider_partial():
    d = AiderPromotionReratifier().decide(live_gate_proof=_with(wired_checker_called=False))
    assert d.decision == "aider_partial"


def test_propagation_false_yields_aider_partial():
    d = AiderPromotionReratifier().decide(live_gate_proof=_with(propagation_verified=False))
    assert d.decision == "aider_partial"


def test_subprocess_not_isolated_yields_aider_partial():
    d = AiderPromotionReratifier().decide(live_gate_proof=_with(subprocess_isolation_verified=False))
    assert d.decision == "aider_partial"


def test_aider_partial_has_blocking_reason():
    d = AiderPromotionReratifier().decide(live_gate_proof=_with(gate_passed=False, blocking_reason="gate blocked"))
    assert d.decision == "aider_partial"
    assert d.blocking_reason is not None


def test_aider_done_blocking_reason_none():
    d = AiderPromotionReratifier().decide(live_gate_proof=_all_true())
    assert d.blocking_reason is None


def test_returns_aider_promotion_decision():
    d = AiderPromotionReratifier().decide(live_gate_proof=_all_true())
    assert isinstance(d, AiderPromotionDecision)


def test_artifact_written(tmp_path):
    d = AiderPromotionReratifier().decide(live_gate_proof=_all_true())
    path = emit_aider_promotion_decision(d, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable(tmp_path):
    d = AiderPromotionReratifier().decide(live_gate_proof=_all_true())
    path = emit_aider_promotion_decision(d, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "decision" in data
    assert data["decision"] in ("aider_done", "aider_partial")


def test_artifact_path_set(tmp_path):
    d = AiderPromotionReratifier().decide(live_gate_proof=_all_true())
    path = emit_aider_promotion_decision(d, artifact_dir=tmp_path)
    assert d.artifact_path == path


def test_package_surface():
    import framework
    assert hasattr(framework, "AiderPromotionReratifier")
    assert hasattr(framework, "AiderPromotionDecision")
    assert hasattr(framework, "emit_aider_promotion_decision")
