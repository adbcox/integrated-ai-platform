"""Seam tests for LACE1-P13-GROUPED-PACKAGE-EXPANSION-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.grouped_package_expansion_selector import (
    GroupedPackageExpansionSelector,
    GroupedPackageSelectionRecord,
    PackageCandidate,
)

_VALID_PACKAGE_IDS = {
    "MT-RETRIEVAL-ENRICHMENT",
    "MT-DECOMP-HANDOFF-WIRING",
    "MT-TRACE-REPLAY-WIRING",
}


def test_import_selector():
    from framework.grouped_package_expansion_selector import GroupedPackageExpansionSelector
    assert callable(GroupedPackageExpansionSelector)


def test_select_returns_record():
    r = GroupedPackageExpansionSelector().select()
    assert isinstance(r, GroupedPackageSelectionRecord)


def test_selected_package_is_valid():
    r = GroupedPackageExpansionSelector().select()
    assert r.selected_package_id in _VALID_PACKAGE_IDS


def test_scoring_method_is_rm_gov_003():
    r = GroupedPackageExpansionSelector().select()
    assert r.scoring_method == "rm_gov_003_shared_touch_count"


def test_all_candidates_present():
    r = GroupedPackageExpansionSelector().select()
    assert len(r.candidates) == 3
    ids = {c.package_id for c in r.candidates}
    assert ids == _VALID_PACKAGE_IDS


def test_emit_writes_json(tmp_path):
    selector = GroupedPackageExpansionSelector()
    r = selector.select()
    path = selector.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "selected_package_id" in data
    assert data["scoring_method"] == "rm_gov_003_shared_touch_count"
    assert len(data["candidates"]) == 3
