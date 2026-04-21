"""Tests for AGCC1-P4: Aider reratification after command registration."""
import pytest

from framework.aider_live_execution_gate import evaluate_aider_live_gate
from framework.aider_live_proof import run_aider_live_proof
from framework.aider_promotion_ratifier import (
    ratify_aider_promotion,
    AiderPromotionArtifact,
    AIDER_PROMOTION_DONE,
    AIDER_PROMOTION_PARTIAL,
)


def _ratify(dry_run=True, num_runs=2):
    g = evaluate_aider_live_gate(dry_run=dry_run)
    p = run_aider_live_proof(g, num_runs=num_runs, dry_run=dry_run)
    return ratify_aider_promotion(g, p, dry_run=dry_run)


def test_import_ok():
    from framework.aider_promotion_ratifier import ratify_aider_promotion  # noqa: F401


def test_returns_artifact():
    a = _ratify()
    assert isinstance(a, AiderPromotionArtifact)


def test_decision_is_valid():
    a = _ratify()
    assert a.decision in (AIDER_PROMOTION_DONE, AIDER_PROMOTION_PARTIAL)


def test_rationale_nonempty():
    a = _ratify()
    assert a.rationale and len(a.rationale) > 0


def test_gate_result_propagated():
    a = _ratify()
    assert a.gate_result in ("live_gate_pass", "live_gate_block")


def test_proof_status_propagated():
    a = _ratify()
    assert a.proof_status in ("live_proven", "dry_run_only", "blocked", "not_evaluated")


def test_live_execution_safe_is_bool():
    a = _ratify()
    assert isinstance(a.live_execution_safe, bool)


def test_to_dict_schema_version():
    a = _ratify()
    d = a.to_dict()
    assert d["schema_version"] == 1


def test_to_dict_has_decision():
    a = _ratify()
    d = a.to_dict()
    assert "decision" in d


def test_bin_script_importable():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "ratify_aider_postreg",
        Path(__file__).resolve().parents[1] / "bin" / "ratify_aider_postreg.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "main")


def test_bin_script_dry_run_exits_zero(monkeypatch, capsys):
    import sys
    from pathlib import Path
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ratify_aider_postreg",
        Path(__file__).resolve().parents[1] / "bin" / "ratify_aider_postreg.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(sys, "argv", ["ratify_aider_postreg.py", "--dry-run", "--num-runs", "1"])
    result = mod.main()
    assert result == 0
