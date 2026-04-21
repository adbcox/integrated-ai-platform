"""Seam tests for LEDT-P8-PLANNER-PREFERENCE-SCHEMA-SEAM-1."""
from __future__ import annotations
import json, sys
import pytest
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.planner_preference_schema import PlannerPreferenceBuilder, PlannerPreferenceRecord

def _base():
    return PlannerPreferenceBuilder().build("TEST", "LACE2 evidence", ["LACE2_closeout.json"])

def test_import_builder():
    assert callable(PlannerPreferenceBuilder)

def test_build_returns_record():
    r = _base()
    assert isinstance(r, PlannerPreferenceRecord)

def test_default_executor_local_first():
    r = _base()
    assert r.default_executor_preference == "local_first"
    assert r.claude_execution_allowed is False

def test_claude_allowed_requires_conditions():
    with pytest.raises(ValueError, match="claude_execution_conditions"):
        PlannerPreferenceBuilder().build("TEST", "rationale", ["ev1"], claude_allowed=True)

def test_upstream_evidence_required():
    with pytest.raises(ValueError, match="upstream_evidence_ids"):
        PlannerPreferenceBuilder().build("TEST", "rationale", [])

def test_emit_batch_local_first_rate(tmp_path):
    b = PlannerPreferenceBuilder()
    r1 = b.build("C1", "ev", ["ev1"])
    r2 = b.build("C2", "ev", ["ev1"], claude_allowed=True, claude_conditions=["unavailable"])
    path = b.emit_batch([r1, r2], tmp_path)
    d = json.loads(Path(path).read_text())
    assert d["local_first_rate"] == 1.0
    assert all(r["default_executor_preference"] == "local_first" for r in d["records"])
    claude_recs = [r for r in d["records"] if r["claude_execution_allowed"]]
    assert all(r["claude_execution_conditions"] for r in claude_recs)
