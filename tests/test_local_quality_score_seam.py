"""Conformance tests for framework/local_quality_score.py (LARAC2-QUALITY-SCORE-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.local_quality_score import LocalQualityScore, compute_quality_score, emit_quality_score
from framework.unified_local_metrics import UnifiedLocalMetrics
from framework.task_class_benchmark import TaskClassBenchmarkReport, TaskClassBenchmarkEntry


def _metrics(first_pass=0.8, failure_rate=0.1, retry_burden=0, verdict="ready"):
    return UnifiedLocalMetrics(
        first_pass_rate=first_pass,
        failure_rate=failure_rate,
        total_retry_burden=retry_burden,
        readiness_verdict=verdict,
        task_classes_total=3,
        computed_at="now",
    )


def _bench_report(pass_rate=1.0, total_tasks=6):
    entries = (
        TaskClassBenchmarkEntry(task_class="text_replacement", total=total_tasks,
                                passed=int(pass_rate * total_tasks), failed=0,
                                pass_rate=pass_rate),
    )
    return TaskClassBenchmarkReport(
        entries=entries,
        total_tasks=total_tasks,
        total_passed=int(pass_rate * total_tasks),
        total_failed=total_tasks - int(pass_rate * total_tasks),
        overall_pass_rate=pass_rate,
        evaluated_at="now",
        artifact_path=None,
    )


# --- import and type ---

def test_import_compute_quality_score():
    assert callable(compute_quality_score)


def test_returns_local_quality_score():
    s = compute_quality_score(_metrics())
    assert isinstance(s, LocalQualityScore)


# --- fields ---

def test_score_fields_present():
    s = compute_quality_score(_metrics())
    assert hasattr(s, "raw_score")
    assert hasattr(s, "grade")
    assert hasattr(s, "evidence_weight")
    assert hasattr(s, "first_pass_contribution")
    assert hasattr(s, "benchmark_contribution")
    assert hasattr(s, "reliability_contribution")
    assert hasattr(s, "computed_at")


# --- score range ---

def test_score_in_range():
    s = compute_quality_score(_metrics())
    assert 0.0 <= s.raw_score <= 1.0


# --- grade boundaries ---

def test_grade_A_for_high_score():
    s = compute_quality_score(_metrics(first_pass=1.0, failure_rate=0.0), benchmark_report=_bench_report(1.0, 6))
    assert s.grade in {"A", "B"}


def test_grade_degrades_with_high_failure():
    s = compute_quality_score(_metrics(first_pass=0.1, failure_rate=0.9))
    assert s.grade in {"D", "F"}


# --- thin evidence degrades score ---

def test_thin_evidence_degrades():
    s_with = compute_quality_score(_metrics(), benchmark_report=_bench_report(1.0, 6))
    s_without = compute_quality_score(_metrics(), benchmark_report=None)
    assert s_with.raw_score >= s_without.raw_score


def test_thin_benchmark_degrades():
    # 2 tasks is below threshold (4)
    thin = _bench_report(pass_rate=1.0, total_tasks=2)
    thick = _bench_report(pass_rate=1.0, total_tasks=6)
    s_thin = compute_quality_score(_metrics(), benchmark_report=thin)
    s_thick = compute_quality_score(_metrics(), benchmark_report=thick)
    assert s_thick.raw_score >= s_thin.raw_score


# --- evidence weight ---

def test_evidence_weight_higher_with_benchmark():
    s_with = compute_quality_score(_metrics(), benchmark_report=_bench_report(1.0, 6))
    s_without = compute_quality_score(_metrics(), benchmark_report=None)
    assert s_with.evidence_weight >= s_without.evidence_weight


# --- emit artifact ---

def test_artifact_written(tmp_path):
    s = compute_quality_score(_metrics())
    path = emit_quality_score(s, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable(tmp_path):
    s = compute_quality_score(_metrics())
    path = emit_quality_score(s, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "raw_score" in data
    assert "grade" in data


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "LocalQualityScore")
    assert hasattr(framework, "compute_quality_score")
    assert hasattr(framework, "emit_quality_score")
