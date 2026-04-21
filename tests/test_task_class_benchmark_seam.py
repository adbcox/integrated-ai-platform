"""Conformance tests for framework/task_class_benchmark.py (LARAC2-TASK-CLASS-BENCHMARK-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.task_class_benchmark import (
    TaskClassBenchmarkRunner,
    TaskClassBenchmarkReport,
    TaskClassBenchmarkEntry,
)


# --- import and type ---

def test_import_task_class_benchmark_runner():
    assert callable(TaskClassBenchmarkRunner)


def test_returns_task_class_benchmark_report(tmp_path):
    r = TaskClassBenchmarkRunner(artifact_root=tmp_path).run()
    assert isinstance(r, TaskClassBenchmarkReport)


# --- fields ---

def test_report_fields_present(tmp_path):
    r = TaskClassBenchmarkRunner(artifact_root=tmp_path).run()
    assert hasattr(r, "entries")
    assert hasattr(r, "total_tasks")
    assert hasattr(r, "total_passed")
    assert hasattr(r, "total_failed")
    assert hasattr(r, "overall_pass_rate")
    assert hasattr(r, "evaluated_at")
    assert hasattr(r, "artifact_path")


# --- per-class entries ---

def test_entries_per_class(tmp_path):
    r = TaskClassBenchmarkRunner(artifact_root=tmp_path).run(
        task_classes=["text_replacement", "metadata_addition"]
    )
    assert len(r.entries) == 2
    kinds = {e.task_class for e in r.entries}
    assert "text_replacement" in kinds
    assert "metadata_addition" in kinds


def test_entry_fields_present(tmp_path):
    r = TaskClassBenchmarkRunner(artifact_root=tmp_path).run()
    e = r.entries[0]
    assert hasattr(e, "task_class")
    assert hasattr(e, "total")
    assert hasattr(e, "passed")
    assert hasattr(e, "failed")
    assert hasattr(e, "pass_rate")


# --- pass rate correctness ---

def test_text_replacement_pass_rate(tmp_path):
    r = TaskClassBenchmarkRunner(artifact_root=tmp_path, tasks_per_class=2).run(
        task_classes=["text_replacement"]
    )
    entry = r.entries[0]
    assert entry.pass_rate == 1.0


def test_total_tasks_correct(tmp_path):
    r = TaskClassBenchmarkRunner(artifact_root=tmp_path, tasks_per_class=3).run(
        task_classes=["text_replacement", "metadata_addition"]
    )
    assert r.total_tasks == 6


# --- overall pass rate ---

def test_overall_pass_rate_range(tmp_path):
    r = TaskClassBenchmarkRunner(artifact_root=tmp_path).run()
    assert 0.0 <= r.overall_pass_rate <= 1.0


# --- artifact ---

def test_artifact_written(tmp_path):
    r = TaskClassBenchmarkRunner(artifact_root=tmp_path).run()
    assert r.artifact_path is not None
    assert Path(r.artifact_path).exists()


def test_artifact_parseable(tmp_path):
    r = TaskClassBenchmarkRunner(artifact_root=tmp_path).run()
    data = json.loads(Path(r.artifact_path).read_text())
    assert "total_tasks" in data
    assert "entries" in data


# --- evaluated_at ---

def test_evaluated_at_is_string(tmp_path):
    r = TaskClassBenchmarkRunner(artifact_root=tmp_path).run()
    assert isinstance(r.evaluated_at, str)
    assert len(r.evaluated_at) > 0


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "TaskClassBenchmarkRunner")
    assert hasattr(framework, "TaskClassBenchmarkReport")
    assert hasattr(framework, "TaskClassBenchmarkEntry")
