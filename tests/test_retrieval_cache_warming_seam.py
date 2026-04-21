"""Conformance tests for framework/retrieval_cache_warmer.py (ADSC1-RETRIEVAL-CACHE-WARMING-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.retrieval_cache_warmer import CacheWarmingResult, warm_retrieval_cache
from framework.local_memory_store import LocalMemoryStore, SuccessPattern
from framework.retrieval_cache import RetrievalCache


def _iso_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _fake_pattern(task_kind="text_replacement", prefix="old_text"):
    return SuccessPattern(
        task_kind=task_kind,
        target_file_suffix=".py",
        old_string_prefix=prefix,
        new_string_prefix="new_text",
        recorded_at=_iso_now(),
        session_id="s1",
        reuse_count=1,
    )


# --- import and type ---

def test_import_warm_retrieval_cache():
    assert callable(warm_retrieval_cache)


def test_returns_cache_warming_result(tmp_path):
    store = MagicMock(spec=LocalMemoryStore)
    store.query_successes.return_value = []
    cache = MagicMock(spec=RetrievalCache)
    result = warm_retrieval_cache(store, cache, tmp_path)
    assert isinstance(result, CacheWarmingResult)


# --- empty memory ---

def test_empty_memory_zero_attempts(tmp_path):
    store = MagicMock(spec=LocalMemoryStore)
    store.query_successes.return_value = []
    cache = MagicMock(spec=RetrievalCache)
    result = warm_retrieval_cache(store, cache, tmp_path)
    assert result.queries_attempted == 0
    assert result.entries_written == 0


# --- cache miss triggers write ---

def test_cache_miss_triggers_put(tmp_path):
    store = MagicMock(spec=LocalMemoryStore)
    store.query_successes.return_value = [_fake_pattern()]
    cache = MagicMock(spec=RetrievalCache)
    cache.get.return_value = None  # miss
    result = warm_retrieval_cache(store, cache, REPO_ROOT)
    assert result.entries_written == 1
    assert cache.put.called


# --- cache hit skips write ---

def test_cache_hit_skips_put(tmp_path):
    store = MagicMock(spec=LocalMemoryStore)
    store.query_successes.return_value = [_fake_pattern()]
    cache = MagicMock(spec=RetrievalCache)
    cache.get.return_value = MagicMock()  # hit
    result = warm_retrieval_cache(store, cache, REPO_ROOT)
    assert result.entries_written == 0
    assert result.cache_hits_before == 1
    assert not cache.put.called


# --- queries_attempted matches pattern count ---

def test_queries_attempted_matches_patterns(tmp_path):
    patterns = [_fake_pattern(prefix=f"prefix_{i}") for i in range(3)]
    store = MagicMock(spec=LocalMemoryStore)
    store.query_successes.return_value = patterns
    cache = MagicMock(spec=RetrievalCache)
    cache.get.return_value = None
    result = warm_retrieval_cache(store, cache, REPO_ROOT)
    assert result.queries_attempted == 3


# --- errors accumulated not raised ---

def test_errors_accumulated_not_raised(tmp_path):
    store = MagicMock(spec=LocalMemoryStore)
    store.query_successes.return_value = [_fake_pattern()]
    cache = MagicMock(spec=RetrievalCache)
    cache.get.return_value = None
    cache.put.side_effect = RuntimeError("simulated put error")
    result = warm_retrieval_cache(store, cache, REPO_ROOT)
    assert len(result.errors) == 1
    assert result.entries_written == 0


# --- cache_hits_before counted ---

def test_cache_hits_before_accumulated(tmp_path):
    patterns = [_fake_pattern(prefix=f"p{i}") for i in range(3)]
    store = MagicMock(spec=LocalMemoryStore)
    store.query_successes.return_value = patterns
    cache = MagicMock(spec=RetrievalCache)
    cache.get.return_value = MagicMock()  # all hits
    result = warm_retrieval_cache(store, cache, REPO_ROOT)
    assert result.cache_hits_before == 3


def test_warmed_at_timestamp_present(tmp_path):
    store = MagicMock(spec=LocalMemoryStore)
    store.query_successes.return_value = []
    cache = MagicMock(spec=RetrievalCache)
    result = warm_retrieval_cache(store, cache, tmp_path)
    assert isinstance(result.warmed_at, str)
    assert len(result.warmed_at) > 0


# --- package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "warm_retrieval_cache")
    assert hasattr(framework, "CacheWarmingResult")
