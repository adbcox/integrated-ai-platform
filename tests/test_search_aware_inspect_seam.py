"""Conformance tests for framework/search_aware_inspect.py (LARAC2-SEARCH-ADOPTION-SEAM-1)."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.search_aware_inspect import SearchAwareInspectRunner, SearchAwareInspectResult
from framework.search_loop_adapter import SearchLoopResult
from framework.workspace_scope import ToolPathScope


def _mock_adapter(snippet="test snippet", match_count=2):
    adapter = MagicMock()
    result = SearchLoopResult(
        query="q",
        matches=("m1",),
        context_snippet=snippet,
        match_count=match_count,
        searched_at="2026-01-01T00:00:00+00:00",
    )
    adapter.search.return_value = result
    return adapter


def _scope(tmp_path):
    return ToolPathScope(source_root=tmp_path)


def _runner(adapter, tmp_path):
    return SearchAwareInspectRunner(search_adapter=adapter, source_root=tmp_path)


# --- import and type ---

def test_import_search_aware_inspect_runner():
    assert callable(SearchAwareInspectRunner)


def test_returns_result_type(tmp_path):
    r = _runner(_mock_adapter(), tmp_path).run("nonexistent.py")
    assert isinstance(r, SearchAwareInspectResult)


# --- fields ---

def test_result_fields_present(tmp_path):
    r = _runner(_mock_adapter(), tmp_path).run("nonexistent.py")
    assert hasattr(r, "path")
    assert hasattr(r, "content")
    assert hasattr(r, "inspect_error")
    assert hasattr(r, "search_query")
    assert hasattr(r, "context_snippet")
    assert hasattr(r, "search_error")
    assert hasattr(r, "search_match_count")


# --- search behavior ---

def test_search_called_when_query_set(tmp_path):
    adapter = _mock_adapter()
    _runner(adapter, tmp_path).run("x.py", search_query="find something")
    adapter.search.assert_called_once()


def test_search_not_called_when_no_query(tmp_path):
    adapter = _mock_adapter()
    _runner(adapter, tmp_path).run("x.py")
    adapter.search.assert_not_called()


def test_context_snippet_populated(tmp_path):
    r = _runner(_mock_adapter(snippet="hello ctx"), tmp_path).run("x.py", search_query="q")
    assert r.context_snippet == "hello ctx"


def test_match_count_populated(tmp_path):
    r = _runner(_mock_adapter(match_count=7), tmp_path).run("x.py", search_query="q")
    assert r.search_match_count == 7


# --- search failure is non-blocking ---

def test_search_failure_non_blocking(tmp_path):
    adapter = MagicMock()
    adapter.search.side_effect = RuntimeError("network error")
    r = SearchAwareInspectRunner(search_adapter=adapter, source_root=tmp_path).run(
        "x.py", search_query="something"
    )
    assert r.search_error is not None
    assert "network error" in r.search_error


def test_search_failure_returns_empty_snippet(tmp_path):
    adapter = MagicMock()
    adapter.search.side_effect = RuntimeError("oops")
    r = SearchAwareInspectRunner(search_adapter=adapter, source_root=tmp_path).run(
        "x.py", search_query="q"
    )
    assert r.context_snippet == ""


# --- inspect behavior ---

def test_inspect_reads_real_file(tmp_path):
    f = tmp_path / "hello.py"
    f.write_text("print('hi')")
    r = SearchAwareInspectRunner(source_root=tmp_path).run("hello.py")
    assert r.content == "print('hi')"
    assert r.inspect_error is None


def test_inspect_error_on_missing_file(tmp_path):
    r = SearchAwareInspectRunner(source_root=tmp_path).run("missing.py")
    assert r.inspect_error is not None


# --- empty query path ---

def test_empty_query_behaves_like_plain_inspect(tmp_path):
    f = tmp_path / "code.py"
    f.write_text("x = 1")
    r = SearchAwareInspectRunner(source_root=tmp_path).run("code.py", search_query="")
    assert r.content == "x = 1"
    assert r.context_snippet == ""
    assert r.search_error is None


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "SearchAwareInspectRunner")
    assert hasattr(framework, "SearchAwareInspectResult")
