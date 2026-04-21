"""Conformance tests for framework/task_class_readiness.py (ADSC1-TASK-CLASS-READINESS-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.autonomy_evidence import TaskClassMetrics
from framework.task_class_readiness import (
    TaskClassReadinessReport,
    TaskClassVerdict,
    derive_task_class_readiness,
    emit_readiness_report,
)


def _metric(task_class, total_attempts=5, failure_rate=0.0):
    successes = int(total_attempts * (1 - failure_rate))
    failures = total_attempts - successes
    return TaskClassMetrics(
        task_class=task_class,
        total_attempts=total_attempts,
        successes=successes,
        failures=failures,
        failure_rate=failure_rate,
        routed_profile="local",
        escalated=False,
    )


# --- import ---

def test_import_derive_task_class_readiness():
    assert callable(derive_task_class_readiness)


def test_returns_report_type():
    report = derive_task_class_readiness([_metric("text_replacement")])
    assert isinstance(report, TaskClassReadinessReport)


# --- verdict logic ---

def test_all_passing_metrics_ready():
    metrics = [_metric("text_replacement", failure_rate=0.0),
               _metric("helper_insertion", failure_rate=0.05)]
    report = derive_task_class_readiness(metrics, min_attempts=1)
    assert all(v.verdict == "ready" for v in report.verdicts)
    assert report.overall_verdict == "ready"


def test_high_failure_not_ready():
    m = _metric("text_replacement", total_attempts=10, failure_rate=0.8)
    report = derive_task_class_readiness([m], min_attempts=3)
    assert report.verdicts[0].verdict == "not_ready"
    assert report.overall_verdict == "not_ready"


def test_borderline_marginal():
    m = _metric("text_replacement", total_attempts=10, failure_rate=0.25)
    report = derive_task_class_readiness([m], min_attempts=3)
    assert report.verdicts[0].verdict == "marginal"


def test_insufficient_attempts_marginal():
    m = _metric("text_replacement", total_attempts=1, failure_rate=0.0)
    report = derive_task_class_readiness([m], min_attempts=3)
    assert report.verdicts[0].verdict == "marginal"
    assert "insufficient evidence" in report.verdicts[0].rationale


# --- overall verdict aggregation ---

def test_overall_not_ready_when_any_not_ready():
    metrics = [_metric("a", failure_rate=0.0), _metric("b", failure_rate=0.9)]
    report = derive_task_class_readiness(metrics, min_attempts=1)
    assert report.overall_verdict == "not_ready"


def test_overall_marginal_when_any_marginal():
    metrics = [_metric("a", failure_rate=0.0, total_attempts=1),
               _metric("b", failure_rate=0.0, total_attempts=5)]
    report = derive_task_class_readiness(metrics, min_attempts=3)
    assert report.overall_verdict == "marginal"


# --- count fields ---

def test_count_fields_correct():
    metrics = [
        _metric("a", failure_rate=0.0, total_attempts=5),
        _metric("b", failure_rate=0.25, total_attempts=5),
        _metric("c", failure_rate=0.9, total_attempts=5),
    ]
    report = derive_task_class_readiness(metrics, min_attempts=3)
    assert report.ready_count == 1
    assert report.marginal_count == 1
    assert report.not_ready_count == 1


# --- artifact writing ---

def test_artifact_written(tmp_path):
    report = derive_task_class_readiness([_metric("x")], min_attempts=1)
    path = emit_readiness_report(report, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable(tmp_path):
    report = derive_task_class_readiness([_metric("x")], min_attempts=1)
    path = emit_readiness_report(report, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "overall_verdict" in data
    assert "verdicts" in data


# --- task_class echoed ---

def test_task_class_echoed_in_verdict():
    report = derive_task_class_readiness([_metric("my_kind")], min_attempts=1)
    assert report.verdicts[0].task_class == "my_kind"


# --- frozen dataclass immutable ---

def test_verdict_is_frozen():
    v = TaskClassVerdict(task_class="x", verdict="ready", failure_rate=0.0, total_attempts=5, rationale="ok")
    try:
        v.verdict = "not_ready"  # type: ignore[misc]
        assert False, "should have raised"
    except (TypeError, AttributeError):
        pass  # frozen as expected


# --- package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "derive_task_class_readiness")
    assert hasattr(framework, "TaskClassReadinessReport")
    assert hasattr(framework, "TaskClassVerdict")
    assert hasattr(framework, "emit_readiness_report")
