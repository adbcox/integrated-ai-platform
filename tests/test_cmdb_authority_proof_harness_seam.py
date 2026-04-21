"""Seam tests for CMDB authority proof harness (CMDB-AUTHORITY-PROOF-HARNESS-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.cmdb_authority_proof_harness import (
    CmdbProofCriterion,
    CmdbProofResult,
    CmdbAuthorityProofHarness,
    emit_cmdb_proof_result,
)
from framework.cmdb_authority_contract import build_cmdb_authority_contract, CmdbServiceRecord
from framework.cmdb_read_model import CmdbReadModel, CmdbReadModelOutput


def _default_run():
    c = build_cmdb_authority_contract()
    m = CmdbReadModel().build(contract=c)
    return CmdbAuthorityProofHarness().run(contract=c, read_model_output=m)


def _empty_output():
    return CmdbReadModelOutput(
        entries=[], total_entries=0, readable_count=0,
        stable_count=0, read_model_complete=True,
        produced_at="2026-01-01T00:00:00+00:00", artifact_path=None,
    )


def test_import_harness():
    assert callable(CmdbAuthorityProofHarness)


def test_run_returns_proof_result():
    r = _default_run()
    assert isinstance(r, CmdbProofResult)


def test_five_criteria_present():
    r = _default_run()
    assert r.criteria_total == 5
    assert len(r.criteria) == 5


def test_criteria_names():
    r = _default_run()
    names = {c.criterion_name for c in r.criteria}
    assert "source_readable" in names
    assert "stable_typed_output" in names
    assert "deterministic_gate" in names
    assert "authority_boundary_correct" in names
    assert "non_overlap_with_manifest" in names


def test_source_readable_passes_when_all_readable():
    r = _default_run()
    c = next(x for x in r.criteria if x.criterion_name == "source_readable")
    assert c.passed is True


def test_source_readable_fails_when_zero_entries():
    c = build_cmdb_authority_contract()
    r = CmdbAuthorityProofHarness().run(contract=c, read_model_output=_empty_output())
    crit = next(x for x in r.criteria if x.criterion_name == "source_readable")
    assert crit.passed is False


def test_stable_typed_output_passes():
    r = _default_run()
    c = next(x for x in r.criteria if x.criterion_name == "stable_typed_output")
    assert c.passed is True


def test_deterministic_gate_passes():
    r = _default_run()
    c = next(x for x in r.criteria if x.criterion_name == "deterministic_gate")
    assert c.passed is True


def test_authority_boundary_correct_passes():
    r = _default_run()
    c = next(x for x in r.criteria if x.criterion_name == "authority_boundary_correct")
    assert c.passed is True


def test_non_overlap_with_manifest_passes():
    r = _default_run()
    c = next(x for x in r.criteria if x.criterion_name == "non_overlap_with_manifest")
    assert c.passed is True


def test_proof_verdict_proven_when_all_pass():
    r = _default_run()
    assert r.proof_verdict == "proven"
    assert r.criteria_passed == 5


def test_proof_verdict_partial_when_one_fails():
    c = build_cmdb_authority_contract()
    r = CmdbAuthorityProofHarness().run(contract=c, read_model_output=_empty_output())
    assert r.proof_verdict in ("partial", "blocked")
    assert r.criteria_passed < 5


def test_proof_verdict_blocked_when_all_entries_zero_and_gate_fails():
    c = build_cmdb_authority_contract()
    with patch("framework.cmdb_authority_proof_harness.evaluate_cmdb_gate", side_effect=RuntimeError("gate error")):
        r = CmdbAuthorityProofHarness().run(contract=c, read_model_output=_empty_output())
    # source_readable fails (0 entries), stable_typed_output fails, deterministic_gate fails
    assert r.criteria_passed <= 2  # only boundary and non-overlap can pass


def test_emit_artifact_written(tmp_path):
    r = _default_run()
    path = emit_cmdb_proof_result(r, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_emit_artifact_parseable(tmp_path):
    r = _default_run()
    path = emit_cmdb_proof_result(r, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "proof_verdict" in data
    assert "criteria" in data
    assert len(data["criteria"]) == 5


def test_package_surface():
    import framework
    assert hasattr(framework, "CmdbAuthorityProofHarness")
    assert hasattr(framework, "CmdbProofResult")
