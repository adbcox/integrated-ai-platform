"""Seam tests for LACE2-P1-EXPANSION-TRANCHE-SELECTOR-SEAM-1."""
from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

SCRIPT = REPO_ROOT / "bin" / "run_lace2_expansion_tranche_selector.py"
ARTIFACT = REPO_ROOT / "artifacts" / "expansion" / "LACE2" / "tranche_selection.json"


def _load_script():
    spec = importlib.util.spec_from_file_location("tranche_selector", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_import_selector():
    mod = _load_script()
    assert hasattr(mod, "main")
    assert callable(mod.main)


def test_collect_shared_touch_callable():
    mod = _load_script()
    assert callable(mod._collect_shared_touch_surfaces)


def test_five_blocks_defined():
    mod = _load_script()
    assert len(mod._CANDIDATE_BLOCKS) == 5


def test_ranking_descending():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    scores = [b["final_score"] for b in data["selected_blocks"]]
    assert scores == sorted(scores, reverse=True) or \
        [b["shared_touch_count"] for b in data["selected_blocks"]] == \
        sorted([b["shared_touch_count"] for b in data["selected_blocks"]], reverse=True)


def test_artifact_written():
    assert ARTIFACT.exists(), f"artifact not found: {ARTIFACT}"
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert data["scoring_method"] == "rm_gov_003_shared_touch_count"
    assert len(data["selected_blocks"]) == 5


def test_lace1_upstream_verdict_field():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert "lace1_upstream_verdict" in data
    assert data["lace1_upstream_verdict"] != ""
