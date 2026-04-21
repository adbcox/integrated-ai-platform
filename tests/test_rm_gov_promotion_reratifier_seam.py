"""Seam tests for RM-GOV-PROMOTION-RERATIFIER-SEAM-1."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bin.run_rm_gov_promotion_reratifier import run_reratification


def test_import_reratifier():
    from bin.run_rm_gov_promotion_reratifier import run_reratification
    assert callable(run_reratification)


def test_all_complete():
    result = run_reratification()
    assert result["all_complete"] is True
    assert result["overall_status"] == "all_complete"


def test_rm_gov_001_complete():
    result = run_reratification()
    item = result["items"]["RM-GOV-001"]
    assert item["ratifier_decision"] == "complete"
    assert item["blocking"] == []


def test_rm_gov_002_complete():
    result = run_reratification()
    item = result["items"]["RM-GOV-002"]
    assert item["ratifier_decision"] == "complete"
    assert item["blocking"] == []


def test_rm_gov_003_complete():
    result = run_reratification()
    item = result["items"]["RM-GOV-003"]
    assert item["ratifier_decision"] == "complete"
    assert item["blocking"] == []


def test_all_subclaims_evidenced():
    result = run_reratification()
    for item_id, item in result["items"].items():
        assert item["evidenced_count"] == item["total_subclaims"], (
            f"{item_id}: only {item['evidenced_count']}/{item['total_subclaims']} evidenced"
        )
