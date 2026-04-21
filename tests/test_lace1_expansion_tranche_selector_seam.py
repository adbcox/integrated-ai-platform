"""Seam tests for LACE1-P1-EXPANSION-TRANCHE-SELECTOR-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bin.run_lace1_expansion_tranche_selector import run_selection, emit_selection


def test_import_selector():
    from bin.run_lace1_expansion_tranche_selector import run_selection
    assert callable(run_selection)


def test_selection_has_five_blocks():
    result = run_selection()
    assert len(result["selected_blocks"]) == 5


def test_scoring_method():
    result = run_selection()
    assert result["scoring_method"] == "rm_gov_003_shared_touch_count"


def test_all_blocks_have_required_keys():
    result = run_selection()
    for block in result["selected_blocks"]:
        assert "block_id" in block
        assert "shared_touch_count" in block
        assert "packets" in block
        assert isinstance(block["packets"], list)


def test_ranked_by_shared_touch_count():
    result = run_selection()
    counts = [b["shared_touch_count"] for b in result["selected_blocks"]]
    assert counts == sorted(counts, reverse=True)


def test_emit_artifact_written(tmp_path):
    result = run_selection()
    path = emit_selection(result, artifact_dir=tmp_path)
    assert Path(path).exists()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["scoring_method"] == "rm_gov_003_shared_touch_count"
    assert len(data["selected_blocks"]) == 5
