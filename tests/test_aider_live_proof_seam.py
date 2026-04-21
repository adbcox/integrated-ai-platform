"""Tests for framework.aider_live_proof — LAPC1 P3."""
import json
import pytest
from pathlib import Path

from framework.aider_live_execution_gate import evaluate_aider_live_gate, LIVE_GATE_BLOCK
from framework.aider_live_proof import (
    PROOF_STATUS_LIVE_PROVEN,
    PROOF_STATUS_DRY_RUN_ONLY,
    PROOF_STATUS_BLOCKED,
    AiderLiveProofRecord,
    AiderLiveProofReport,
    run_aider_live_proof,
)


def _gate():
    return evaluate_aider_live_gate(dry_run=True)


def test_import_ok():
    from framework.aider_live_proof import run_aider_live_proof, AiderLiveProofReport  # noqa: F401


def test_constants():
    assert PROOF_STATUS_LIVE_PROVEN == "live_proven"
    assert PROOF_STATUS_DRY_RUN_ONLY == "dry_run_only"
    assert PROOF_STATUS_BLOCKED == "blocked"


def test_returns_report():
    r = run_aider_live_proof(_gate(), num_runs=2, dry_run=True)
    assert isinstance(r, AiderLiveProofReport)


def test_num_runs_respected():
    r = run_aider_live_proof(_gate(), num_runs=3, dry_run=True)
    assert r.total_runs == 3
    assert len(r.records) == 3


def test_num_runs_one():
    r = run_aider_live_proof(_gate(), num_runs=1, dry_run=True)
    assert r.total_runs == 1
    assert len(r.records) == 1


def test_proof_status_valid():
    r = run_aider_live_proof(_gate(), num_runs=2, dry_run=True)
    assert r.proof_status in (PROOF_STATUS_LIVE_PROVEN, PROOF_STATUS_DRY_RUN_ONLY, PROOF_STATUS_BLOCKED)


def test_gate_blocked_means_blocked_status():
    gate = _gate()
    # Current env has aider not registered, so gate is blocked
    if not gate.live_execution_safe:
        r = run_aider_live_proof(gate, num_runs=2, dry_run=True)
        assert r.proof_status == PROOF_STATUS_BLOCKED


def test_gate_blocked_no_live_attempts():
    gate = _gate()
    if not gate.live_execution_safe:
        r = run_aider_live_proof(gate, num_runs=3, dry_run=True)
        for rec in r.records:
            assert rec.attempted_live is False


def test_gate_blocked_all_dry_run():
    gate = _gate()
    if not gate.live_execution_safe:
        r = run_aider_live_proof(gate, num_runs=3, dry_run=True)
        for rec in r.records:
            assert rec.dry_run_used is True


def test_gate_result_propagated():
    gate = _gate()
    r = run_aider_live_proof(gate, num_runs=2, dry_run=True)
    assert r.gate_result == gate.overall_result


def test_live_execution_safe_propagated():
    gate = _gate()
    r = run_aider_live_proof(gate, num_runs=2, dry_run=True)
    assert r.live_execution_safe == gate.live_execution_safe


def test_successful_runs_is_int():
    r = run_aider_live_proof(_gate(), num_runs=2, dry_run=True)
    assert isinstance(r.successful_runs, int)


def test_notes_non_empty():
    r = run_aider_live_proof(_gate(), num_runs=2, dry_run=True)
    assert len(r.notes) > 0


def test_to_dict_schema_version():
    r = run_aider_live_proof(_gate(), num_runs=2, dry_run=True)
    d = r.to_dict()
    assert d["schema_version"] == 1


def test_to_dict_keys():
    r = run_aider_live_proof(_gate(), num_runs=2, dry_run=True)
    d = r.to_dict()
    for k in ("schema_version", "proof_status", "total_runs", "successful_runs", "records"):
        assert k in d


def test_json_round_trip():
    r = run_aider_live_proof(_gate(), num_runs=2, dry_run=True)
    text = json.dumps(r.to_dict())
    back = json.loads(text)
    assert back["schema_version"] == 1
    assert len(back["records"]) == 2


def test_dry_run_no_file(tmp_path):
    r = run_aider_live_proof(_gate(), num_runs=1, artifact_dir=tmp_path / "out", dry_run=True)
    assert r.artifact_path == ""


def test_non_dry_run_writes_file(tmp_path):
    r = run_aider_live_proof(_gate(), num_runs=1, artifact_dir=tmp_path / "out", dry_run=False)
    assert r.artifact_path != ""
    assert Path(r.artifact_path).exists()


def test_init_ok_from_framework():
    from framework import run_aider_live_proof  # noqa: F401
