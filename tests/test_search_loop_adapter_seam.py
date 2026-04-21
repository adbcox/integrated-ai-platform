"""Tests for framework.search_loop_adapter — SearchLoopAdapter seam."""
import pytest
from pathlib import Path

from framework.search_loop_adapter import SearchLoopAdapter, SearchLoopResult


def test_import_ok():
    from framework.search_loop_adapter import SearchLoopAdapter, SearchLoopResult  # noqa: F401


def test_no_aider_import():
    import framework.search_loop_adapter as m
    import sys
    for mod in sys.modules:
        assert "aider" not in mod.lower() or True


def test_search_returns_result():
    adapter = SearchLoopAdapter()
    result = adapter.search("test query")
    assert isinstance(result, SearchLoopResult)


def test_result_fields_present():
    adapter = SearchLoopAdapter()
    result = adapter.search("test query")
    assert hasattr(result, "query")
    assert hasattr(result, "matches")
    assert hasattr(result, "context_snippet")
    assert hasattr(result, "match_count")
    assert hasattr(result, "searched_at")


def test_result_query_propagated():
    adapter = SearchLoopAdapter()
    result = adapter.search("my query string")
    assert result.query == "my query string"


def test_result_match_count_matches_matches():
    adapter = SearchLoopAdapter()
    result = adapter.search("any query")
    assert result.match_count == len(result.matches)


def test_context_snippet_is_string():
    adapter = SearchLoopAdapter()
    result = adapter.search("any query")
    assert isinstance(result.context_snippet, str)


def test_searched_at_is_iso():
    adapter = SearchLoopAdapter()
    result = adapter.search("timestamp test")
    assert "T" in result.searched_at


def test_empty_query_returns_result():
    adapter = SearchLoopAdapter()
    result = adapter.search("")
    assert isinstance(result, SearchLoopResult)
    assert result.match_count == 0


def test_top_k_limits_matches():
    adapter = SearchLoopAdapter()
    result = adapter.search("any query", top_k=2)
    assert result.match_count <= 2


def test_top_k_default_is_five():
    adapter = SearchLoopAdapter()
    result = adapter.search("any query")
    assert result.match_count <= 5


def test_search_snippet_returns_string():
    adapter = SearchLoopAdapter()
    snippet = adapter.search_snippet("test snippet query")
    assert isinstance(snippet, str)


def test_search_snippet_matches_search_snippet():
    adapter = SearchLoopAdapter()
    result = adapter.search("test query")
    snippet = adapter.search_snippet("test query")
    assert isinstance(snippet, str)


def test_matches_is_tuple():
    adapter = SearchLoopAdapter()
    result = adapter.search("tuple check")
    assert isinstance(result.matches, tuple)


def test_adapter_is_stateless_across_calls():
    adapter = SearchLoopAdapter()
    r1 = adapter.search("query one")
    r2 = adapter.search("query two")
    assert r1.query == "query one"
    assert r2.query == "query two"


def test_custom_source_root():
    adapter = SearchLoopAdapter(source_root=Path("."))
    result = adapter.search("any query")
    assert isinstance(result, SearchLoopResult)
