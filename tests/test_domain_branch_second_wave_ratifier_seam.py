"""Tests for framework.domain_branch_second_wave_ratifier — LAPC1 P11."""
import json
import pytest
from pathlib import Path

from framework.domain_branch_proof_harness import (
    BRANCH_VERDICT_DONE,
    BRANCH_VERDICT_SCAFFOLD_COMPLETE_PRODUCT_DEFERRED,
)
from framework.domain_branch_second_wave_ratifier import (
    SecondWavePromotionRecord,
    SecondWavePromotionArtifact,
    ratify_second_wave_promotion,
)


def test_import_ok():
    from framework.domain_branch_second_wave_ratifier import ratify_second_wave_promotion, SecondWavePromotionArtifact  # noqa: F401


def test_returns_artifact():
    a = ratify_second_wave_promotion(dry_run=True)
    assert isinstance(a, SecondWavePromotionArtifact)


def test_total_branches_two():
    a = ratify_second_wave_promotion(dry_run=True)
    assert a.total_branches == 2


def test_exactly_two_records():
    a = ratify_second_wave_promotion(dry_run=True)
    assert len(a.records) == 2


def test_branch_names():
    a = ratify_second_wave_promotion(dry_run=True)
    names = [r.branch_name for r in a.records]
    assert names == ["athlete_analytics", "office_automation"]


def test_athlete_analytics_first():
    a = ratify_second_wave_promotion(dry_run=True)
    assert a.records[0].branch_name == "athlete_analytics"


def test_office_automation_second():
    a = ratify_second_wave_promotion(dry_run=True)
    assert a.records[1].branch_name == "office_automation"


def test_all_scaffold_complete():
    a = ratify_second_wave_promotion(dry_run=True)
    assert a.all_scaffold_complete is True


def test_not_any_done():
    a = ratify_second_wave_promotion(dry_run=True)
    assert a.any_done is False


def test_each_verdict_scaffold():
    a = ratify_second_wave_promotion(dry_run=True)
    for r in a.records:
        assert r.verdict == BRANCH_VERDICT_SCAFFOLD_COMPLETE_PRODUCT_DEFERRED


def test_to_dict_schema_version():
    a = ratify_second_wave_promotion(dry_run=True)
    d = a.to_dict()
    assert d["schema_version"] == 1


def test_to_dict_keys():
    a = ratify_second_wave_promotion(dry_run=True)
    d = a.to_dict()
    for k in ("schema_version", "any_done", "all_scaffold_complete", "total_branches", "records"):
        assert k in d


def test_json_round_trip():
    a = ratify_second_wave_promotion(dry_run=True)
    text = json.dumps(a.to_dict())
    back = json.loads(text)
    assert back["schema_version"] == 1
    assert back["total_branches"] == 2


def test_dry_run_no_file(tmp_path):
    a = ratify_second_wave_promotion(artifact_dir=tmp_path / "out", dry_run=True)
    assert a.artifact_path == ""


def test_non_dry_run_writes_file(tmp_path):
    a = ratify_second_wave_promotion(artifact_dir=tmp_path / "out", dry_run=False)
    assert a.artifact_path != ""
    assert Path(a.artifact_path).exists()


def test_init_ok_from_framework():
    from framework import ratify_second_wave_promotion  # noqa: F401
