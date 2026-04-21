"""Seam tests for LACE2-P15-EXPANSION-CLOSEOUT-RATIFIER-SEAM-1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace2_expansion_closeout_ratifier import (
    Lace2ExpansionCloseoutRatifier,
    Lace2CloseoutRecord,
)

VALID_VERDICTS = {
    "lace2_campaign_complete",
    "lace2_campaign_partial",
    "lace2_campaign_inconclusive",
}


def test_import_ratifier():
    assert callable(Lace2ExpansionCloseoutRatifier)


def test_ratify_returns_record():
    r = Lace2ExpansionCloseoutRatifier().ratify()
    assert isinstance(r, Lace2CloseoutRecord)


def test_campaign_verdict_valid():
    r = Lace2ExpansionCloseoutRatifier().ratify()
    assert r.campaign_verdict in VALID_VERDICTS


def test_known_limitations_at_least_six():
    r = Lace2ExpansionCloseoutRatifier().ratify()
    assert len(r.known_limitations) >= 6


def test_what_remains_unproven_at_least_four():
    r = Lace2ExpansionCloseoutRatifier().ratify()
    assert len(r.what_remains_unproven) >= 4


def test_emit_artifact(tmp_path):
    ratifier = Lace2ExpansionCloseoutRatifier()
    r = ratifier.ratify()
    path = ratifier.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["campaign_verdict"] in VALID_VERDICTS
    assert len(data["known_limitations"]) >= 6
    assert len(data["what_remains_unproven"]) >= 4
    assert len(data["what_was_built"]) == 15
    assert data["packets_completed"] == 15
