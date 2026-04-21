"""Seam tests for LEDT-P11-TRANSITION-RATIFIER-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.ledt_transition_ratifier import LEDTTransitionRatifier, LEDTTransitionRatificationRecord

VALID_VERDICTS = {
    "local_exec_default_confirmed",
    "partial_local_exec_default",
    "local_exec_default_not_confirmed",
}

def test_import_ratifier():
    assert callable(LEDTTransitionRatifier)

def test_ratify_returns_record():
    r = LEDTTransitionRatifier().ratify()
    assert isinstance(r, LEDTTransitionRatificationRecord)

def test_five_criteria():
    r = LEDTTransitionRatifier().ratify()
    assert r.criteria_total == 5
    assert len(r.criteria) == 5

def test_verdict_valid():
    r = LEDTTransitionRatifier().ratify()
    assert r.verdict in VALID_VERDICTS

def test_limitations_at_least_four():
    r = LEDTTransitionRatifier().ratify()
    assert len(r.limitations) >= 4

def test_emit_artifact(tmp_path):
    ratifier = LEDTTransitionRatifier()
    r = ratifier.ratify()
    path = ratifier.emit(r, tmp_path)
    d = json.loads(Path(path).read_text())
    assert d["criteria_total"] == 5
    assert d["verdict"] in VALID_VERDICTS
    assert len(d["limitations"]) >= 4
