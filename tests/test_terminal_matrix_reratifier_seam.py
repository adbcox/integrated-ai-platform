"""Tests for APCC1-P6: terminal matrix reratifier seam."""
import pytest

from framework.aider_live_gate_wired import evaluate_wired_aider_gate, run_wired_aider_proof
from framework.aider_promotion_ratifier import ratify_aider_promotion
from framework.codex_availability_gate import evaluate_codex_availability
from framework.codex_promotion_ratifier import ratify_codex_promotion
from framework.cmdb_promotion_evidence import evaluate_cmdb_promotion_evidence
from framework.cmdb_promotion_ratifier import ratify_cmdb_promotion
from framework.domain_branch_first_wave_ratifier import ratify_first_wave_promotion
from framework.domain_branch_second_wave_ratifier import ratify_second_wave_promotion
from framework.terminal_promotion_ratifier import (
    ratify_terminal_promotion,
    TerminalPromotionArtifact,
    TERMINAL_PROMOTION_COMPLETE,
    TERMINAL_PROMOTION_PARTIAL,
)


def _full_chain(dry_run=True):
    g = evaluate_wired_aider_gate(dry_run=dry_run)
    p = run_wired_aider_proof(g, num_runs=2, dry_run=dry_run)
    aider_a = ratify_aider_promotion(g, p, dry_run=dry_run)
    avail = evaluate_codex_availability(dry_run=dry_run)
    codex_a = ratify_codex_promotion(avail, dry_run=dry_run)
    evidence = evaluate_cmdb_promotion_evidence(dry_run=dry_run)
    cmdb_a = ratify_cmdb_promotion(evidence, dry_run=dry_run)
    first_a = ratify_first_wave_promotion(dry_run=dry_run)
    second_a = ratify_second_wave_promotion(dry_run=dry_run)
    return ratify_terminal_promotion(
        aider_artifact=aider_a,
        codex_artifact=codex_a,
        cmdb_artifact=cmdb_a,
        first_wave_artifact=first_a,
        second_wave_artifact=second_a,
        dry_run=dry_run,
    )


def test_returns_artifact():
    a = _full_chain()
    assert isinstance(a, TerminalPromotionArtifact)


def test_decision_is_valid():
    a = _full_chain()
    assert a.decision in (TERMINAL_PROMOTION_COMPLETE, TERMINAL_PROMOTION_PARTIAL)


def test_total_count_eight():
    a = _full_chain()
    assert a.total_count == 8


def test_unresolved_items_is_explicit_list():
    a = _full_chain()
    assert isinstance(a.unresolved_items, list)


def test_resolved_count_seven_when_aider_partial():
    a = _full_chain()
    if a.decision == TERMINAL_PROMOTION_PARTIAL:
        assert a.resolved_count == 7


def test_aider_overall_unresolved_when_partial():
    a = _full_chain()
    if a.decision == TERMINAL_PROMOTION_PARTIAL:
        assert "aider_overall" in a.unresolved_items


def test_unresolved_empty_when_complete():
    a = _full_chain()
    if a.decision == TERMINAL_PROMOTION_COMPLETE:
        assert a.unresolved_items == []
        assert a.resolved_count == 8


def test_to_dict_schema_version():
    a = _full_chain()
    d = a.to_dict()
    assert d["schema_version"] == 1


def test_bin_script_importable():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "ratify_terminal_postfix",
        Path(__file__).resolve().parents[1] / "bin" / "ratify_terminal_postfix.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "main")


def test_bin_script_dry_run_exits_zero(monkeypatch, capsys):
    import sys
    from pathlib import Path
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ratify_terminal_postfix",
        Path(__file__).resolve().parents[1] / "bin" / "ratify_terminal_postfix.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(sys, "argv", ["ratify_terminal_postfix.py", "--dry-run"])
    result = mod.main()
    assert result == 0
