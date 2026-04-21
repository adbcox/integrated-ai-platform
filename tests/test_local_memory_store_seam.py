"""Tests for framework.local_memory_store — failure/success memory seam."""
import json
import pytest
from pathlib import Path

from framework.local_memory_store import (
    FailurePattern,
    SuccessPattern,
    LocalMemoryStore,
    record_mvp_loop_outcome,
)


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "memory")


def test_import_ok():
    from framework.local_memory_store import LocalMemoryStore  # noqa: F401


def test_record_failure_returns_failure_pattern(store):
    p = store.record_failure(
        task_kind="text_replacement",
        target_file="framework/foo.py",
        old_string="x = 1",
        error="old_string not found in file",
    )
    assert isinstance(p, FailurePattern)
    assert p.task_kind == "text_replacement"
    assert p.error_type == "old_string_not_found"


def test_record_success_returns_success_pattern(store):
    p = store.record_success(
        task_kind="helper_insertion",
        target_file="framework/bar.py",
        old_string="def foo(): pass",
        new_string="def foo(): pass\n\ndef bar(): pass",
    )
    assert isinstance(p, SuccessPattern)
    assert p.task_kind == "helper_insertion"


def test_read_failures_empty_before_any_write(store):
    assert store.read_failures() == []


def test_read_successes_empty_before_any_write(store):
    assert store.read_successes() == []


def test_read_failures_returns_written_pattern(store):
    store.record_failure(
        task_kind="bug_fix",
        target_file="framework/x.py",
        old_string="broken_call()",
        error="test failed",
    )
    failures = store.read_failures()
    assert len(failures) == 1
    assert failures[0].error_type == "test_failed"


def test_read_successes_returns_written_pattern(store):
    store.record_success(
        task_kind="metadata_addition",
        target_file="framework/y.py",
        old_string="# top",
        new_string="# top\n# version: 2",
    )
    successes = store.read_successes()
    assert len(successes) == 1
    assert successes[0].task_kind == "metadata_addition"


def test_multiple_failures_appended(store):
    for i in range(3):
        store.record_failure(
            task_kind="text_replacement",
            target_file=f"f{i}.py",
            old_string=f"old_{i}",
            error="permission denied path outside writable",
        )
    assert len(store.read_failures()) == 3


def test_query_failures_filters_by_task_kind(store):
    store.record_failure(task_kind="bug_fix", target_file="a.py", old_string="x", error="test failed")
    store.record_failure(task_kind="text_replacement", target_file="b.py", old_string="y", error="not found")
    result = store.query_failures(task_kind="bug_fix")
    assert all(p.task_kind == "bug_fix" for p in result)
    assert len(result) == 1


def test_query_failures_filters_by_error_type(store):
    store.record_failure(task_kind="bug_fix", target_file="a.py", old_string="x", error="test failed")
    store.record_failure(task_kind="bug_fix", target_file="b.py", old_string="y", error="old_string not found in file")
    result = store.query_failures(error_type="old_string_not_found")
    assert len(result) == 1


def test_query_successes_filters_by_task_kind(store):
    store.record_success(task_kind="helper_insertion", target_file="a.py", old_string="x", new_string="y")
    store.record_success(task_kind="bug_fix", target_file="b.py", old_string="p", new_string="q")
    result = store.query_successes(task_kind="helper_insertion")
    assert len(result) == 1


def test_failure_rate_zero_with_only_successes(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    assert store.failure_rate() == 0.0


def test_failure_rate_one_with_only_failures(store):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    assert store.failure_rate() == 1.0


def test_failure_rate_mixed(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    store.record_failure(task_kind="text_replacement", target_file="b.py", old_string="z", error="err")
    assert store.failure_rate() == pytest.approx(0.5)


def test_failure_pattern_to_dict_round_trips(store):
    p = store.record_failure(task_kind="bug_fix", target_file="f.py", old_string="bug", error="test failed")
    d = p.to_dict()
    p2 = FailurePattern.from_dict(d)
    assert p == p2


def test_success_pattern_to_dict_round_trips(store):
    p = store.record_success(task_kind="helper_insertion", target_file="f.py", old_string="x", new_string="y")
    d = p.to_dict()
    p2 = SuccessPattern.from_dict(d)
    assert p == p2


def test_failure_jsonl_is_valid_json(store, tmp_path):
    store.record_failure(task_kind="text_replacement", target_file="f.py", old_string="x", error="err")
    line = (tmp_path / "memory" / "failure_patterns.jsonl").read_text().strip()
    parsed = json.loads(line)
    assert parsed["task_kind"] == "text_replacement"


def test_record_mvp_loop_outcome_success(store):
    class FakeResult:
        success = True
        task_kind = "text_replacement"
        error = None

    record_mvp_loop_outcome(
        FakeResult(),
        target_file="f.py",
        old_string="x = 1",
        new_string="x = 2",
        memory_dir=store._dir,
    )
    assert len(store.read_successes()) == 1
    assert len(store.read_failures()) == 0


def test_record_mvp_loop_outcome_failure(store):
    class FakeResult:
        success = False
        task_kind = "bug_fix"
        error = "old_string not found in file"

    record_mvp_loop_outcome(
        FakeResult(),
        target_file="f.py",
        old_string="broken",
        new_string="fixed",
        memory_dir=store._dir,
    )
    assert len(store.read_failures()) == 1
    assert store.read_failures()[0].error_type == "old_string_not_found"


def test_emit_memory_summary_record_dry_run(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    result = store.emit_memory_summary_record(dry_run=True)
    assert result is None or isinstance(result, str)


def test_classify_error_permission(store):
    p = store.record_failure(task_kind="text_replacement", target_file="f.py", old_string="x", error="path outside writable roots")
    assert p.error_type == "permission_denied"


def test_classify_error_unknown(store):
    p = store.record_failure(task_kind="text_replacement", target_file="f.py", old_string="x", error=None)
    assert p.error_type == "unknown"
