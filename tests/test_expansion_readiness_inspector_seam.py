"""Tests for framework.expansion_readiness_inspector — expansion readiness seam."""
import json
import pytest
from pathlib import Path

from framework.expansion_readiness_inspector import (
    ExpansionReadinessItem,
    ExpansionReadinessReport,
    READINESS_EXPANSION_READY,
    READINESS_EXPANSION_PARTIAL,
    READINESS_EXPANSION_BLOCKED,
    inspect_expansion_readiness,
)


def test_import_ok():
    from framework.expansion_readiness_inspector import inspect_expansion_readiness, ExpansionReadinessReport  # noqa: F401


def test_constants():
    assert READINESS_EXPANSION_READY == "expansion_ready"
    assert READINESS_EXPANSION_PARTIAL == "expansion_partial"
    assert READINESS_EXPANSION_BLOCKED == "expansion_blocked"


def test_item_fields():
    item = ExpansionReadinessItem(name="test", status="present", detail="ok")
    assert item.name == "test"
    assert item.status == "present"
    assert item.detail == "ok"


def test_item_to_dict():
    item = ExpansionReadinessItem(name="test", status="missing", detail="not found")
    d = item.to_dict()
    assert d["name"] == "test"
    assert d["status"] == "missing"
    assert d["detail"] == "not found"


def test_no_evidence_returns_report():
    report = inspect_expansion_readiness(dry_run=True)
    assert isinstance(report, ExpansionReadinessReport)


def test_no_evidence_is_partial():
    report = inspect_expansion_readiness(dry_run=True)
    assert report.overall_status == READINESS_EXPANSION_PARTIAL


def test_items_count_correct():
    report = inspect_expansion_readiness(dry_run=True)
    # 3 evidence surfaces + 4 post-LARAC1 modules = 7
    assert len(report.items) == 7


def test_post_larac1_modules_present_on_disk():
    report = inspect_expansion_readiness(dry_run=True)
    module_items = [i for i in report.items if i.name.startswith("framework/")]
    present = [i for i in module_items if i.status == "present"]
    # All 4 post-LARAC1 modules should be present on disk
    assert len(present) == 4


def test_inspected_at_is_iso():
    report = inspect_expansion_readiness(dry_run=True)
    assert "T" in report.inspected_at


def test_to_dict_keys():
    report = inspect_expansion_readiness(dry_run=True)
    d = report.to_dict()
    for k in ("schema_version", "overall_status", "inspected_at", "items"):
        assert k in d


def test_to_dict_schema_version():
    report = inspect_expansion_readiness(dry_run=True)
    assert report.to_dict()["schema_version"] == 1


def test_dry_run_no_file(tmp_path):
    report = inspect_expansion_readiness(artifact_dir=tmp_path / "out", dry_run=True)
    assert report.artifact_path == ""
    assert not (tmp_path / "out").exists()


def test_non_dry_run_writes_file(tmp_path):
    report = inspect_expansion_readiness(artifact_dir=tmp_path / "out", dry_run=False)
    assert report.artifact_path != ""
    assert Path(report.artifact_path).exists()


def test_json_valid(tmp_path):
    report = inspect_expansion_readiness(artifact_dir=tmp_path / "out", dry_run=False)
    data = json.loads(Path(report.artifact_path).read_text())
    assert "schema_version" in data
    assert "overall_status" in data


def test_all_present_is_ready():
    from framework.readiness_ratifier import RatificationArtifact
    from framework.adapter_campaign_pre_authorizer import PreAuthorizationArtifact
    from framework.first_pass_metric import FirstPassReport

    rat = RatificationArtifact(
        campaign_id="C", decision="ratified", ratified_at="T",
        total_attempts=1, all_criteria_passed=True,
        criteria_summary=[], defer_reasons=[], next_steps=""
    )
    pre = PreAuthorizationArtifact(
        campaign_id="C", decision="pre_authorized", gates=[],
        all_gates_passed=True, defer_reasons=[], next_steps="", generated_at="T"
    )
    fp = FirstPassReport(
        stats=[], overall_first_pass_successes=0, overall_retry_successes=0,
        overall_attempts=0, overall_first_pass_rate=0.0, generated_at="T"
    )
    report = inspect_expansion_readiness(
        ratification_artifact=rat,
        pre_auth_artifact=pre,
        first_pass_report=fp,
        dry_run=True,
    )
    # Post-LARAC1 modules are present, evidence present → ready
    assert report.overall_status == READINESS_EXPANSION_READY


def test_init_ok_from_framework():
    from framework import inspect_expansion_readiness  # noqa: F401


def test_items_are_list_of_expansion_readiness_items():
    report = inspect_expansion_readiness(dry_run=True)
    for item in report.items:
        assert isinstance(item, ExpansionReadinessItem)
