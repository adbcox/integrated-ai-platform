"""Tests for framework.aider_promotion_ratifier — LAPC1 P4."""
import json
import pytest
from pathlib import Path

from framework.aider_live_execution_gate import evaluate_aider_live_gate
from framework.aider_live_proof import run_aider_live_proof
from framework.aider_promotion_ratifier import (
    AIDER_PROMOTION_DONE,
    AIDER_PROMOTION_PARTIAL,
    AiderPromotionArtifact,
    ratify_aider_promotion,
)


def _gate():
    return evaluate_aider_live_gate(dry_run=True)


def _proof(gate):
    return run_aider_live_proof(gate, num_runs=2, dry_run=True)


def test_import_ok():
    from framework.aider_promotion_ratifier import ratify_aider_promotion, AiderPromotionArtifact  # noqa: F401


def test_constants():
    assert AIDER_PROMOTION_DONE == "aider_done"
    assert AIDER_PROMOTION_PARTIAL == "aider_partial"


def test_returns_artifact():
    a = ratify_aider_promotion(dry_run=True)
    assert isinstance(a, AiderPromotionArtifact)


def test_no_inputs_is_partial():
    a = ratify_aider_promotion(dry_run=True)
    assert a.decision == AIDER_PROMOTION_PARTIAL


def test_blocked_gate_is_partial():
    gate = _gate()
    proof = _proof(gate)
    a = ratify_aider_promotion(gate, proof, dry_run=True)
    assert a.decision == AIDER_PROMOTION_PARTIAL


def test_gate_result_propagated():
    gate = _gate()
    a = ratify_aider_promotion(gate, dry_run=True)
    assert a.gate_result == gate.overall_result


def test_live_execution_safe_propagated():
    gate = _gate()
    a = ratify_aider_promotion(gate, dry_run=True)
    assert a.live_execution_safe == gate.live_execution_safe


def test_proof_status_propagated():
    gate = _gate()
    proof = _proof(gate)
    a = ratify_aider_promotion(gate, proof, dry_run=True)
    assert a.proof_status == proof.proof_status


def test_successful_live_runs_propagated():
    gate = _gate()
    proof = _proof(gate)
    a = ratify_aider_promotion(gate, proof, dry_run=True)
    assert a.successful_live_runs == proof.successful_runs


def test_rationale_non_empty():
    a = ratify_aider_promotion(dry_run=True)
    assert len(a.rationale) > 0


def test_to_dict_schema_version():
    a = ratify_aider_promotion(dry_run=True)
    d = a.to_dict()
    assert d["schema_version"] == 1


def test_to_dict_keys():
    a = ratify_aider_promotion(dry_run=True)
    d = a.to_dict()
    for k in ("schema_version", "decision", "rationale", "gate_result", "proof_status",
              "successful_live_runs", "live_execution_safe", "ratified_at"):
        assert k in d


def test_json_round_trip():
    a = ratify_aider_promotion(dry_run=True)
    text = json.dumps(a.to_dict())
    back = json.loads(text)
    assert back["schema_version"] == 1
    assert back["decision"] in (AIDER_PROMOTION_DONE, AIDER_PROMOTION_PARTIAL)


def test_dry_run_no_file(tmp_path):
    a = ratify_aider_promotion(artifact_dir=tmp_path / "out", dry_run=True)
    assert a.artifact_path == ""


def test_non_dry_run_writes_file(tmp_path):
    a = ratify_aider_promotion(artifact_dir=tmp_path / "out", dry_run=False)
    assert a.artifact_path != ""
    assert Path(a.artifact_path).exists()


def test_init_ok_from_framework():
    from framework import ratify_aider_promotion  # noqa: F401
