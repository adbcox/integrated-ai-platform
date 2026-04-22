# version: 2026-04-22
"""Seam tests for LACE2-P13-GROUPED-MINI-TRANCHE-SELECTOR-SEAM-1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace2_grouped_package_selector import (
    Lace2GroupedPackageSelector,
    Lace2GroupedPackageSelection,
    CandidateScore,
)

VALID_TRANCHES = {
    "MT2-RETRY-LOOP-WIRING",
    "MT2-RETRIEVAL-STAGE4-WIRING",
    "MT2-TRACE-REPLAY-PIPELINE",
}


def test_import_selector():
    assert callable(Lace2GroupedPackageSelector)


def test_select_returns_record():
    r = Lace2GroupedPackageSelector().select()
    assert isinstance(r, Lace2GroupedPackageSelection)


def test_three_candidates():
    r = Lace2GroupedPackageSelector().select()
    assert len(r.candidates) == 3


def test_one_winner():
    r = Lace2GroupedPackageSelector().select()
    assert r.selected_tranche in VALID_TRANCHES


def test_winner_is_highest_score():
    r = Lace2GroupedPackageSelector().select()
    winner_score = next(c.final_score for c in r.candidates if c.tranche_id == r.selected_tranche)
    for c in r.candidates:
        assert c.final_score <= winner_score


def test_emit_artifact(tmp_path):
    selector = Lace2GroupedPackageSelector()
    r = selector.select()
    path = selector.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "selected_tranche" in data
    assert data["selected_tranche"] in VALID_TRANCHES
    assert len(data["candidates"]) == 3
