"""Tests for framework.aider_live_execution_gate — LAPC1 P2."""
import json
import pytest
from pathlib import Path

from framework.aider_live_execution_gate import (
    LIVE_GATE_PASS,
    LIVE_GATE_BLOCK,
    AiderLiveGateCheck,
    AiderLiveGateReport,
    evaluate_aider_live_gate,
)


def test_import_ok():
    from framework.aider_live_execution_gate import evaluate_aider_live_gate, AiderLiveGateReport  # noqa: F401


def test_constants():
    assert LIVE_GATE_PASS == "live_gate_pass"
    assert LIVE_GATE_BLOCK == "live_gate_block"


def test_returns_report():
    r = evaluate_aider_live_gate(dry_run=True)
    assert isinstance(r, AiderLiveGateReport)


def test_exactly_four_checks():
    r = evaluate_aider_live_gate(dry_run=True)
    assert len(r.checks) == 4


def test_check_names():
    r = evaluate_aider_live_gate(dry_run=True)
    names = {c.check_name for c in r.checks}
    assert names == {"command_registered", "preflight_verdict", "policy_ollama_first", "dry_run_default_safe"}


def test_live_execution_safe_is_bool():
    r = evaluate_aider_live_gate(dry_run=True)
    assert isinstance(r.live_execution_safe, bool)


def test_overall_result_is_valid():
    r = evaluate_aider_live_gate(dry_run=True)
    assert r.overall_result in (LIVE_GATE_PASS, LIVE_GATE_BLOCK)


def test_blocking_checks_is_list():
    r = evaluate_aider_live_gate(dry_run=True)
    assert isinstance(r.blocking_checks, list)


def test_live_execution_safe_consistent_with_checks():
    r = evaluate_aider_live_gate(dry_run=True)
    all_passed = all(c.passed for c in r.checks)
    assert r.live_execution_safe == all_passed


def test_overall_result_consistent_with_live_execution_safe():
    r = evaluate_aider_live_gate(dry_run=True)
    if r.live_execution_safe:
        assert r.overall_result == LIVE_GATE_PASS
    else:
        assert r.overall_result == LIVE_GATE_BLOCK


def test_passed_property():
    r = evaluate_aider_live_gate(dry_run=True)
    assert r.passed == (r.overall_result == LIVE_GATE_PASS)


def test_blocking_checks_names_in_checks():
    r = evaluate_aider_live_gate(dry_run=True)
    check_names = {c.check_name for c in r.checks}
    for bc in r.blocking_checks:
        assert bc in check_names


def test_to_dict_schema_version():
    r = evaluate_aider_live_gate(dry_run=True)
    d = r.to_dict()
    assert d["schema_version"] == 1


def test_to_dict_keys():
    r = evaluate_aider_live_gate(dry_run=True)
    d = r.to_dict()
    for k in ("schema_version", "overall_result", "live_execution_safe", "blocking_checks", "checks"):
        assert k in d


def test_json_round_trip():
    r = evaluate_aider_live_gate(dry_run=True)
    text = json.dumps(r.to_dict())
    back = json.loads(text)
    assert back["schema_version"] == 1
    assert len(back["checks"]) == 4


def test_dry_run_no_file(tmp_path):
    r = evaluate_aider_live_gate(artifact_dir=tmp_path / "out", dry_run=True)
    assert r.artifact_path == ""


def test_non_dry_run_writes_file(tmp_path):
    r = evaluate_aider_live_gate(artifact_dir=tmp_path / "out", dry_run=False)
    assert r.artifact_path != ""
    assert Path(r.artifact_path).exists()


def test_init_ok_from_framework():
    from framework import evaluate_aider_live_gate  # noqa: F401
