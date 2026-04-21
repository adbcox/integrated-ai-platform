"""Tests for framework.task_repetition_harness — evidence accumulation seam."""
import json
import pytest
from pathlib import Path

from framework.local_memory_store import LocalMemoryStore
from framework.task_repetition_harness import (
    RepetitionRunConfig,
    RepetitionRunRecord,
    RepetitionRunResult,
    TaskRepetitionHarness,
    make_synthetic_repetition_tasks,
)


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "memory")


@pytest.fixture
def tmp_tasks_dir(tmp_path):
    return tmp_path / "tasks"


def test_import_ok():
    from framework.task_repetition_harness import TaskRepetitionHarness, RepetitionRunResult  # noqa: F401


def test_repetition_run_config_fields():
    config = RepetitionRunConfig(task_kind="text_replacement", num_runs=3)
    assert config.task_kind == "text_replacement"
    assert config.num_runs == 3
    assert config.dry_run is False


def test_repetition_run_record_fields():
    rec = RepetitionRunRecord(
        task_kind="text_replacement",
        run_index=0,
        success=True,
        error_message="",
        duration_seconds=0.01,
        recorded_at="2026-01-01T00:00:00+00:00",
    )
    assert rec.success is True
    assert rec.run_index == 0


def test_run_dry_run_returns_result(store, tmp_tasks_dir):
    harness = TaskRepetitionHarness(memory_store=store)
    config = RepetitionRunConfig(task_kind="text_replacement", num_runs=3, dry_run=True)
    tasks = make_synthetic_repetition_tasks("text_replacement", 3, tmp_tasks_dir)
    result = harness.run(config, tasks)
    assert isinstance(result, RepetitionRunResult)
    assert result.total_runs == 3


def test_dry_run_all_success(store, tmp_tasks_dir):
    harness = TaskRepetitionHarness(memory_store=store)
    config = RepetitionRunConfig(task_kind="text_replacement", num_runs=2, dry_run=True)
    tasks = make_synthetic_repetition_tasks("text_replacement", 2, tmp_tasks_dir)
    result = harness.run(config, tasks)
    assert result.success_count == 2
    assert result.failure_count == 0


def test_dry_run_does_not_write_to_memory(store, tmp_tasks_dir):
    harness = TaskRepetitionHarness(memory_store=store)
    config = RepetitionRunConfig(task_kind="text_replacement", num_runs=3, dry_run=True)
    tasks = make_synthetic_repetition_tasks("text_replacement", 3, tmp_tasks_dir)
    harness.run(config, tasks)
    assert len(store.query_successes()) == 0
    assert len(store.query_failures()) == 0


def test_make_synthetic_tasks_count(tmp_tasks_dir):
    tasks = make_synthetic_repetition_tasks("text_replacement", 5, tmp_tasks_dir)
    assert len(tasks) == 5


def test_make_synthetic_tasks_files_exist(tmp_tasks_dir):
    tasks = make_synthetic_repetition_tasks("text_replacement", 3, tmp_tasks_dir)
    for t in tasks:
        assert Path(t["target_path"]).exists()


def test_make_synthetic_tasks_have_required_keys(tmp_tasks_dir):
    tasks = make_synthetic_repetition_tasks("text_replacement", 2, tmp_tasks_dir)
    for t in tasks:
        assert "target_path" in t
        assert "old_string" in t
        assert "new_string" in t
        assert "task_kind" in t


def test_result_to_dict_keys(store, tmp_tasks_dir):
    harness = TaskRepetitionHarness(memory_store=store)
    config = RepetitionRunConfig(task_kind="text_replacement", num_runs=1, dry_run=True)
    tasks = make_synthetic_repetition_tasks("text_replacement", 1, tmp_tasks_dir)
    result = harness.run(config, tasks)
    d = result.to_dict()
    for k in ("schema_version", "task_kind", "total_runs", "success_count", "failure_count", "records"):
        assert k in d, f"Missing key: {k}"


def test_summary_line_format(store, tmp_tasks_dir):
    harness = TaskRepetitionHarness(memory_store=store)
    config = RepetitionRunConfig(task_kind="text_replacement", num_runs=2, dry_run=True)
    tasks = make_synthetic_repetition_tasks("text_replacement", 2, tmp_tasks_dir)
    result = harness.run(config, tasks)
    line = result.summary_line()
    assert "text_replacement" in line
    assert "runs" in line


def test_started_at_is_iso(store, tmp_tasks_dir):
    harness = TaskRepetitionHarness(memory_store=store)
    config = RepetitionRunConfig(task_kind="text_replacement", num_runs=1, dry_run=True)
    tasks = make_synthetic_repetition_tasks("text_replacement", 1, tmp_tasks_dir)
    result = harness.run(config, tasks)
    assert "T" in result.started_at


def test_finished_at_is_iso(store, tmp_tasks_dir):
    harness = TaskRepetitionHarness(memory_store=store)
    config = RepetitionRunConfig(task_kind="text_replacement", num_runs=1, dry_run=True)
    tasks = make_synthetic_repetition_tasks("text_replacement", 1, tmp_tasks_dir)
    result = harness.run(config, tasks)
    assert "T" in result.finished_at


def test_run_num_runs_cap(store, tmp_tasks_dir):
    harness = TaskRepetitionHarness(memory_store=store)
    config = RepetitionRunConfig(task_kind="text_replacement", num_runs=2, dry_run=True)
    tasks = make_synthetic_repetition_tasks("text_replacement", 5, tmp_tasks_dir)
    result = harness.run(config, tasks)
    assert result.total_runs == 2


def test_run_records_have_correct_run_index(store, tmp_tasks_dir):
    harness = TaskRepetitionHarness(memory_store=store)
    config = RepetitionRunConfig(task_kind="text_replacement", num_runs=3, dry_run=True)
    tasks = make_synthetic_repetition_tasks("text_replacement", 3, tmp_tasks_dir)
    result = harness.run(config, tasks)
    indices = [r.run_index for r in result.records]
    assert indices == [0, 1, 2]


def test_record_duration_non_negative(store, tmp_tasks_dir):
    harness = TaskRepetitionHarness(memory_store=store)
    config = RepetitionRunConfig(task_kind="text_replacement", num_runs=2, dry_run=True)
    tasks = make_synthetic_repetition_tasks("text_replacement", 2, tmp_tasks_dir)
    result = harness.run(config, tasks)
    for rec in result.records:
        assert rec.duration_seconds >= 0
