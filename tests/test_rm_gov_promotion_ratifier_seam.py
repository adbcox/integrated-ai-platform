"""Seam tests for RM-GOV promotion ratifier (RM-GOV-PROMOTION-RATIFIER-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.rm_gov_promotion_ratifier import (
    RmGovItemDecision,
    RmGovPromotionDecision,
    RmGovPromotionRatifier,
    emit_rm_gov_promotion_decision,
)


def _all_evidenced_5():
    return {
        "subclaims": {
            "sub_a": {"evidenced": True, "evidence_source": "path/a"},
            "sub_b": {"evidenced": True, "evidence_source": "path/b"},
            "sub_c": {"evidenced": True, "evidence_source": "path/c"},
            "sub_d": {"evidenced": True, "evidence_source": "path/d"},
            "sub_e": {"evidenced": True, "evidence_source": "path/e"},
        }
    }


def _all_false_5():
    return {
        "subclaims": {
            "sub_a": {"evidenced": False, "evidence_source": None},
            "sub_b": {"evidenced": False, "evidence_source": None},
            "sub_c": {"evidenced": False, "evidence_source": None},
            "sub_d": {"evidenced": False, "evidence_source": None},
            "sub_e": {"evidenced": False, "evidence_source": None},
        }
    }


def _partial_4():
    d = _all_evidenced_5()
    d["subclaims"]["sub_e"]["evidenced"] = False
    d["subclaims"]["sub_e"]["evidence_source"] = None
    return d


def _002_recurrence_false():
    return {
        "subclaims": {
            "integrity_review_capability": {"evidenced": True, "evidence_source": "x"},
            "naming_consistency_checks": {"evidenced": True, "evidence_source": "x"},
            "duplicate_detection": {"evidenced": True, "evidence_source": "x"},
            "mismatch_synchronization_hygiene": {"evidenced": True, "evidence_source": "x"},
            "recurrence": {"evidenced": False, "evidence_source": None},
        }
    }


def _003_both_false():
    return {
        "subclaims": {
            "grouped_feature_block_planning": {"evidenced": False, "evidence_source": None},
            "package_grouping_outputs_machine_readable": {"evidenced": False, "evidence_source": None},
            "shared_touch_loe_optimization": {"evidenced": False, "evidence_source": None},
            "planner_outputs_reusable": {"evidenced": False, "evidence_source": None},
        }
    }


def _003_grouped_false_loe_false_others_true():
    return {
        "subclaims": {
            "grouped_feature_block_planning": {"evidenced": False, "evidence_source": None},
            "package_grouping_outputs_machine_readable": {"evidenced": True, "evidence_source": "x"},
            "shared_touch_loe_optimization": {"evidenced": False, "evidence_source": None},
            "planner_outputs_reusable": {"evidenced": True, "evidence_source": "x"},
        }
    }


def test_import_ratifier():
    assert callable(RmGovPromotionRatifier)


def test_all_evidenced_yields_complete():
    d = RmGovPromotionRatifier().ratify(
        evidence_001=_all_evidenced_5(),
        evidence_002=_all_evidenced_5(),
        evidence_003=_all_evidenced_5(),
    )
    assert d.rm_gov_001.decision == "complete"
    assert d.rm_gov_002.decision == "complete"
    assert d.rm_gov_003.decision == "complete"


def test_zero_evidenced_yields_deferred():
    d = RmGovPromotionRatifier().ratify(
        evidence_001=_all_false_5(),
        evidence_002=_all_false_5(),
        evidence_003=_003_both_false(),
    )
    assert d.rm_gov_001.decision == "deferred"
    assert d.rm_gov_002.decision == "deferred"
    assert d.rm_gov_003.decision == "deferred"


def test_partial_evidenced_yields_partial():
    d = RmGovPromotionRatifier().ratify(
        evidence_001=_partial_4(),
        evidence_002=_partial_4(),
        evidence_003=_003_grouped_false_loe_false_others_true(),
    )
    assert d.rm_gov_001.decision == "partial"
    assert d.rm_gov_002.decision == "partial"


def test_recurrence_false_caps_002_at_partial():
    d = RmGovPromotionRatifier().ratify(
        evidence_001=_all_evidenced_5(),
        evidence_002=_002_recurrence_false(),
        evidence_003=_all_evidenced_5(),
    )
    assert d.rm_gov_002.decision == "partial"


def test_feature_block_false_caps_003_at_partial():
    d = RmGovPromotionRatifier().ratify(
        evidence_001=_all_evidenced_5(),
        evidence_002=_all_evidenced_5(),
        evidence_003=_003_grouped_false_loe_false_others_true(),
    )
    assert d.rm_gov_003.decision in ("partial", "deferred")


def test_blocking_subclaims_populated_when_not_complete():
    d = RmGovPromotionRatifier().ratify(
        evidence_001=_partial_4(),
        evidence_002=_002_recurrence_false(),
        evidence_003=_003_grouped_false_loe_false_others_true(),
    )
    assert len(d.rm_gov_001.blocking_subclaims) >= 1
    assert len(d.rm_gov_002.blocking_subclaims) >= 1


def test_blocking_subclaims_empty_when_complete():
    d = RmGovPromotionRatifier().ratify(
        evidence_001=_all_evidenced_5(),
        evidence_002=_all_evidenced_5(),
        evidence_003=_all_evidenced_5(),
    )
    assert d.rm_gov_001.blocking_subclaims == []
    assert d.rm_gov_002.blocking_subclaims == []
    assert d.rm_gov_003.blocking_subclaims == []


def test_returns_rm_gov_promotion_decision():
    d = RmGovPromotionRatifier().ratify(
        evidence_001=_all_evidenced_5(),
        evidence_002=_all_evidenced_5(),
        evidence_003=_all_evidenced_5(),
    )
    assert isinstance(d, RmGovPromotionDecision)
    assert isinstance(d.rm_gov_001, RmGovItemDecision)


def test_package_surface():
    import framework
    assert hasattr(framework, "RmGovPromotionRatifier")
    assert hasattr(framework, "RmGovPromotionDecision")
