"""Seam tests for LEDT-P12-TRANSITION-CLOSEOUT-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.ledt_expansion_closeout_ratifier import LEDTExpansionCloseoutRatifier, LEDTCloseoutRecord

VALID_VERDICTS = {
    "ledt_campaign_complete",
    "ledt_campaign_partial",
    "ledt_campaign_inconclusive",
}

def test_import_ratifier():
    assert callable(LEDTExpansionCloseoutRatifier)

def test_ratify_returns_record():
    r = LEDTExpansionCloseoutRatifier().ratify()
    assert isinstance(r, LEDTCloseoutRecord)

def test_campaign_verdict_valid():
    r = LEDTExpansionCloseoutRatifier().ratify()
    assert r.campaign_verdict in VALID_VERDICTS

def test_known_limitations_at_least_six():
    r = LEDTExpansionCloseoutRatifier().ratify()
    assert len(r.known_limitations) >= 6

def test_what_remains_unproven_at_least_four():
    r = LEDTExpansionCloseoutRatifier().ratify()
    assert len(r.what_remains_unproven) >= 4

def test_emit_artifact(tmp_path):
    ratifier = LEDTExpansionCloseoutRatifier()
    r = ratifier.ratify()
    path = ratifier.emit(r, tmp_path)
    d = json.loads(Path(path).read_text())
    assert d["campaign_verdict"] in VALID_VERDICTS
    assert len(d["what_was_built"]) == 12
    assert len(d["known_limitations"]) >= 6
    assert len(d["what_remains_unproven"]) >= 4
    assert len(d["when_claude_execution_allowed"]) >= 3
    assert len(d["what_changed_operationally"]) >= 4
    assert d["packets_completed"] == 12
