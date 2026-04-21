"""Tests for APCC1-P4: postfix wired gate and proof seam."""
import pytest

from framework.aider_live_gate_wired import (
    evaluate_wired_aider_gate,
    run_wired_aider_proof,
    _ARA_ACCEPTS_CHECKER,
)
from framework.aider_live_execution_gate import AiderLiveGateReport, LIVE_GATE_PASS, LIVE_GATE_BLOCK
from framework.aider_live_proof import (
    AiderLiveProofReport,
    PROOF_STATUS_BLOCKED,
    PROOF_STATUS_DRY_RUN_ONLY,
    PROOF_STATUS_LIVE_PROVEN,
)


def test_evaluate_wired_gate_returns_report():
    r = evaluate_wired_aider_gate(dry_run=True)
    assert isinstance(r, AiderLiveGateReport)


def test_wired_gate_live_execution_safe_is_bool():
    r = evaluate_wired_aider_gate(dry_run=True)
    assert isinstance(r.live_execution_safe, bool)


def test_wired_gate_live_execution_safe_is_true():
    r = evaluate_wired_aider_gate(dry_run=True)
    assert r.live_execution_safe is True


def test_wired_gate_overall_result_is_pass():
    r = evaluate_wired_aider_gate(dry_run=True)
    assert r.overall_result == LIVE_GATE_PASS


def test_wired_gate_no_blocking_checks():
    r = evaluate_wired_aider_gate(dry_run=True)
    assert list(r.blocking_checks) == []


def test_wired_gate_has_permission_gate_check_passing():
    r = evaluate_wired_aider_gate(dry_run=True)
    names = {c.check_name: c.passed for c in r.checks}
    assert names.get("permission_gate_active") is True


def test_wired_gate_has_config_keys_check_passing():
    r = evaluate_wired_aider_gate(dry_run=True)
    names = {c.check_name: c.passed for c in r.checks}
    assert names.get("config_keys_present") is True


def test_run_wired_proof_returns_report():
    g = evaluate_wired_aider_gate(dry_run=True)
    p = run_wired_aider_proof(g, num_runs=2, dry_run=True)
    assert isinstance(p, AiderLiveProofReport)


def test_run_wired_proof_dry_run_status():
    g = evaluate_wired_aider_gate(dry_run=True)
    p = run_wired_aider_proof(g, num_runs=2, dry_run=True)
    assert p.proof_status in (PROOF_STATUS_DRY_RUN_ONLY, PROOF_STATUS_LIVE_PROVEN, PROOF_STATUS_BLOCKED)


def test_ara_accepts_checker_is_bool():
    assert isinstance(_ARA_ACCEPTS_CHECKER, bool)


def test_bin_script_importable():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "run_aider_postfix_gate_proof",
        Path(__file__).resolve().parents[1] / "bin" / "run_aider_postfix_gate_proof.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "main")


def test_bin_script_dry_run_exits_zero(monkeypatch, capsys):
    import sys
    from pathlib import Path
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_aider_postfix_gate_proof",
        Path(__file__).resolve().parents[1] / "bin" / "run_aider_postfix_gate_proof.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(sys, "argv", ["run_aider_postfix_gate_proof.py", "--dry-run", "--num-runs", "1"])
    result = mod.main()
    assert result == 0
