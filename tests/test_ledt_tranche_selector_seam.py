"""Seam tests for LEDT-P1-TRANSITION-TRANCHE-SELECTOR-SEAM-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

from roadmap_governance.planner_service import _collect_shared_touch_surfaces
import run_ledt_tranche_selector as sel

VALID_BLOCK_IDS = {
    "FB-EXEC-ELIGIBILITY-AND-PREFLIGHT",
    "FB-ROUTE-DECISION-AND-FALLBACK-GATE",
    "FB-PACKET-ROUTING-METADATA-AND-RECEIPT",
    "FB-PLANNER-PREFERENCE-SCHEMA",
    "FB-AUDIT-PROOF-AND-RATIFICATION",
}


def test_collect_shared_touch_surfaces_callable():
    assert callable(_collect_shared_touch_surfaces)


def test_collect_shared_touch_surfaces_returns_list():
    result = _collect_shared_touch_surfaces(["FB-EXEC-ELIGIBILITY-AND-PREFLIGHT"])
    assert isinstance(result, list)


def test_lace2_closeout_exists():
    p = REPO_ROOT / "artifacts" / "expansion" / "LACE2" / "LACE2_closeout.json"
    assert p.exists(), "LACE2_closeout.json required upstream artifact"


def test_lace2_closeout_verdict():
    p = REPO_ROOT / "artifacts" / "expansion" / "LACE2" / "LACE2_closeout.json"
    d = json.loads(p.read_text())
    assert d.get("campaign_verdict") == "lace2_campaign_complete"


def test_score_blocks_returns_five_ranked():
    scored = sel.score_blocks(sel.TRANSITION_BLOCKS)
    assert len(scored) == 5
    assert all(b["block_id"] in VALID_BLOCK_IDS for b in scored)
    scores = [b["final_score"] for b in scored]
    assert scores == sorted(scores, reverse=True)


def test_tranche_artifact_emitted():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_ledt_tranche_selector.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    p = REPO_ROOT / "artifacts" / "expansion" / "LEDT" / "tranche_selection.json"
    assert p.exists()
    d = json.loads(p.read_text())
    assert d["scoring_method"] == "rm_gov_003_shared_touch_count"
    assert len(d["selected_blocks"]) == 5
    assert d["lace2_upstream_verdict"] == "lace2_campaign_complete"
