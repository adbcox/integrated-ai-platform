"""Tests for framework.codex_availability_gate — LAPC1 P5."""
import json
import pytest
from pathlib import Path

from framework.codex_availability_gate import (
    CODEX_GATE_PASS,
    CODEX_GATE_BLOCK,
    CodexAvailabilityCheck,
    CodexAvailabilityReport,
    evaluate_codex_availability,
)


def test_import_ok():
    from framework.codex_availability_gate import evaluate_codex_availability, CodexAvailabilityReport  # noqa: F401


def test_constants():
    assert CODEX_GATE_PASS == "codex_gate_pass"
    assert CODEX_GATE_BLOCK == "codex_gate_block"


def test_returns_report():
    r = evaluate_codex_availability(dry_run=True)
    assert isinstance(r, CodexAvailabilityReport)


def test_exactly_four_checks():
    r = evaluate_codex_availability(dry_run=True)
    assert len(r.checks) == 4


def test_check_names():
    r = evaluate_codex_availability(dry_run=True)
    names = {c.check_name for c in r.checks}
    assert names == {"env_key_present", "policy_optional", "policy_allows_without_key", "defer_candidate_when_no_key"}


def test_codex_available_is_bool():
    r = evaluate_codex_availability(dry_run=True)
    assert isinstance(r.codex_available, bool)


def test_policy_allows_execution_is_bool():
    r = evaluate_codex_availability(dry_run=True)
    assert isinstance(r.policy_allows_execution, bool)


def test_overall_result_valid():
    r = evaluate_codex_availability(dry_run=True)
    assert r.overall_result in (CODEX_GATE_PASS, CODEX_GATE_BLOCK)


def test_passed_property():
    r = evaluate_codex_availability(dry_run=True)
    assert r.passed == (r.overall_result == CODEX_GATE_PASS)


def test_no_env_key_is_blocked():
    # Current test env has no API key
    r = evaluate_codex_availability(dry_run=True)
    # codex_available corresponds to env key presence
    if not r.codex_available:
        assert r.overall_result == CODEX_GATE_BLOCK


def test_blocking_reason_non_empty_when_blocked():
    r = evaluate_codex_availability(dry_run=True)
    if r.overall_result == CODEX_GATE_BLOCK:
        assert len(r.blocking_reason) > 0


def test_to_dict_schema_version():
    r = evaluate_codex_availability(dry_run=True)
    d = r.to_dict()
    assert d["schema_version"] == 1


def test_to_dict_keys():
    r = evaluate_codex_availability(dry_run=True)
    d = r.to_dict()
    for k in ("schema_version", "overall_result", "codex_available", "policy_allows_execution",
              "blocking_reason", "checks"):
        assert k in d


def test_json_round_trip():
    r = evaluate_codex_availability(dry_run=True)
    text = json.dumps(r.to_dict())
    back = json.loads(text)
    assert back["schema_version"] == 1
    assert len(back["checks"]) == 4


def test_dry_run_no_file(tmp_path):
    r = evaluate_codex_availability(artifact_dir=tmp_path / "out", dry_run=True)
    assert r.artifact_path == ""


def test_non_dry_run_writes_file(tmp_path):
    r = evaluate_codex_availability(artifact_dir=tmp_path / "out", dry_run=False)
    assert r.artifact_path != ""
    assert Path(r.artifact_path).exists()


def test_init_ok_from_framework():
    from framework import evaluate_codex_availability  # noqa: F401
