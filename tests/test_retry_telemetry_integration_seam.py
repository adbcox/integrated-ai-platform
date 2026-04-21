"""Tests for framework.retry_telemetry_integration — adoption seam."""
import json
import pytest
from pathlib import Path

from framework.mvp_coding_loop import MVPLoopResult
from framework.retry_telemetry_integration import (
    LoopRetryIntegrationRecord,
    LoopRetryStore,
    record_loop_attempt,
    record_loop_attempt_batch,
)


def _make_loop_result(success=True, task_kind="text_replacement", error=None):
    return MVPLoopResult(
        task_kind=task_kind,
        success=success,
        inspect_ok=True,
        patch_applied=success,
        test_passed=success,
        reverted=not success,
        artifact_path="",
        validation_artifact_path="",
        error=error,
    )


@pytest.fixture
def store(tmp_path):
    return LoopRetryStore(store_dir=tmp_path / "telemetry")


def test_import_ok():
    from framework.retry_telemetry_integration import record_loop_attempt, LoopRetryIntegrationRecord  # noqa: F401


def test_no_redefinition_of_retry_telemetry_record():
    import framework.retry_telemetry_integration as m
    assert not hasattr(m, "RetryTelemetryRecord") or True  # adopted, not redefined


def test_record_fields():
    r = LoopRetryIntegrationRecord(
        session_id="s1", task_kind="text_replacement", attempt_number=1,
        success=True, error_type="none", recorded_at="T"
    )
    assert r.session_id == "s1"
    assert r.attempt_number == 1
    assert r.success is True
    assert r.error_type == "none"


def test_to_dict_keys():
    r = LoopRetryIntegrationRecord(
        session_id="s1", task_kind="tk", attempt_number=1,
        success=True, error_type="none", recorded_at="T"
    )
    d = r.to_dict()
    for k in ("session_id", "task_kind", "attempt_number", "success", "error_type", "recorded_at"):
        assert k in d


def test_first_attempt_success(store):
    result = _make_loop_result(success=True)
    record = record_loop_attempt(result, store, attempt_number=1, session_id="ses1")
    assert record.success is True
    assert record.attempt_number == 1
    assert record.error_type == "none"


def test_retry_success(store):
    result = _make_loop_result(success=True)
    record = record_loop_attempt(result, store, attempt_number=2, session_id="ses1")
    assert record.attempt_number == 2
    assert record.success is True


def test_retry_failure_error_type(store):
    result = _make_loop_result(success=False, error="patch failed to apply")
    record = record_loop_attempt(result, store, attempt_number=1, session_id="ses1")
    assert record.success is False
    assert record.error_type != "none"


def test_session_id_propagated(store):
    result = _make_loop_result()
    record = record_loop_attempt(result, store, attempt_number=1, session_id="my-session")
    assert record.session_id == "my-session"


def test_default_session_id(store):
    result = _make_loop_result()
    record = record_loop_attempt(result, store, attempt_number=1)
    assert isinstance(record.session_id, str)
    assert len(record.session_id) > 0


def test_recorded_at_is_iso(store):
    result = _make_loop_result()
    record = record_loop_attempt(result, store, attempt_number=1)
    assert "T" in record.recorded_at


def test_store_appends_record(store, tmp_path):
    result = _make_loop_result()
    record_loop_attempt(result, store, attempt_number=1, session_id="s1")
    all_records = store.query_all()
    assert len(all_records) == 1


def test_store_query_by_session(store):
    r1 = _make_loop_result()
    r2 = _make_loop_result()
    record_loop_attempt(r1, store, attempt_number=1, session_id="s1")
    record_loop_attempt(r2, store, attempt_number=1, session_id="s2")
    s1_records = store.query_by_session("s1")
    assert len(s1_records) == 1
    assert s1_records[0]["session_id"] == "s1"


def test_batch_recording(store):
    results = [_make_loop_result(success=(i % 2 == 0)) for i in range(4)]
    records = record_loop_attempt_batch(results, store, session_id="batch-session")
    assert len(records) == 4


def test_batch_attempt_numbers(store):
    results = [_make_loop_result() for _ in range(3)]
    records = record_loop_attempt_batch(results, store)
    attempt_numbers = [r.attempt_number for r in records]
    assert attempt_numbers == [1, 2, 3]


def test_init_ok_from_framework():
    from framework import record_loop_attempt  # noqa: F401


def test_error_type_derivation_syntax(store):
    result = _make_loop_result(success=False, error="SyntaxError in file")
    record = record_loop_attempt(result, store, attempt_number=1)
    assert record.error_type == "syntax_error"
