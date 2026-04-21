"""Seam tests for RM-GOV-TERMINAL-CLOSEOUT-RERATIFIER-SEAM-1."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bin.run_rm_gov_terminal_closeout_reratifier import run_closeout_reratification

_CLOSEOUT = REPO_ROOT / "governance" / "rm_gov_closeout.json"


def test_import_reratifier():
    from bin.run_rm_gov_terminal_closeout_reratifier import run_closeout_reratification
    assert callable(run_closeout_reratification)


def test_overall_status_all_complete():
    result = run_closeout_reratification()
    assert result["overall_status"] == "all_complete"
    assert result["all_complete"] is True


def test_all_items_complete():
    result = run_closeout_reratification()
    for item_id, item in result["items"].items():
        assert item["decision"] == "complete", f"{item_id} is not complete"
        assert item["complete_vs_resolved"] == "complete"


def test_no_unevidenced_subclaims():
    result = run_closeout_reratification()
    for item_id, item in result["items"].items():
        assert item["unevidenced_subclaims"] == [], (
            f"{item_id} has unevidenced: {item['unevidenced_subclaims']}"
        )


def test_closeout_json_written():
    run_closeout_reratification()
    assert _CLOSEOUT.exists()
    data = json.loads(_CLOSEOUT.read_text(encoding="utf-8"))
    assert data["overall_status"] == "all_complete"
    assert len(data["items"]) == 3


def test_closeout_json_campaign_id():
    run_closeout_reratification()
    data = json.loads(_CLOSEOUT.read_text(encoding="utf-8"))
    assert data["campaign_id"] == "RM-GOV-CLOSEOUT-GAPS-1"
