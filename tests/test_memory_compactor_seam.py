"""Tests for framework.memory_compactor — memory compaction seam."""
import json
import pytest
from pathlib import Path

from framework.local_memory_store import LocalMemoryStore
from framework.memory_compactor import (
    MemoryCompactionResult,
    compact_failure_patterns,
    compact_memory,
    compact_success_patterns,
)


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "memory")


def test_import_ok():
    from framework.memory_compactor import compact_memory, MemoryCompactionResult  # noqa: F401


def test_memory_compaction_result_is_frozen():
    r = MemoryCompactionResult(
        failures_before=0, failures_after=0, successes_before=0,
        successes_after=0, compacted_at="2026-01-01T00:00:00+00:00", dry_run=True,
    )
    with pytest.raises((AttributeError, TypeError)):
        r.failures_before = 99  # type: ignore[misc]


def test_compact_failures_empty_store(store):
    result = compact_failure_patterns(store, dry_run=True)
    assert result.failures_before == 0
    assert result.failures_after == 0


def test_compact_successes_empty_store(store):
    result = compact_success_patterns(store, dry_run=True)
    assert result.successes_before == 0
    assert result.successes_after == 0


def test_compact_memory_empty_store(store):
    result = compact_memory(store, dry_run=True)
    assert result.failures_before == 0
    assert result.successes_before == 0
    assert result.dry_run is True


def test_compact_failures_no_duplicates(store):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    store.record_failure(task_kind="bug_fix", target_file="b.py", old_string="y", error="err2")
    result = compact_failure_patterns(store, dry_run=True)
    assert result.failures_before == 2
    assert result.failures_after == 2


def test_compact_failures_deduplicates(store):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    result = compact_failure_patterns(store, dry_run=True)
    assert result.failures_before == 2
    assert result.failures_after == 1


def test_compact_successes_deduplicates(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    result = compact_success_patterns(store, dry_run=True)
    assert result.successes_before == 2
    assert result.successes_after == 1


def test_compact_failures_dry_run_does_not_rewrite(store):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    compact_failure_patterns(store, dry_run=True)
    # Still 2 records after dry-run
    assert len(store.read_failures()) == 2


def test_compact_failures_rewrite_deduplicates_on_disk(store):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    compact_failure_patterns(store, dry_run=False)
    assert len(store.read_failures()) == 1


def test_compact_successes_rewrite_deduplicates_on_disk(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    compact_success_patterns(store, dry_run=False)
    assert len(store.read_successes()) == 1


def test_compact_failure_merges_recurrence_count(store):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    compact_failure_patterns(store, dry_run=False)
    records = store.read_failures()
    assert len(records) == 1
    assert records[0].recurrence_count >= 2


def test_compact_success_merges_reuse_count(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    compact_success_patterns(store, dry_run=False)
    records = store.read_successes()
    assert len(records) == 1
    assert records[0].reuse_count >= 2


def test_compact_memory_combined_counts(store):
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    store.record_failure(task_kind="text_replacement", target_file="a.py", old_string="x", error="err")
    store.record_success(task_kind="bug_fix", target_file="b.py", old_string="y", new_string="z")
    result = compact_memory(store, dry_run=True)
    assert result.failures_before == 2
    assert result.successes_before == 1


def test_compacted_at_is_iso_string(store):
    result = compact_memory(store, dry_run=True)
    assert "T" in result.compacted_at
    assert result.compacted_at.endswith("+00:00") or result.compacted_at.endswith("Z")
