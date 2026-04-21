"""Tests for framework.repo_pattern_store — repo pattern library seam."""
import json
import pytest
from pathlib import Path

from framework.local_memory_store import LocalMemoryStore
from framework.repo_pattern_store import (
    PatternEntry,
    RepoPatternLibrary,
    build_repo_pattern_library,
    save_repo_pattern_library,
)


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "memory")


@pytest.fixture
def artifact_dir(tmp_path):
    return tmp_path / "patterns"


def test_import_ok():
    from framework.repo_pattern_store import build_repo_pattern_library, RepoPatternLibrary  # noqa: F401


def test_pattern_entry_is_frozen():
    e = PatternEntry(
        task_kind="text_replacement", target_file_suffix=".py",
        old_string_prefix="x", new_string_prefix="y", reuse_count=1,
        recorded_at="2026-01-01T00:00:00+00:00",
    )
    with pytest.raises((AttributeError, TypeError)):
        e.reuse_count = 99  # type: ignore[misc]


def test_build_empty_store(store):
    lib = build_repo_pattern_library(store)
    assert isinstance(lib, RepoPatternLibrary)
    assert lib.total_patterns == 0
    assert lib.entries == []


def test_build_with_one_success(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    lib = build_repo_pattern_library(store)
    assert lib.total_patterns == 1
    assert lib.entries[0].task_kind == "text_replacement"


def test_build_aggregates_reuse_count(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    lib = build_repo_pattern_library(store)
    assert lib.total_patterns == 1
    assert lib.entries[0].reuse_count >= 2


def test_build_keeps_distinct_keys_separate(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    store.record_success(task_kind="bug_fix", target_file="b.py", old_string="z", new_string="w")
    lib = build_repo_pattern_library(store)
    assert lib.total_patterns == 2


def test_query_no_filter(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    lib = build_repo_pattern_library(store)
    results = lib.query()
    assert len(results) == 1


def test_query_filters_by_task_kind(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    store.record_success(task_kind="bug_fix", target_file="b.py", old_string="z", new_string="w")
    lib = build_repo_pattern_library(store)
    results = lib.query(task_kind="text_replacement")
    assert all(e.task_kind == "text_replacement" for e in results)
    assert len(results) == 1


def test_query_sorts_by_reuse_count_desc(store):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    store.record_success(task_kind="bug_fix", target_file="b.py", old_string="z", new_string="w")
    lib = build_repo_pattern_library(store)
    results = lib.query()
    counts = [e.reuse_count for e in results]
    assert counts == sorted(counts, reverse=True)


def test_save_dry_run_no_file(store, artifact_dir):
    lib = build_repo_pattern_library(store)
    result = save_repo_pattern_library(lib, artifact_dir=artifact_dir, dry_run=True)
    assert result is None
    assert not artifact_dir.exists()


def test_save_writes_file(store, artifact_dir):
    lib = build_repo_pattern_library(store)
    path = save_repo_pattern_library(lib, artifact_dir=artifact_dir, dry_run=False)
    assert path is not None
    assert Path(path).exists()


def test_save_json_is_valid(store, artifact_dir):
    store.record_success(task_kind="text_replacement", target_file="a.py", old_string="x", new_string="y")
    lib = build_repo_pattern_library(store)
    path = save_repo_pattern_library(lib, artifact_dir=artifact_dir, dry_run=False)
    data = json.loads(Path(path).read_text())
    assert "schema_version" in data
    assert "entries" in data
    assert "built_at" in data


def test_to_dict_keys(store):
    lib = build_repo_pattern_library(store)
    d = lib.to_dict()
    assert "schema_version" in d
    assert "total_patterns" in d
    assert "entries" in d


def test_built_at_is_iso(store):
    lib = build_repo_pattern_library(store)
    assert "T" in lib.built_at
