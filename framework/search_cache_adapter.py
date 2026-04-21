"""CachedSearchAdapter — wraps SearchLoopAdapter with RetrievalCache for deduplication.

Inspection gate output:
  SearchLoopAdapter.search sig: (self, query: str, top_k: int = 5) -> SearchLoopResult
  RetrievalCache.get sig: (self, query_text: str, top_k: int) -> Optional[CachedRetrievalResult]
  RetrievalCache.put sig: (self, query_text: str, top_k: int, result_dict: dict) -> CachedRetrievalResult
  CachedRetrievalResult fields: cache_key, query_text, top_k, result_dict, cached_at, ttl_seconds
  SearchLoopResult fields: query, matches, context_snippet, match_count, searched_at
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from framework.retrieval_cache import RetrievalCache
from framework.search_loop_adapter import SearchLoopAdapter, SearchLoopResult

assert callable(SearchLoopAdapter), "INTERFACE MISMATCH: SearchLoopAdapter not callable"
assert callable(RetrievalCache), "INTERFACE MISMATCH: RetrievalCache not callable"


def _result_to_dict(result: SearchLoopResult) -> dict:
    return {
        "query": result.query,
        "matches": list(result.matches),
        "context_snippet": result.context_snippet,
        "match_count": result.match_count,
        "searched_at": result.searched_at,
    }


def _dict_to_result(d: dict) -> SearchLoopResult:
    return SearchLoopResult(
        query=d.get("query", ""),
        matches=tuple(d.get("matches", [])),
        context_snippet=d.get("context_snippet", ""),
        match_count=d.get("match_count", 0),
        searched_at=d.get("searched_at", ""),
    )


class CachedSearchAdapter:
    """Wraps SearchLoopAdapter with RetrievalCache to deduplicate repeated queries."""

    def __init__(
        self,
        search_adapter: Optional[SearchLoopAdapter] = None,
        cache: Optional[RetrievalCache] = None,
        cache_dir: Optional[Path] = None,
    ) -> None:
        self._adapter = search_adapter if search_adapter is not None else SearchLoopAdapter()
        self._cache = cache if cache is not None else RetrievalCache(
            cache_dir=cache_dir or Path("artifacts") / "search_cache"
        )
        self._hits = 0
        self._misses = 0

    def search(self, query: str, top_k: int = 5) -> SearchLoopResult:
        cached = self._cache.get(query_text=query, top_k=top_k)
        if cached is not None and not cached.is_expired():
            self._hits += 1
            return _dict_to_result(cached.result_dict)
        self._misses += 1
        result = self._adapter.search(query, top_k=top_k)
        self._cache.put(query_text=query, top_k=top_k, result_dict=_result_to_dict(result))
        return result

    def search_snippet(self, query: str, top_k: int = 5) -> str:
        return self.search(query, top_k=top_k).context_snippet

    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total": total,
            "hit_rate": self._hits / total if total > 0 else 0.0,
        }


__all__ = ["CachedSearchAdapter"]
