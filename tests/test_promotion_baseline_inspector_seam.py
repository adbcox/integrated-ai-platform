"""Tests for framework.promotion_baseline_inspector — LAPC1 P1."""
import json
import pytest
from pathlib import Path

from framework.promotion_baseline_inspector import (
    BLOCKER_CLASS_HARD,
    BLOCKER_CLASS_SOFT,
    BLOCKER_CLASS_NONE,
    CURRENT_STATE_PARTIAL,
    CURRENT_STATE_DEFERRED,
    CURRENT_STATE_SEED_COMPLETE,
    CURRENT_STATE_DONE,
    PromotionCandidate,
    PromotionBaselineReport,
    inspect_promotion_baseline,
)


def test_import_ok():
    from framework.promotion_baseline_inspector import inspect_promotion_baseline, PromotionBaselineReport  # noqa: F401


def test_constants():
    assert BLOCKER_CLASS_HARD == "hard"
    assert BLOCKER_CLASS_SOFT == "soft"
    assert BLOCKER_CLASS_NONE == "none"
    assert CURRENT_STATE_PARTIAL == "partial"
    assert CURRENT_STATE_DEFERRED == "deferred"
    assert CURRENT_STATE_SEED_COMPLETE == "seed_complete"
    assert CURRENT_STATE_DONE == "done"


def test_returns_report():
    r = inspect_promotion_baseline(dry_run=True)
    assert isinstance(r, PromotionBaselineReport)


def test_total_candidates_is_eight():
    r = inspect_promotion_baseline(dry_run=True)
    assert r.total_candidates == 8


def test_candidates_length_is_eight():
    r = inspect_promotion_baseline(dry_run=True)
    assert len(r.candidates) == 8


def test_candidate_names():
    r = inspect_promotion_baseline(dry_run=True)
    names = [c.name for c in r.candidates]
    assert names == [
        "aider", "codex", "cmdb",
        "media_control", "media_lab", "meeting_intelligence",
        "athlete_analytics", "office_automation",
    ]


def test_blocked_counts_sum_to_total():
    r = inspect_promotion_baseline(dry_run=True)
    assert r.hard_blocked_count + r.soft_blocked_count + r.unblocked_count == r.total_candidates


def test_aider_is_hard_blocked():
    r = inspect_promotion_baseline(dry_run=True)
    aider = next(c for c in r.candidates if c.name == "aider")
    assert aider.blocker_class == BLOCKER_CLASS_HARD
    assert aider.current_state == CURRENT_STATE_PARTIAL


def test_codex_is_soft_blocked():
    r = inspect_promotion_baseline(dry_run=True)
    codex = next(c for c in r.candidates if c.name == "codex")
    assert codex.blocker_class == BLOCKER_CLASS_SOFT
    assert codex.current_state == CURRENT_STATE_DEFERRED


def test_cmdb_is_unblocked():
    r = inspect_promotion_baseline(dry_run=True)
    cmdb = next(c for c in r.candidates if c.name == "cmdb")
    assert cmdb.blocker_class == BLOCKER_CLASS_NONE
    assert cmdb.current_state == CURRENT_STATE_SEED_COMPLETE


def test_domain_branches_are_soft_blocked():
    r = inspect_promotion_baseline(dry_run=True)
    branch_names = {"media_control", "media_lab", "meeting_intelligence", "athlete_analytics", "office_automation"}
    for c in r.candidates:
        if c.name in branch_names:
            assert c.blocker_class == BLOCKER_CLASS_SOFT
            assert c.current_state == CURRENT_STATE_SEED_COMPLETE


def test_all_candidates_have_evidence_present():
    r = inspect_promotion_baseline(dry_run=True)
    for c in r.candidates:
        assert len(c.evidence_present) > 0, f"{c.name} has no evidence_present"


def test_all_candidates_have_evidence_missing():
    r = inspect_promotion_baseline(dry_run=True)
    for c in r.candidates:
        assert len(c.evidence_missing) > 0, f"{c.name} has no evidence_missing"


def test_to_dict_has_schema_version():
    r = inspect_promotion_baseline(dry_run=True)
    d = r.to_dict()
    assert d["schema_version"] == 1


def test_to_dict_keys():
    r = inspect_promotion_baseline(dry_run=True)
    d = r.to_dict()
    for k in ("schema_version", "total_candidates", "hard_blocked_count", "soft_blocked_count", "unblocked_count", "candidates"):
        assert k in d


def test_candidate_to_dict():
    r = inspect_promotion_baseline(dry_run=True)
    cd = r.candidates[0].to_dict()
    for k in ("name", "current_state", "promotion_target", "evidence_present", "evidence_missing", "blocker_class"):
        assert k in cd


def test_json_round_trip():
    r = inspect_promotion_baseline(dry_run=True)
    d = r.to_dict()
    text = json.dumps(d)
    back = json.loads(text)
    assert back["schema_version"] == 1
    assert back["total_candidates"] == 8


def test_dry_run_no_file(tmp_path):
    r = inspect_promotion_baseline(artifact_dir=tmp_path / "out", dry_run=True)
    assert r.artifact_path == ""
    assert not (tmp_path / "out").exists()


def test_non_dry_run_writes_file(tmp_path):
    r = inspect_promotion_baseline(artifact_dir=tmp_path / "out", dry_run=False)
    assert r.artifact_path != ""
    assert Path(r.artifact_path).exists()


def test_init_ok_from_framework():
    from framework import inspect_promotion_baseline  # noqa: F401
