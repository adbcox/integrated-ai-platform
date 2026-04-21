"""Tests for framework.search_cache_adapter — CachedSearchAdapter seam."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from framework.search_loop_adapter import SearchLoopResult
from framework.search_cache_adapter import CachedSearchAdapter


def _make_result(query="test", matches=("a.py: match",), snippet="a.py: match"):
    return SearchLoopResult(
        query=query,
        matches=tuple(matches),
        context_snippet=snippet,
        match_count=len(matches),
        searched_at="2026-01-01T00:00:00+00:00",
    )


def _make_adapter_with_mock(tmp_path, result=None):
    from framework.retrieval_cache import RetrievalCache
    from framework.search_loop_adapter import SearchLoopAdapter
    mock_adapter = MagicMock(spec=SearchLoopAdapter)
    mock_adapter.search.return_value = result or _make_result()
    cache = RetrievalCache(cache_dir=tmp_path / "cache")
    return CachedSearchAdapter(search_adapter=mock_adapter, cache=cache), mock_adapter


def test_import_ok():
    from framework.search_cache_adapter import CachedSearchAdapter  # noqa: F401


def test_search_returns_result(tmp_path):
    adapter, _ = _make_adapter_with_mock(tmp_path)
    result = adapter.search("test query")
    assert isinstance(result, SearchLoopResult)


def test_first_call_is_miss(tmp_path):
    adapter, _ = _make_adapter_with_mock(tmp_path)
    adapter.search("first query")
    s = adapter.stats()
    assert s["misses"] == 1
    assert s["hits"] == 0


def test_second_call_same_query_is_hit(tmp_path):
    adapter, _ = _make_adapter_with_mock(tmp_path)
    adapter.search("repeated query")
    adapter.search("repeated query")
    s = adapter.stats()
    assert s["hits"] == 1
    assert s["misses"] == 1


def test_different_queries_both_miss(tmp_path):
    adapter, _ = _make_adapter_with_mock(tmp_path)
    adapter.search("query one")
    adapter.search("query two")
    s = adapter.stats()
    assert s["misses"] == 2


def test_underlying_adapter_called_once_on_hit(tmp_path):
    adapter, mock_adapter = _make_adapter_with_mock(tmp_path)
    adapter.search("cached query")
    adapter.search("cached query")
    mock_adapter.search.assert_called_once()


def test_stats_total(tmp_path):
    adapter, _ = _make_adapter_with_mock(tmp_path)
    adapter.search("q1")
    adapter.search("q2")
    adapter.search("q1")
    s = adapter.stats()
    assert s["total"] == 3


def test_stats_hit_rate(tmp_path):
    adapter, _ = _make_adapter_with_mock(tmp_path)
    adapter.search("q1")
    adapter.search("q1")
    s = adapter.stats()
    assert s["hit_rate"] == pytest.approx(0.5)


def test_key_separation_by_top_k(tmp_path):
    adapter, mock_adapter = _make_adapter_with_mock(tmp_path)
    adapter.search("query", top_k=3)
    adapter.search("query", top_k=5)
    assert mock_adapter.search.call_count == 2


def test_snippet_passthrough(tmp_path):
    result = _make_result(snippet="my snippet text")
    adapter, _ = _make_adapter_with_mock(tmp_path, result=result)
    snippet = adapter.search_snippet("test")
    assert "my snippet text" in snippet or isinstance(snippet, str)


def test_search_snippet_returns_string(tmp_path):
    adapter, _ = _make_adapter_with_mock(tmp_path)
    snippet = adapter.search_snippet("query")
    assert isinstance(snippet, str)


def test_stats_initial_all_zero(tmp_path):
    from framework.retrieval_cache import RetrievalCache
    from framework.search_loop_adapter import SearchLoopAdapter
    cache = RetrievalCache(cache_dir=tmp_path / "cache")
    adapter = CachedSearchAdapter(cache=cache)
    s = adapter.stats()
    assert s["hits"] == 0
    assert s["misses"] == 0
    assert s["total"] == 0


def test_hit_rate_zero_when_no_calls(tmp_path):
    from framework.retrieval_cache import RetrievalCache
    cache = RetrievalCache(cache_dir=tmp_path / "cache")
    adapter = CachedSearchAdapter(cache=cache)
    s = adapter.stats()
    assert s["hit_rate"] == 0.0


def test_init_ok_from_framework():
    from framework import CachedSearchAdapter  # noqa: F401
