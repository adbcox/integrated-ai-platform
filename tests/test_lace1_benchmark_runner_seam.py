"""Seam tests for LACE1-P10-BENCHMARK-RUNNER-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace1_benchmark_runner import Lace1BenchmarkRunner, BenchmarkRunReport, TaskRunResult
from framework.local_autonomy_benchmark_pack import LACE1_TASK_PACK


def test_import_runner():
    from framework.lace1_benchmark_runner import Lace1BenchmarkRunner
    assert callable(Lace1BenchmarkRunner)


def test_run_returns_report():
    report = Lace1BenchmarkRunner().run()
    assert isinstance(report, BenchmarkRunReport)


def test_benchmark_kind_is_synthetic_baseline():
    report = Lace1BenchmarkRunner().run()
    assert report.benchmark_kind == "synthetic_baseline"


def test_pass_rate_is_1():
    report = Lace1BenchmarkRunner().run()
    assert report.pass_rate == 1.0
    assert report.failed == 0


def test_task_results_count_matches_pack():
    report = Lace1BenchmarkRunner().run()
    assert len(report.task_results) == len(LACE1_TASK_PACK)


def test_emit_writes_json(tmp_path):
    runner = Lace1BenchmarkRunner()
    report = runner.run()
    path = runner.emit(report, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["benchmark_kind"] == "synthetic_baseline"
    assert data["pass_rate"] == 1.0
    assert "run_id" in data
