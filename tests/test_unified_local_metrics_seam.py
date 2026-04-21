"""Conformance tests for framework/unified_local_metrics.py (LARAC2-METRICS-UNIFICATION-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.unified_local_metrics import UnifiedLocalMetrics, compute_unified_metrics, emit_unified_metrics
from framework.autonomy_metrics_extended import ExtendedAutonomyMetrics
from framework.retry_telemetry import RetryTelemetryRecord
from framework.task_class_readiness import TaskClassReadinessReport


def _ext(first_pass=0.8, failure_rate=0.1, total_classes=3):
    return ExtendedAutonomyMetrics(
        generated_at="now",
        total_task_classes=total_classes,
        overall_first_pass_rate=first_pass,
        overall_failure_rate=failure_rate,
    )


def _rr(eligible=2):
    return RetryTelemetryRecord(
        session_id="s", job_id="j", total_steps=5, failed_steps=2,
        retry_eligible_failures=eligible, outcome="partial", recorded_at="now"
    )


def _readiness(verdict="ready"):
    return TaskClassReadinessReport(
        verdicts=(), overall_verdict=verdict,
        ready_count=1, marginal_count=0, not_ready_count=0, evaluated_at="now"
    )


# --- import and type ---

def test_import_compute_unified_metrics():
    assert callable(compute_unified_metrics)


def test_returns_unified_local_metrics():
    m = compute_unified_metrics(_ext())
    assert isinstance(m, UnifiedLocalMetrics)


# --- fields ---

def test_fields_present():
    m = compute_unified_metrics(_ext())
    assert hasattr(m, "first_pass_rate")
    assert hasattr(m, "failure_rate")
    assert hasattr(m, "total_retry_burden")
    assert hasattr(m, "readiness_verdict")
    assert hasattr(m, "task_classes_total")
    assert hasattr(m, "computed_at")


# --- first_pass_rate ---

def test_first_pass_rate_extracted():
    m = compute_unified_metrics(_ext(first_pass=0.75))
    assert abs(m.first_pass_rate - 0.75) < 0.001


# --- failure_rate ---

def test_failure_rate_extracted():
    m = compute_unified_metrics(_ext(failure_rate=0.25))
    assert abs(m.failure_rate - 0.25) < 0.001


# --- retry burden ---

def test_retry_burden_empty():
    m = compute_unified_metrics(_ext(), retry_records=[])
    assert m.total_retry_burden == 0


def test_retry_burden_summed():
    m = compute_unified_metrics(_ext(), retry_records=[_rr(2), _rr(3)])
    assert m.total_retry_burden == 5


# --- readiness verdict ---

def test_readiness_unknown_when_none():
    m = compute_unified_metrics(_ext(), readiness_report=None)
    assert m.readiness_verdict == "unknown"


def test_readiness_verdict_from_report():
    m = compute_unified_metrics(_ext(), readiness_report=_readiness("marginal"))
    assert m.readiness_verdict == "marginal"


# --- emit artifact ---

def test_artifact_written(tmp_path):
    m = compute_unified_metrics(_ext())
    path = emit_unified_metrics(m, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable(tmp_path):
    m = compute_unified_metrics(_ext())
    path = emit_unified_metrics(m, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "first_pass_rate" in data
    assert "failure_rate" in data


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "UnifiedLocalMetrics")
    assert hasattr(framework, "compute_unified_metrics")
    assert hasattr(framework, "emit_unified_metrics")
