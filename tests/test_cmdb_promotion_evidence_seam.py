"""Tests for framework.cmdb_promotion_evidence — LAPC1 P7."""
import json
import pytest
from pathlib import Path

from framework.cmdb_promotion_evidence import (
    CMDB_PROOF_SUFFICIENT,
    CMDB_PROOF_INSUFFICIENT,
    CMDB_PROOF_CRITERIA,
    CmdbProofCriterionResult,
    CmdbEvidenceReport,
    evaluate_cmdb_promotion_evidence,
)


def test_import_ok():
    from framework.cmdb_promotion_evidence import evaluate_cmdb_promotion_evidence, CmdbEvidenceReport  # noqa: F401


def test_constants():
    assert CMDB_PROOF_SUFFICIENT == "cmdb_proof_sufficient"
    assert CMDB_PROOF_INSUFFICIENT == "cmdb_proof_insufficient"


def test_criteria_tuple_length():
    assert len(CMDB_PROOF_CRITERIA) == 5


def test_criteria_names():
    assert set(CMDB_PROOF_CRITERIA) == {
        "current_phase_json_readable",
        "authority_record_non_default",
        "gate_evaluates_no_class",
        "gate_blocks_invalid_class",
        "gate_passes_permitted_class",
    }


def test_returns_report():
    r = evaluate_cmdb_promotion_evidence(dry_run=True)
    assert isinstance(r, CmdbEvidenceReport)


def test_criteria_total_is_five():
    r = evaluate_cmdb_promotion_evidence(dry_run=True)
    assert r.criteria_total == 5


def test_exactly_five_results():
    r = evaluate_cmdb_promotion_evidence(dry_run=True)
    assert len(r.criterion_results) == 5


def test_criterion_names_match():
    r = evaluate_cmdb_promotion_evidence(dry_run=True)
    names = {cr.criterion for cr in r.criterion_results}
    assert names == set(CMDB_PROOF_CRITERIA)


def test_all_criteria_pass():
    r = evaluate_cmdb_promotion_evidence(dry_run=True)
    assert r.criteria_passed == 5


def test_overall_result_sufficient():
    r = evaluate_cmdb_promotion_evidence(dry_run=True)
    assert r.overall_result == CMDB_PROOF_SUFFICIENT


def test_observed_non_empty():
    r = evaluate_cmdb_promotion_evidence(dry_run=True)
    for cr in r.criterion_results:
        assert len(cr.observed) > 0, f"{cr.criterion} has empty observed"


def test_to_dict_schema_version():
    r = evaluate_cmdb_promotion_evidence(dry_run=True)
    d = r.to_dict()
    assert d["schema_version"] == 1


def test_to_dict_keys():
    r = evaluate_cmdb_promotion_evidence(dry_run=True)
    d = r.to_dict()
    for k in ("schema_version", "overall_result", "criteria_passed", "criteria_total", "criterion_results"):
        assert k in d


def test_json_round_trip():
    r = evaluate_cmdb_promotion_evidence(dry_run=True)
    text = json.dumps(r.to_dict())
    back = json.loads(text)
    assert back["schema_version"] == 1
    assert back["criteria_total"] == 5


def test_dry_run_no_file(tmp_path):
    r = evaluate_cmdb_promotion_evidence(artifact_dir=tmp_path / "out", dry_run=True)
    assert r.artifact_path == ""


def test_non_dry_run_writes_file(tmp_path):
    r = evaluate_cmdb_promotion_evidence(artifact_dir=tmp_path / "out", dry_run=False)
    assert r.artifact_path != ""
    assert Path(r.artifact_path).exists()


def test_init_ok_from_framework():
    from framework import evaluate_cmdb_promotion_evidence  # noqa: F401
