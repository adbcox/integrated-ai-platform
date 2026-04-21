"""Tests for framework.autonomy_metrics_extended — extended metrics seam."""
import json
import pytest
from pathlib import Path

from framework.local_memory_store import LocalMemoryStore
from framework.task_prompt_pack import SUPPORTED_TASK_CLASSES
from framework.autonomy_metrics_extended import (
    ExtendedAutonomyMetrics,
    TaskClassMetricsExtended,
    collect_extended_metrics,
    save_extended_metrics,
)


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "memory")


@pytest.fixture
def artifact_dir(tmp_path):
    return tmp_path / "metrics"


def test_import_ok():
    from framework.autonomy_metrics_extended import collect_extended_metrics, ExtendedAutonomyMetrics  # noqa: F401


def test_collect_returns_extended_metrics(store):
    result = collect_extended_metrics(memory_store=store)
    assert isinstance(result, ExtendedAutonomyMetrics)


def test_collect_empty_zero_counts(store):
    result = collect_extended_metrics(memory_store=store)
    assert result.overall_successes == 0
    assert result.overall_failures == 0


def test_collect_task_class_count(store):
    result = collect_extended_metrics(memory_store=store)
    assert len(result.task_class_breakdown) == len(SUPPORTED_TASK_CLASSES)


def test_collect_total_task_classes(store):
    result = collect_extended_metrics(memory_store=store)
    assert result.total_task_classes == len(SUPPORTED_TASK_CLASSES)


def test_collect_counts_successes(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    store.record_success(task_kind="bug_fix", target_file="b.py", old_string="z", new_string="w")
    result = collect_extended_metrics(memory_store=store)
    assert result.overall_successes == 2


def test_collect_counts_failures(store):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    result = collect_extended_metrics(memory_store=store)
    assert result.overall_failures == 1


def test_collect_failure_rate_correct(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    store.record_failure(task_kind="text_replacement", target_file="b.py", old_string="z", error="err")
    result = collect_extended_metrics(memory_store=store)
    assert result.overall_failure_rate == pytest.approx(0.5)


def test_collect_first_pass_rate(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    store.record_success(task_kind="text_replacement", target_file="b.py", old_string="y", new_string="z")
    result = collect_extended_metrics(memory_store=store)
    assert result.overall_first_pass_rate == pytest.approx(1.0)


def test_collect_dominant_error_type(store):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="syntax_error")
    store.record_failure(task_kind="text_replacement", target_file="b.py", old_string="y", error="syntax_error")
    store.record_failure(task_kind="bug_fix", target_file="c.py", old_string="z", error="runtime_error")
    result = collect_extended_metrics(memory_store=store)
    assert result.dominant_error_type != ""


def test_passes_thresholds_false_on_empty(store):
    result = collect_extended_metrics(memory_store=store, min_attempts=5)
    assert not result.passes_thresholds()


def test_passes_thresholds_true_when_met(store):
    for _ in range(10):
        store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    result = collect_extended_metrics(memory_store=store, min_attempts=5, max_failure_rate=0.30)
    assert result.passes_thresholds()


def test_threshold_report_is_string(store):
    result = collect_extended_metrics(memory_store=store)
    report = result.threshold_report()
    assert isinstance(report, str)
    assert "attempts" in report


def test_save_dry_run_no_file(store, artifact_dir):
    result = collect_extended_metrics(memory_store=store)
    path = save_extended_metrics(result, artifact_dir=artifact_dir, dry_run=True)
    assert path is None
    assert not artifact_dir.exists()


def test_save_writes_file(store, artifact_dir):
    result = collect_extended_metrics(memory_store=store)
    path = save_extended_metrics(result, artifact_dir=artifact_dir, dry_run=False)
    assert path is not None
    assert Path(path).exists()


def test_save_json_valid(store, artifact_dir):
    result = collect_extended_metrics(memory_store=store)
    path = save_extended_metrics(result, artifact_dir=artifact_dir, dry_run=False)
    data = json.loads(Path(path).read_text())
    assert "schema_version" in data
    assert "task_class_breakdown" in data
    assert "overall_failure_rate" in data
