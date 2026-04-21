"""Seam tests for LACE2-P9-REAL-FILE-RUNNER-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace2_benchmark_runner import Lace2BenchmarkRunner, Lace2BenchmarkRecord


def test_import_runner():
    assert callable(Lace2BenchmarkRunner)


def test_run_returns_record():
    r = Lace2BenchmarkRunner().run()
    assert isinstance(r, Lace2BenchmarkRecord)


def test_benchmark_kind_real_file_baseline():
    r = Lace2BenchmarkRunner().run()
    assert r.benchmark_kind == "real_file_baseline"


def test_total_tasks_8():
    r = Lace2BenchmarkRunner().run()
    assert r.total_tasks == 8


def test_pass_rate_1():
    r = Lace2BenchmarkRunner().run()
    assert r.pass_rate == 1.0, f"Expected pass_rate=1.0, got {r.pass_rate}; failures: {[t for t in r.task_results if not t.passed]}"


def test_emit_artifact(tmp_path):
    runner = Lace2BenchmarkRunner()
    r = runner.run()
    path = runner.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["benchmark_kind"] == "real_file_baseline"
    assert data["total_tasks"] == 8
    assert data["pass_rate"] == 1.0
    assert len(data["task_results"]) == 8
