"""Seam tests for RM-GOV terminal closeout (RM-GOV-TERMINAL-CLOSEOUT-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.rm_gov_terminal_closeout import (
    RmGovCloseoutEntry,
    RmGovTerminalCloseout,
    RmGovTerminalCloseoutEmitter,
    emit_rm_gov_terminal_closeout,
)


def _sample_promotion_decision(dec_001="partial", dec_002="complete", dec_003="partial"):
    return {
        "items": {
            "RM-GOV-001": {
                "item_id": "RM-GOV-001",
                "decision": dec_001,
                "subclaims": [
                    {"subclaim_name": "roadmap_to_development_tracking", "evidenced": False},
                    {"subclaim_name": "cmdb_linkage", "evidenced": True},
                    {"subclaim_name": "standardized_metrics", "evidenced": True},
                    {"subclaim_name": "enforced_naming", "evidenced": True},
                    {"subclaim_name": "impact_transparency", "evidenced": True},
                ],
                "decided_at": "2026-04-21T00:00:00+00:00",
            },
            "RM-GOV-002": {
                "item_id": "RM-GOV-002",
                "decision": dec_002,
                "subclaims": [
                    {"subclaim_name": "integrity_review_capability", "evidenced": True},
                    {"subclaim_name": "naming_consistency_checks", "evidenced": True},
                    {"subclaim_name": "duplicate_detection", "evidenced": True},
                    {"subclaim_name": "mismatch_synchronization_hygiene", "evidenced": True},
                    {"subclaim_name": "recurrence", "evidenced": True},
                ],
                "decided_at": "2026-04-21T00:00:00+00:00",
            },
            "RM-GOV-003": {
                "item_id": "RM-GOV-003",
                "decision": dec_003,
                "subclaims": [
                    {"subclaim_name": "grouped_feature_block_planning", "evidenced": True},
                    {"subclaim_name": "package_grouping_outputs_machine_readable", "evidenced": True},
                    {"subclaim_name": "shared_touch_loe_optimization", "evidenced": False},
                    {"subclaim_name": "planner_outputs_reusable", "evidenced": True},
                ],
                "decided_at": "2026-04-21T00:00:00+00:00",
            },
        }
    }


def test_import_closeout_emitter():
    assert callable(RmGovTerminalCloseoutEmitter)


def test_close_returns_terminal_closeout():
    c = RmGovTerminalCloseoutEmitter().close(promotion_decision=_sample_promotion_decision())
    assert isinstance(c, RmGovTerminalCloseout)


def test_items_count_three():
    c = RmGovTerminalCloseoutEmitter().close(promotion_decision=_sample_promotion_decision())
    assert len(c.items) == 3


def test_complete_maps_to_complete_vs_resolved():
    c = RmGovTerminalCloseoutEmitter().close(
        promotion_decision=_sample_promotion_decision(dec_002="complete")
    )
    entry_002 = next(e for e in c.items if e.item_id == "RM-GOV-002")
    assert entry_002.complete_vs_resolved == "complete"


def test_partial_maps_to_resolved_not_complete():
    c = RmGovTerminalCloseoutEmitter().close(
        promotion_decision=_sample_promotion_decision(dec_001="partial")
    )
    entry_001 = next(e for e in c.items if e.item_id == "RM-GOV-001")
    assert entry_001.complete_vs_resolved == "resolved_not_complete"


def test_deferred_maps_to_deferred():
    c = RmGovTerminalCloseoutEmitter().close(
        promotion_decision=_sample_promotion_decision(dec_003="deferred")
    )
    entry_003 = next(e for e in c.items if e.item_id == "RM-GOV-003")
    assert entry_003.complete_vs_resolved == "deferred"


def test_partial_has_blocker_summary():
    c = RmGovTerminalCloseoutEmitter().close(promotion_decision=_sample_promotion_decision())
    for entry in c.items:
        if entry.decision != "complete":
            assert entry.blocker_summary is not None and len(entry.blocker_summary) > 0, (
                f"{entry.item_id} is {entry.decision} but has empty blocker_summary"
            )


def test_evidence_summary_not_empty():
    c = RmGovTerminalCloseoutEmitter().close(promotion_decision=_sample_promotion_decision())
    for entry in c.items:
        assert len(entry.evidence_summary) > 0, f"{entry.item_id} has empty evidence_summary"


def test_emit_artifact_written(tmp_path):
    pd = _sample_promotion_decision()
    c = RmGovTerminalCloseoutEmitter().close(promotion_decision=pd)
    path = emit_rm_gov_terminal_closeout(c, artifact_dir=tmp_path)
    assert Path(path).exists()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert len(data["items"]) == 3
    assert "overall_status" in data


def test_package_surface():
    import framework
    assert hasattr(framework, "RmGovTerminalCloseoutEmitter")
    assert hasattr(framework, "RmGovTerminalCloseout")
