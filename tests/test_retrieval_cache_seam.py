"""Tests for framework.retrieval_cache — disk-backed retrieval cache seam."""
import json
import time
import pytest
from pathlib import Path

from framework.retrieval_cache import CachedRetrievalResult, RetrievalCache


@pytest.fixture
def cache(tmp_path):
    return RetrievalCache(cache_dir=tmp_path / "cache")


@pytest.fixture
def sample_result():
    return {"files": ["a.py", "b.py"], "snippet": "some code"}


def test_import_ok():
    from framework.retrieval_cache import RetrievalCache, CachedRetrievalResult  # noqa: F401


def test_cache_miss_returns_none(cache):
    assert cache.get("missing query", 5) is None


def test_cache_hit_returns_entry(cache, sample_result):
    cache.put("hello world", 5, sample_result)
    entry = cache.get("hello world", 5)
    assert entry is not None
    assert entry.result_dict == sample_result


def test_cache_key_is_deterministic(cache, sample_result):
    cache.put("my query", 3, sample_result)
    e1 = cache.get("my query", 3)
    e2 = cache.get("my query", 3)
    assert e1 is not None and e2 is not None
    assert e1.cache_key == e2.cache_key


def test_different_top_k_separate_entries(cache, sample_result):
    cache.put("query", 3, sample_result)
    cache.put("query", 5, {"files": ["c.py"]})
    e3 = cache.get("query", 3)
    e5 = cache.get("query", 5)
    assert e3 is not None and e5 is not None
    assert e3.cache_key != e5.cache_key


def test_different_queries_separate_entries(cache, sample_result):
    cache.put("query A", 5, sample_result)
    cache.put("query B", 5, {"files": []})
    assert cache.get("query A", 5) is not None
    assert cache.get("query B", 5) is not None


def test_expired_entry_returns_none(tmp_path, sample_result):
    fast_cache = RetrievalCache(cache_dir=tmp_path / "cache", ttl_seconds=0)
    fast_cache.put("q", 1, sample_result)
    time.sleep(0.01)
    assert fast_cache.get("q", 1) is None


def test_is_expired_false_for_fresh(cache, sample_result):
    entry = cache.put("q", 1, sample_result)
    assert not entry.is_expired()


def test_invalidate_removes_entry(cache, sample_result):
    cache.put("q", 1, sample_result)
    removed = cache.invalidate("q", 1)
    assert removed is True
    assert cache.get("q", 1) is None


def test_invalidate_missing_returns_false(cache):
    assert cache.invalidate("not there", 5) is False


def test_clear_removes_all_entries(cache, sample_result):
    cache.put("q1", 1, sample_result)
    cache.put("q2", 2, sample_result)
    count = cache.clear()
    assert count == 2
    assert cache.get("q1", 1) is None
    assert cache.get("q2", 2) is None


def test_clear_empty_cache(cache):
    count = cache.clear()
    assert count == 0


def test_stats_zero_on_empty(cache):
    s = cache.stats()
    assert s["total_entries"] == 0


def test_stats_counts_entries(cache, sample_result):
    cache.put("q1", 1, sample_result)
    cache.put("q2", 2, sample_result)
    assert cache.stats()["total_entries"] == 2


def test_put_returns_cached_result(cache, sample_result):
    entry = cache.put("q", 5, sample_result)
    assert isinstance(entry, CachedRetrievalResult)
    assert entry.query_text == "q"
    assert entry.top_k == 5


def test_cached_at_is_iso_string(cache, sample_result):
    entry = cache.put("q", 1, sample_result)
    assert "T" in entry.cached_at
    assert "+" in entry.cached_at or entry.cached_at.endswith("Z")
