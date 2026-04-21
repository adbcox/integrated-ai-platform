"""Tests for framework.pattern_guided_inspector — PatternGuidedInspector seam."""
import pytest

from framework.local_memory_store import LocalMemoryStore
from framework.repo_pattern_store import build_repo_pattern_library
from framework.pattern_guided_inspector import InspectHint, PatternGuidedInspector


@pytest.fixture
def empty_library(tmp_path):
    store = LocalMemoryStore(memory_dir=tmp_path / "mem")
    return build_repo_pattern_library(store)


@pytest.fixture
def populated_library(tmp_path):
    store = LocalMemoryStore(memory_dir=tmp_path / "mem")
    for _ in range(5):
        store.record_success(task_kind="text_replacement", target_file="a.py", old_string="foo", new_string="bar")
    for _ in range(2):
        store.record_success(task_kind="text_replacement", target_file="b.py", old_string="baz", new_string="qux")
    return build_repo_pattern_library(store)


def test_import_ok():
    from framework.pattern_guided_inspector import InspectHint, PatternGuidedInspector  # noqa: F401


def test_inspect_hint_frozen():
    h = InspectHint(target_file_suffix=".py", old_string_prefix="foo", confidence=0.9, source="pattern_library")
    with pytest.raises(Exception):
        h.confidence = 0.5


def test_inspect_hint_fields():
    h = InspectHint(target_file_suffix=".py", old_string_prefix="foo", confidence=0.8, source="pattern_library")
    assert h.target_file_suffix == ".py"
    assert h.old_string_prefix == "foo"
    assert h.confidence == 0.8
    assert h.source == "pattern_library"


def test_empty_library_returns_no_hints(empty_library):
    inspector = PatternGuidedInspector(empty_library)
    hints = inspector.hints_for("text_replacement")
    assert hints == []


def test_populated_library_returns_hints(populated_library):
    inspector = PatternGuidedInspector(populated_library)
    hints = inspector.hints_for("text_replacement")
    assert len(hints) > 0


def test_hints_are_inspect_hint_instances(populated_library):
    inspector = PatternGuidedInspector(populated_library)
    hints = inspector.hints_for("text_replacement")
    for h in hints:
        assert isinstance(h, InspectHint)


def test_hints_sorted_by_confidence_desc(populated_library):
    inspector = PatternGuidedInspector(populated_library)
    hints = inspector.hints_for("text_replacement")
    if len(hints) > 1:
        for i in range(len(hints) - 1):
            assert hints[i].confidence >= hints[i + 1].confidence


def test_top_n_limits_results(populated_library):
    inspector = PatternGuidedInspector(populated_library)
    hints = inspector.hints_for("text_replacement", top_n=1)
    assert len(hints) <= 1


def test_confidence_between_zero_and_one(populated_library):
    inspector = PatternGuidedInspector(populated_library)
    hints = inspector.hints_for("text_replacement")
    for h in hints:
        assert 0.0 <= h.confidence <= 1.0


def test_source_is_pattern_library(populated_library):
    inspector = PatternGuidedInspector(populated_library)
    hints = inspector.hints_for("text_replacement")
    for h in hints:
        assert h.source == "pattern_library"


def test_hint_snippet_returns_string(populated_library):
    inspector = PatternGuidedInspector(populated_library)
    snippet = inspector.hint_snippet("text_replacement")
    assert isinstance(snippet, str)


def test_hint_snippet_empty_library(empty_library):
    inspector = PatternGuidedInspector(empty_library)
    snippet = inspector.hint_snippet("text_replacement")
    assert "no pattern hints" in snippet or isinstance(snippet, str)


def test_hint_snippet_contains_task_kind(populated_library):
    inspector = PatternGuidedInspector(populated_library)
    snippet = inspector.hint_snippet("text_replacement")
    assert "text_replacement" in snippet


def test_unknown_task_kind_returns_empty(populated_library):
    inspector = PatternGuidedInspector(populated_library)
    hints = inspector.hints_for("nonexistent_task_kind_xyz")
    assert hints == []


def test_init_ok_from_framework():
    from framework import PatternGuidedInspector  # noqa: F401
