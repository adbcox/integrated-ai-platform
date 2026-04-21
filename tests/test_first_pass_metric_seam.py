"""Tests for framework.first_pass_metric — FirstPassReport seam."""
import json
import pytest
from pathlib import Path

from framework.retry_telemetry_integration import LoopRetryIntegrationRecord, LoopRetryStore
from framework.first_pass_metric import (
    FirstPassStat,
    FirstPassReport,
    compute_first_pass_metrics,
    save_first_pass_report,
)


@pytest.fixture
def store(tmp_path):
    return LoopRetryStore(store_dir=tmp_path / "telemetry")


def _add_record(store, task_kind="text_replacement", attempt=1, success=True, session_id="s1"):
    r = LoopRetryIntegrationRecord(
        session_id=session_id,
        task_kind=task_kind,
        attempt_number=attempt,
        success=success,
        error_type="none" if success else "other",
        recorded_at="2026-01-01T00:00:00+00:00",
    )
    store.append(r)


def test_import_ok():
    from framework.first_pass_metric import FirstPassReport, compute_first_pass_metrics  # noqa: F401


def test_compute_returns_report(store):
    report = compute_first_pass_metrics(store)
    assert isinstance(report, FirstPassReport)


def test_empty_store_zero_attempts(store):
    report = compute_first_pass_metrics(store)
    assert report.overall_attempts == 0


def test_empty_store_zero_fp_rate(store):
    report = compute_first_pass_metrics(store)
    assert report.overall_first_pass_rate == 0.0


def test_first_pass_success_counted(store):
    _add_record(store, attempt=1, success=True)
    report = compute_first_pass_metrics(store)
    assert report.overall_first_pass_successes >= 1


def test_retry_success_counted(store):
    _add_record(store, attempt=1, success=False)
    _add_record(store, attempt=2, success=True)
    report = compute_first_pass_metrics(store)
    assert report.overall_retry_successes >= 1


def test_first_pass_rate_correct(store):
    _add_record(store, attempt=1, success=True, task_kind="text_replacement")
    _add_record(store, attempt=2, success=True, task_kind="text_replacement")
    report = compute_first_pass_metrics(store)
    # 1 fp success out of 2 total in the task_kind
    stat = next((s for s in report.stats if s.task_kind == "text_replacement"), None)
    assert stat is not None
    assert stat.first_pass_successes == 1
    assert stat.retry_successes == 1


def test_retry_attempt_not_counted_as_fp(store):
    _add_record(store, attempt=2, success=True)
    report = compute_first_pass_metrics(store)
    assert report.overall_first_pass_successes == 0


def test_generated_at_is_iso(store):
    report = compute_first_pass_metrics(store)
    assert "T" in report.generated_at


def test_summary_lines_returns_list(store):
    report = compute_first_pass_metrics(store)
    lines = report.summary_lines()
    assert isinstance(lines, list)
    assert len(lines) >= 1


def test_to_dict_keys(store):
    report = compute_first_pass_metrics(store)
    d = report.to_dict()
    for k in ("schema_version", "generated_at", "overall_first_pass_rate", "stats"):
        assert k in d


def test_save_dry_run_no_file(store, tmp_path):
    report = compute_first_pass_metrics(store)
    saved = save_first_pass_report(report, artifact_dir=tmp_path / "out", dry_run=True)
    assert saved.artifact_path == ""


def test_save_writes_file(store, tmp_path):
    report = compute_first_pass_metrics(store)
    saved = save_first_pass_report(report, artifact_dir=tmp_path / "out", dry_run=False)
    assert saved.artifact_path != ""
    assert Path(saved.artifact_path).exists()


def test_save_json_valid(store, tmp_path):
    report = compute_first_pass_metrics(store)
    saved = save_first_pass_report(report, artifact_dir=tmp_path / "out", dry_run=False)
    data = json.loads(Path(saved.artifact_path).read_text())
    assert "schema_version" in data
    assert "overall_first_pass_rate" in data


def test_overall_attempts_total_records(store):
    _add_record(store, attempt=1, success=True, task_kind="text_replacement")
    _add_record(store, attempt=2, success=True, task_kind="text_replacement")
    report = compute_first_pass_metrics(store)
    assert report.overall_attempts >= 2


def test_init_ok_from_framework():
    from framework import compute_first_pass_metrics  # noqa: F401
