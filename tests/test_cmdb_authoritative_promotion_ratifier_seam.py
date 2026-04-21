"""Seam tests for CMDB authoritative promotion ratifier (CMDB-AUTHORITATIVE-PROMOTION-RATIFIER-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.cmdb_authoritative_promotion_ratifier import (
    CmdbRatificationCriterion,
    CmdbAuthoritativePromotionDecision,
    CmdbAuthoritativePromotionRatifier,
    emit_cmdb_authoritative_promotion_decision,
)


def _all_pass():
    return {
        "proof_result": {"proof_verdict": "proven"},
        "read_model_output": {"read_model_complete": True},
        "operating_context": {"context_complete": True},
        "authority_boundary": {"overlap_violations": []},
    }


def _with(**overrides):
    d = _all_pass()
    d.update(overrides)
    return d


def test_import_ratifier():
    assert callable(CmdbAuthoritativePromotionRatifier)


def test_all_pass_yields_cmdb_done():
    d = CmdbAuthoritativePromotionRatifier().ratify(**_all_pass())
    assert d.decision == "cmdb_done"


def test_proof_not_proven_yields_deferred():
    args = _with(proof_result={"proof_verdict": "partial"})
    d = CmdbAuthoritativePromotionRatifier().ratify(**args)
    assert d.decision == "cmdb_deferred"


def test_read_model_incomplete_yields_deferred():
    args = _with(read_model_output={"read_model_complete": False})
    d = CmdbAuthoritativePromotionRatifier().ratify(**args)
    assert d.decision == "cmdb_deferred"


def test_operating_context_incomplete_yields_deferred():
    args = _with(operating_context={"context_complete": False})
    d = CmdbAuthoritativePromotionRatifier().ratify(**args)
    assert d.decision == "cmdb_deferred"


def test_boundary_overlap_yields_deferred():
    args = _with(authority_boundary={"overlap_violations": ["some_overlap"]})
    d = CmdbAuthoritativePromotionRatifier().ratify(**args)
    assert d.decision == "cmdb_deferred"


def test_four_criteria_present():
    d = CmdbAuthoritativePromotionRatifier().ratify(**_all_pass())
    assert d.criteria_total == 4
    assert len(d.criteria) == 4


def test_criteria_names():
    d = CmdbAuthoritativePromotionRatifier().ratify(**_all_pass())
    names = {c.criterion_name for c in d.criteria}
    assert "proof_verdict_proven" in names
    assert "read_model_complete" in names
    assert "operating_context_complete" in names
    assert "boundary_no_overlap" in names


def test_blocking_reasons_populated_when_deferred():
    args = _with(proof_result={"proof_verdict": "blocked"})
    d = CmdbAuthoritativePromotionRatifier().ratify(**args)
    assert d.decision == "cmdb_deferred"
    assert len(d.blocking_reasons) >= 1


def test_blocking_reasons_empty_when_done():
    d = CmdbAuthoritativePromotionRatifier().ratify(**_all_pass())
    assert d.blocking_reasons == []


def test_decision_from_actual_artifacts():
    artifact_dir = Path("artifacts/cmdb_authoritative_adoption")
    p = json.loads((artifact_dir / "proof_harness_result.json").read_text())
    r = json.loads((artifact_dir / "read_model_output.json").read_text())
    o = json.loads((artifact_dir / "operating_context.json").read_text())
    b = json.loads((artifact_dir / "authority_boundary.json").read_text())
    d = CmdbAuthoritativePromotionRatifier().ratify(
        proof_result=p, read_model_output=r, operating_context=o, authority_boundary=b
    )
    assert d.decision in ("cmdb_done", "cmdb_deferred")


def test_emit_artifact_written(tmp_path):
    d = CmdbAuthoritativePromotionRatifier().ratify(**_all_pass())
    path = emit_cmdb_authoritative_promotion_decision(d, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_emit_artifact_parseable(tmp_path):
    d = CmdbAuthoritativePromotionRatifier().ratify(**_all_pass())
    path = emit_cmdb_authoritative_promotion_decision(d, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "decision" in data
    assert data["decision"] in ("cmdb_done", "cmdb_deferred")
    assert "criteria_total" in data


def test_package_surface():
    import framework
    assert hasattr(framework, "CmdbAuthoritativePromotionRatifier")
    assert hasattr(framework, "CmdbAuthoritativePromotionDecision")
