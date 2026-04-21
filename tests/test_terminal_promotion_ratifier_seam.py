"""Tests for framework.terminal_promotion_ratifier — LAPC1 P12."""
import json
import pytest
from pathlib import Path

from framework.aider_live_execution_gate import evaluate_aider_live_gate
from framework.aider_live_proof import run_aider_live_proof
from framework.aider_promotion_ratifier import ratify_aider_promotion
from framework.codex_availability_gate import evaluate_codex_availability
from framework.codex_promotion_ratifier import ratify_codex_promotion
from framework.cmdb_promotion_evidence import evaluate_cmdb_promotion_evidence
from framework.cmdb_promotion_ratifier import ratify_cmdb_promotion
from framework.domain_branch_first_wave_ratifier import ratify_first_wave_promotion
from framework.domain_branch_second_wave_ratifier import ratify_second_wave_promotion
from framework.terminal_promotion_ratifier import (
    TERMINAL_PROMOTION_COMPLETE,
    TERMINAL_PROMOTION_PARTIAL,
    TerminalPromotionRecord,
    TerminalPromotionArtifact,
    ratify_terminal_promotion,
)


def _golden_path():
    gate = evaluate_aider_live_gate(dry_run=True)
    proof = run_aider_live_proof(gate, num_runs=2, dry_run=True)
    avail = evaluate_codex_availability(dry_run=True)
    evidence = evaluate_cmdb_promotion_evidence(dry_run=True)
    return ratify_terminal_promotion(
        aider_artifact=ratify_aider_promotion(gate, proof, dry_run=True),
        codex_artifact=ratify_codex_promotion(avail, dry_run=True),
        cmdb_artifact=ratify_cmdb_promotion(evidence, dry_run=True),
        first_wave_artifact=ratify_first_wave_promotion(dry_run=True),
        second_wave_artifact=ratify_second_wave_promotion(dry_run=True),
        dry_run=True,
    )


def test_import_ok():
    from framework.terminal_promotion_ratifier import ratify_terminal_promotion, TerminalPromotionArtifact  # noqa: F401


def test_constants():
    assert TERMINAL_PROMOTION_COMPLETE == "terminal_promotion_complete"
    assert TERMINAL_PROMOTION_PARTIAL == "terminal_promotion_partial"


def test_returns_artifact():
    a = ratify_terminal_promotion(dry_run=True)
    assert isinstance(a, TerminalPromotionArtifact)


def test_no_inputs_total_count_eight():
    a = ratify_terminal_promotion(dry_run=True)
    assert a.total_count == 8


def test_no_inputs_resolved_count_zero():
    a = ratify_terminal_promotion(dry_run=True)
    assert a.resolved_count == 0


def test_no_inputs_is_partial():
    a = ratify_terminal_promotion(dry_run=True)
    assert a.decision == TERMINAL_PROMOTION_PARTIAL


def test_golden_path_total_count():
    a = _golden_path()
    assert a.total_count == 8


def test_golden_path_resolved_count_seven():
    a = _golden_path()
    assert a.resolved_count == 7


def test_golden_path_is_partial():
    a = _golden_path()
    assert a.decision == TERMINAL_PROMOTION_PARTIAL


def test_golden_path_unresolved_is_aider():
    a = _golden_path()
    assert a.unresolved_items == ["aider_overall"]


def test_golden_path_not_complete():
    a = _golden_path()
    assert a.decision != TERMINAL_PROMOTION_COMPLETE


def test_campaign_id_default():
    a = ratify_terminal_promotion(dry_run=True)
    assert "LAPC1" in a.campaign_id or "PROMOTION" in a.campaign_id


def test_campaign_id_propagated():
    a = ratify_terminal_promotion(campaign_id="TEST-CAMPAIGN", dry_run=True)
    assert a.campaign_id == "TEST-CAMPAIGN"


def test_to_dict_schema_version():
    a = ratify_terminal_promotion(dry_run=True)
    d = a.to_dict()
    assert d["schema_version"] == 1


def test_to_dict_keys():
    a = ratify_terminal_promotion(dry_run=True)
    d = a.to_dict()
    for k in ("schema_version", "campaign_id", "decision", "all_resolved",
              "resolved_count", "total_count", "unresolved_items", "records"):
        assert k in d


def test_json_round_trip():
    a = ratify_terminal_promotion(dry_run=True)
    text = json.dumps(a.to_dict())
    back = json.loads(text)
    assert back["schema_version"] == 1
    assert back["total_count"] == 8


def test_dry_run_no_file(tmp_path):
    a = ratify_terminal_promotion(artifact_dir=tmp_path / "out", dry_run=True)
    assert a.artifact_path == ""


def test_non_dry_run_writes_file(tmp_path):
    a = ratify_terminal_promotion(artifact_dir=tmp_path / "out", dry_run=False)
    assert a.artifact_path != ""
    assert Path(a.artifact_path).exists()


def test_init_ok_from_framework():
    from framework import TerminalPromotionArtifact  # noqa: F401
