"""Tests for AGCC1-P3: post-registration gate and proof rerun."""
import pytest

from framework.aider_live_execution_gate import evaluate_aider_live_gate, LIVE_GATE_PASS, LIVE_GATE_BLOCK
from framework.aider_live_proof import run_aider_live_proof, PROOF_STATUS_BLOCKED, PROOF_STATUS_LIVE_PROVEN, PROOF_STATUS_DRY_RUN_ONLY


def test_gate_callable():
    r = evaluate_aider_live_gate(dry_run=True)
    assert r is not None


def test_gate_overall_result_is_valid():
    r = evaluate_aider_live_gate(dry_run=True)
    assert r.overall_result in (LIVE_GATE_PASS, LIVE_GATE_BLOCK)


def test_gate_command_registered_now_passes():
    from framework.local_command_runner import KNOWN_FRAMEWORK_COMMANDS
    assert "aider" in KNOWN_FRAMEWORK_COMMANDS


def test_gate_live_execution_safe_is_bool():
    r = evaluate_aider_live_gate(dry_run=True)
    assert isinstance(r.live_execution_safe, bool)


def test_gate_blocking_checks_is_list():
    r = evaluate_aider_live_gate(dry_run=True)
    assert isinstance(r.blocking_checks, list)


def test_proof_callable_when_gate_blocked():
    g = evaluate_aider_live_gate(dry_run=True)
    p = run_aider_live_proof(g, num_runs=2, dry_run=True)
    assert p is not None


def test_proof_status_valid():
    g = evaluate_aider_live_gate(dry_run=True)
    p = run_aider_live_proof(g, num_runs=2, dry_run=True)
    assert p.proof_status in (PROOF_STATUS_BLOCKED, PROOF_STATUS_LIVE_PROVEN, PROOF_STATUS_DRY_RUN_ONLY)


def test_proof_records_count_matches_num_runs():
    g = evaluate_aider_live_gate(dry_run=True)
    p = run_aider_live_proof(g, num_runs=2, dry_run=True)
    assert p.total_runs == 2
    assert len(p.records) == 2


def test_proof_when_gate_blocked_is_blocked():
    g = evaluate_aider_live_gate(dry_run=True)
    if not g.live_execution_safe:
        p = run_aider_live_proof(g, num_runs=2, dry_run=True)
        assert p.proof_status == PROOF_STATUS_BLOCKED


def test_proof_gate_result_propagated():
    g = evaluate_aider_live_gate(dry_run=True)
    p = run_aider_live_proof(g, num_runs=2, dry_run=True)
    assert p.gate_result == g.overall_result


def test_bin_script_importable():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "run_aider_postreg_gate_proof",
        Path(__file__).resolve().parents[1] / "bin" / "run_aider_postreg_gate_proof.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "main")


def test_bin_script_dry_run_exits_zero(tmp_path, monkeypatch, capsys):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_aider_postreg_gate_proof",
        Path(__file__).resolve().parents[1] / "bin" / "run_aider_postreg_gate_proof.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(sys, "argv", ["run_aider_postreg_gate_proof.py", "--dry-run", "--num-runs", "1"])
    result = mod.main()
    assert result == 0
