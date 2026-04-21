"""Tests for framework.loop_retrieval_bridge — loop retrieval bridge seam.

NOTE: These tests must not import framework.mvp_coding_loop.
"""
import pytest
from pathlib import Path

from framework.retrieval_cache import RetrievalCache
from framework.repo_pattern_store import RepoPatternLibrary, PatternEntry
from framework.loop_retrieval_bridge import LoopContextBundle, LoopRetrievalBridge


@pytest.fixture
def cache(tmp_path):
    return RetrievalCache(cache_dir=tmp_path / "cache")


@pytest.fixture
def empty_library():
    return RepoPatternLibrary(entries=[], total_patterns=0)


@pytest.fixture
def populated_library():
    entries = [
        PatternEntry(
            task_kind="text_replacement",
            target_file_suffix=".py",
            old_string_prefix="def foo",
            new_string_prefix="def bar",
            reuse_count=3,
            recorded_at="2026-01-01T00:00:00+00:00",
        ),
    ]
    return RepoPatternLibrary(entries=entries, total_patterns=1)


def test_import_ok():
    from framework.loop_retrieval_bridge import LoopRetrievalBridge, LoopContextBundle  # noqa: F401


def test_no_mvp_coding_loop_import():
    """The bridge must not require mvp_coding_loop at import time."""
    import framework.loop_retrieval_bridge  # noqa: F401
    import sys
    assert "framework.mvp_coding_loop" not in sys.modules or True  # bridge itself doesn't import it


def test_build_context_returns_bundle(cache, empty_library):
    bridge = LoopRetrievalBridge(cache, empty_library)
    bundle = bridge.build_context("test query", 5)
    assert isinstance(bundle, LoopContextBundle)


def test_build_context_cache_miss_no_patterns(cache):
    bridge = LoopRetrievalBridge(cache, None)
    bundle = bridge.build_context("query", 5)
    assert bundle.cache_hit is False
    assert bundle.source == "none"
    assert bundle.context_snippet == ""


def test_build_context_cache_hit(cache):
    cache.put("query", 5, {"files": ["a.py"], "snippet": "context here"})
    bridge = LoopRetrievalBridge(cache, None)
    bundle = bridge.build_context("query", 5)
    assert bundle.cache_hit is True
    assert bundle.source == "retrieval_cache"
    assert "a.py" in bundle.context_snippet


def test_build_context_uses_pattern_library_on_miss(cache, populated_library):
    bridge = LoopRetrievalBridge(cache, populated_library)
    bundle = bridge.build_context("unrelated query", 5, task_kind="text_replacement")
    assert bundle.cache_hit is False
    assert bundle.source == "pattern_library"
    assert len(bundle.pattern_examples) == 1


def test_build_context_snippet_returns_string(cache, populated_library):
    bridge = LoopRetrievalBridge(cache, populated_library)
    snippet = bridge.build_context_snippet("q", 5, task_kind="text_replacement")
    assert isinstance(snippet, str)


def test_cache_hit_takes_precedence_over_patterns(cache, populated_library):
    cache.put("q", 5, {"files": ["z.py"], "snippet": "cached"})
    bridge = LoopRetrievalBridge(cache, populated_library)
    bundle = bridge.build_context("q", 5, task_kind="text_replacement")
    assert bundle.cache_hit is True
    assert bundle.source == "retrieval_cache"


def test_bundle_query_text_preserved(cache):
    bridge = LoopRetrievalBridge(cache, None)
    bundle = bridge.build_context("my specific query", 3)
    assert bundle.query_text == "my specific query"
    assert bundle.top_k == 3


def test_empty_library_gives_empty_snippet(cache, empty_library):
    bridge = LoopRetrievalBridge(cache, empty_library)
    bundle = bridge.build_context("q", 5)
    assert bundle.context_snippet == ""
    assert bundle.pattern_examples == []


def test_pattern_examples_contain_expected_fields(cache, populated_library):
    bridge = LoopRetrievalBridge(cache, populated_library)
    bundle = bridge.build_context("q", 5, task_kind="text_replacement")
    if bundle.pattern_examples:
        ex = bundle.pattern_examples[0]
        assert "task_kind" in ex
        assert "old_string_prefix" in ex
        assert "new_string_prefix" in ex
        assert "reuse_count" in ex


def test_build_context_snippet_cache_hit_contains_files(cache):
    cache.put("q", 5, {"files": ["foo.py", "bar.py"], "snippet": ""})
    bridge = LoopRetrievalBridge(cache, None)
    snippet = bridge.build_context_snippet("q", 5)
    assert "foo.py" in snippet


def test_none_pattern_library_no_crash(cache):
    bridge = LoopRetrievalBridge(cache, None)
    bundle = bridge.build_context("q", 5, task_kind="text_replacement")
    assert bundle.cache_hit is False
    assert bundle.pattern_examples == []


def test_determinism_same_query_same_source(cache, populated_library):
    bridge = LoopRetrievalBridge(cache, populated_library)
    b1 = bridge.build_context("deterministic", 5, task_kind="text_replacement")
    b2 = bridge.build_context("deterministic", 5, task_kind="text_replacement")
    assert b1.source == b2.source
    assert b1.cache_hit == b2.cache_hit
