"""Tests for framework.aider_adapter_evidence — Aider evidence seam."""
import json
import pytest
from pathlib import Path

from framework.aider_adapter_evidence import (
    AIDER_STATUS_DONE,
    AIDER_STATUS_PARTIAL,
    AIDER_STATUS_DEFERRED,
    AiderAdapterEvidenceRecord,
    AiderAdapterEvidenceReport,
    gather_aider_evidence,
)


def test_import_ok():
    from framework.aider_adapter_evidence import gather_aider_evidence, AiderAdapterEvidenceReport  # noqa: F401


def test_status_constants():
    assert AIDER_STATUS_DONE == "adapter_done"
    assert AIDER_STATUS_PARTIAL == "adapter_partial"
    assert AIDER_STATUS_DEFERRED == "adapter_deferred"


def test_gather_returns_report():
    report = gather_aider_evidence(num_runs=2, dry_run=True)
    assert isinstance(report, AiderAdapterEvidenceReport)


def test_gather_correct_record_count():
    report = gather_aider_evidence(num_runs=3, dry_run=True)
    assert len(report.records) == 3
    assert report.total_runs == 3


def test_gather_never_emits_done():
    report = gather_aider_evidence(num_runs=4, dry_run=True)
    assert report.overall_status != AIDER_STATUS_DONE


def test_gather_dry_run_status_is_partial():
    report = gather_aider_evidence(num_runs=3, dry_run=True)
    assert report.overall_status == AIDER_STATUS_PARTIAL


def test_gather_all_records_dry_run():
    report = gather_aider_evidence(num_runs=3, dry_run=True)
    assert all(r.dry_run is True for r in report.records)


def test_gather_all_records_success():
    report = gather_aider_evidence(num_runs=3, dry_run=True)
    assert all(r.success is True for r in report.records)


def test_generated_at_is_iso():
    report = gather_aider_evidence(dry_run=True)
    assert "T" in report.generated_at


def test_to_dict_keys():
    report = gather_aider_evidence(num_runs=2, dry_run=True)
    d = report.to_dict()
    for k in ("schema_version", "overall_status", "total_runs", "successful_runs", "records", "notes"):
        assert k in d


def test_to_dict_schema_version():
    report = gather_aider_evidence(dry_run=True)
    assert report.to_dict()["schema_version"] == 1


def test_record_to_dict_keys():
    report = gather_aider_evidence(num_runs=1, dry_run=True)
    d = report.records[0].to_dict()
    for k in ("request_index", "model", "task_kind", "dry_run", "success", "exit_code"):
        assert k in d


def test_dry_run_no_file(tmp_path):
    report = gather_aider_evidence(artifact_dir=tmp_path / "out", dry_run=True)
    assert report.artifact_path == ""
    assert not (tmp_path / "out").exists()


def test_non_dry_run_writes_file(tmp_path):
    report = gather_aider_evidence(artifact_dir=tmp_path / "out", num_runs=2, dry_run=False)
    assert report.artifact_path != ""
    assert Path(report.artifact_path).exists()


def test_json_valid(tmp_path):
    report = gather_aider_evidence(artifact_dir=tmp_path / "out", num_runs=2, dry_run=False)
    data = json.loads(Path(report.artifact_path).read_text())
    assert "schema_version" in data
    assert "overall_status" in data


def test_init_ok_from_framework():
    from framework import gather_aider_evidence  # noqa: F401


def test_notes_mention_dry_run():
    report = gather_aider_evidence(dry_run=True)
    assert "dry-run" in report.notes.lower() or "dry_run" in report.notes.lower()
