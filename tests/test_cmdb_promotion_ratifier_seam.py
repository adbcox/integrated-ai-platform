"""Tests for framework.cmdb_promotion_ratifier — LAPC1 P8."""
import json
import pytest
from pathlib import Path

from framework.cmdb_promotion_evidence import evaluate_cmdb_promotion_evidence
from framework.cmdb_promotion_ratifier import (
    CMDB_PROMOTION_DONE,
    CMDB_PROMOTION_DEFERRED,
    CmdbPromotionArtifact,
    ratify_cmdb_promotion,
)


def _evidence():
    return evaluate_cmdb_promotion_evidence(dry_run=True)


def test_import_ok():
    from framework.cmdb_promotion_ratifier import ratify_cmdb_promotion, CmdbPromotionArtifact  # noqa: F401


def test_constants():
    assert CMDB_PROMOTION_DONE == "cmdb_done"
    assert CMDB_PROMOTION_DEFERRED == "cmdb_deferred"


def test_returns_artifact():
    a = ratify_cmdb_promotion(dry_run=True)
    assert isinstance(a, CmdbPromotionArtifact)


def test_no_inputs_is_deferred():
    a = ratify_cmdb_promotion(dry_run=True)
    assert a.decision == CMDB_PROMOTION_DEFERRED


def test_all_criteria_pass_is_done():
    ev = _evidence()
    a = ratify_cmdb_promotion(ev, dry_run=True)
    # Current env has all 5 criteria passing
    if ev.criteria_passed == 5:
        assert a.decision == CMDB_PROMOTION_DONE


def test_criteria_passed_propagated():
    ev = _evidence()
    a = ratify_cmdb_promotion(ev, dry_run=True)
    assert a.criteria_passed == ev.criteria_passed


def test_criteria_total_propagated():
    ev = _evidence()
    a = ratify_cmdb_promotion(ev, dry_run=True)
    assert a.criteria_total == ev.criteria_total


def test_evidence_result_propagated():
    ev = _evidence()
    a = ratify_cmdb_promotion(ev, dry_run=True)
    assert a.evidence_result == ev.overall_result


def test_rationale_non_empty():
    a = ratify_cmdb_promotion(dry_run=True)
    assert len(a.rationale) > 0


def test_rationale_mentions_count():
    a = ratify_cmdb_promotion(dry_run=True)
    assert "0" in a.rationale or "5" in a.rationale


def test_to_dict_schema_version():
    a = ratify_cmdb_promotion(dry_run=True)
    d = a.to_dict()
    assert d["schema_version"] == 1


def test_to_dict_keys():
    a = ratify_cmdb_promotion(dry_run=True)
    d = a.to_dict()
    for k in ("schema_version", "decision", "rationale", "criteria_passed", "criteria_total",
              "evidence_result", "ratified_at"):
        assert k in d


def test_json_round_trip():
    a = ratify_cmdb_promotion(dry_run=True)
    text = json.dumps(a.to_dict())
    back = json.loads(text)
    assert back["schema_version"] == 1
    assert back["decision"] in (CMDB_PROMOTION_DONE, CMDB_PROMOTION_DEFERRED)


def test_dry_run_no_file(tmp_path):
    a = ratify_cmdb_promotion(artifact_dir=tmp_path / "out", dry_run=True)
    assert a.artifact_path == ""


def test_non_dry_run_writes_file(tmp_path):
    a = ratify_cmdb_promotion(artifact_dir=tmp_path / "out", dry_run=False)
    assert a.artifact_path != ""
    assert Path(a.artifact_path).exists()


def test_init_ok_from_framework():
    from framework import ratify_cmdb_promotion  # noqa: F401
