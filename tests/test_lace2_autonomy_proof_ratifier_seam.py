"""Seam tests for LACE2-P12-LOCAL-AUTONOMY-PROOF-RATIFIER-SEAM-1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace2_autonomy_proof_ratifier import (
    Lace2AutonomyProofRatifier,
    Lace2RatificationRecord,
    CriterionResult,
)

VALID_VERDICTS = {
    "real_local_autonomy_uplift_confirmed",
    "partial_real_local_autonomy_uplift",
    "real_local_autonomy_uplift_not_confirmed",
}


def test_import_ratifier():
    assert callable(Lace2AutonomyProofRatifier)


def test_ratify_returns_record():
    r = Lace2AutonomyProofRatifier().ratify()
    assert isinstance(r, Lace2RatificationRecord)


def test_five_criteria():
    r = Lace2AutonomyProofRatifier().ratify()
    assert r.criteria_total == 5
    assert len(r.criteria) == 5


def test_verdict_valid():
    r = Lace2AutonomyProofRatifier().ratify()
    assert r.verdict in VALID_VERDICTS


def test_limitations_at_least_four():
    r = Lace2AutonomyProofRatifier().ratify()
    assert len(r.limitations) >= 4


def test_emit_artifact(tmp_path):
    ratifier = Lace2AutonomyProofRatifier()
    r = ratifier.ratify()
    path = ratifier.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "verdict" in data
    assert data["criteria_total"] == 5
    assert len(data["limitations"]) >= 4
    assert data["verdict"] in VALID_VERDICTS
