"""Conformance tests for framework/retry_telemetry.py (ADSC1-RETRY-TELEMETRY-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.retry_telemetry import RetryTelemetryRecord, record_retry_telemetry
from framework.runtime_execution_adapter import BoundedExecutionSummary, ExecutionStepResult


def _make_summary(*, steps=(), outcome="pass", session_id="s1", job_id="job-abc"):
    succeeded = sum(1 for s in steps if s.success)
    failed = sum(1 for s in steps if not s.success)
    return BoundedExecutionSummary(
        session_id=session_id,
        job_id=job_id,
        total_steps=len(steps),
        succeeded=succeeded,
        failed=failed,
        outcome=outcome,
        steps=tuple(steps),
    )


def _pass_step():
    return ExecutionStepResult(action_type="run_tests", success=True)


def _fail_step_with_error():
    return ExecutionStepResult(action_type="run_tests", success=False, error="test failed")


def _fail_step_no_error():
    return ExecutionStepResult(action_type="run_tests", success=False, error=None)


# --- import and type ---

def test_import_retry_telemetry():
    assert callable(record_retry_telemetry)


def test_returns_record_type(tmp_path):
    summary = _make_summary()
    result = record_retry_telemetry(summary, artifact_dir=tmp_path)
    assert isinstance(result, RetryTelemetryRecord)


# --- count correctness ---

def test_all_pass_zero_failed(tmp_path):
    summary = _make_summary(steps=[_pass_step(), _pass_step()])
    result = record_retry_telemetry(summary, artifact_dir=tmp_path)
    assert result.failed_steps == 0
    assert result.retry_eligible_failures == 0


def test_failed_step_counted(tmp_path):
    summary = _make_summary(steps=[_pass_step(), _fail_step_with_error()])
    result = record_retry_telemetry(summary, artifact_dir=tmp_path)
    assert result.failed_steps == 1


def test_retry_eligible_requires_error(tmp_path):
    summary = _make_summary(steps=[_fail_step_with_error(), _fail_step_no_error()])
    result = record_retry_telemetry(summary, artifact_dir=tmp_path)
    assert result.failed_steps == 2
    assert result.retry_eligible_failures == 1


# --- artifact writing ---

def test_artifact_written(tmp_path):
    summary = _make_summary(job_id="job-test1")
    record_retry_telemetry(summary, artifact_dir=tmp_path)
    assert (tmp_path / "retry_telemetry_job-test1.json").exists()


def test_artifact_parseable_json(tmp_path):
    summary = _make_summary(job_id="job-test2")
    record_retry_telemetry(summary, artifact_dir=tmp_path)
    data = json.loads((tmp_path / "retry_telemetry_job-test2.json").read_text())
    assert "session_id" in data
    assert "job_id" in data
    assert "retry_eligible_failures" in data


# --- field echoes ---

def test_session_id_echoed(tmp_path):
    summary = _make_summary(session_id="my-session")
    result = record_retry_telemetry(summary, artifact_dir=tmp_path)
    assert result.session_id == "my-session"


def test_job_id_echoed(tmp_path):
    summary = _make_summary(job_id="job-xyz")
    result = record_retry_telemetry(summary, artifact_dir=tmp_path)
    assert result.job_id == "job-xyz"


def test_outcome_echoed(tmp_path):
    summary = _make_summary(outcome="fail")
    result = record_retry_telemetry(summary, artifact_dir=tmp_path)
    assert result.outcome == "fail"


def test_total_steps_echoed(tmp_path):
    summary = _make_summary(steps=[_pass_step(), _pass_step(), _fail_step_with_error()])
    result = record_retry_telemetry(summary, artifact_dir=tmp_path)
    assert result.total_steps == 3


# --- package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "RetryTelemetryRecord")
    assert hasattr(framework, "record_retry_telemetry")
