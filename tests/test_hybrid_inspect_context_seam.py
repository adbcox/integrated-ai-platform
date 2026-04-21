"""Conformance tests for framework/hybrid_inspect_context.py (LARAC2-RETRIEVAL-PATTERN-INSPECT-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.hybrid_inspect_context import HybridInspectContext, build_hybrid_inspect_context
from framework.retrieval_cache import CachedRetrievalResult
from framework.repo_pattern_store import PatternEntry


def _mock_cache(files=None):
    cache = MagicMock()
    if files is None:
        cache.get.return_value = None
    else:
        hit = CachedRetrievalResult(
            cache_key="k",
            query_text="q",
            top_k=5,
            result_dict={"files": files},
            cached_at="now",
            ttl_seconds=600,
        )
        cache.get.return_value = hit
    return cache


def _mock_lib(entries=None):
    lib = MagicMock()
    lib.query.return_value = entries or []
    return lib


def _mock_adapter(snippet="search result"):
    adapter = MagicMock()
    adapter.search_snippet.return_value = snippet
    return adapter


def _entry(task_kind="text_replacement", prefix="old val"):
    return PatternEntry(
        task_kind=task_kind,
        target_file_suffix=".py",
        old_string_prefix=prefix,
        new_string_prefix="new val",
        reuse_count=1,
        recorded_at="2026-01-01T00:00:00+00:00",
    )


# --- import and type ---

def test_import_build_hybrid_inspect_context():
    assert callable(build_hybrid_inspect_context)


def test_returns_hybrid_inspect_context():
    ctx = build_hybrid_inspect_context("q")
    assert isinstance(ctx, HybridInspectContext)


# --- fields ---

def test_context_fields_present():
    ctx = build_hybrid_inspect_context("q")
    assert hasattr(ctx, "query")
    assert hasattr(ctx, "cache_snippet")
    assert hasattr(ctx, "pattern_hints")
    assert hasattr(ctx, "search_snippet")
    assert hasattr(ctx, "context_sources")
    assert hasattr(ctx, "error_notes")


# --- all-none inputs return empty context ---

def test_all_none_returns_empty():
    ctx = build_hybrid_inspect_context("q")
    assert ctx.cache_snippet == ""
    assert ctx.pattern_hints == []
    assert ctx.search_snippet == ""
    assert ctx.context_sources == []


# --- cache step ---

def test_cache_snippet_populated():
    cache = _mock_cache(files=[{"path": "framework/foo.py", "snippet": "x"}])
    ctx = build_hybrid_inspect_context("q", cache=cache)
    assert "framework/foo.py" in ctx.cache_snippet
    assert "retrieval_cache" in ctx.context_sources


def test_cache_miss_is_empty():
    cache = _mock_cache(files=None)
    ctx = build_hybrid_inspect_context("q", cache=cache)
    assert ctx.cache_snippet == ""


# --- pattern step ---

def test_pattern_hints_populated():
    lib = _mock_lib([_entry("text_replacement", "old val"), _entry("add_import", "import x")])
    ctx = build_hybrid_inspect_context("q", pattern_library=lib)
    assert len(ctx.pattern_hints) == 2
    assert "pattern_library" in ctx.context_sources


# --- search step ---

def test_search_snippet_populated():
    adapter = _mock_adapter("found something")
    ctx = build_hybrid_inspect_context("q", search_adapter=adapter)
    assert ctx.search_snippet == "found something"
    assert "search" in ctx.context_sources


# --- failures non-blocking ---

def test_cache_failure_non_blocking():
    cache = MagicMock()
    cache.get.side_effect = RuntimeError("cache down")
    ctx = build_hybrid_inspect_context("q", cache=cache)
    assert any("cache_error" in n for n in ctx.error_notes)


def test_search_failure_non_blocking():
    adapter = MagicMock()
    adapter.search_snippet.side_effect = RuntimeError("search down")
    ctx = build_hybrid_inspect_context("q", search_adapter=adapter)
    assert any("search_error" in n for n in ctx.error_notes)


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "HybridInspectContext")
    assert hasattr(framework, "build_hybrid_inspect_context")
