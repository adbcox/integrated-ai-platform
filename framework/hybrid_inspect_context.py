"""HybridInspectContext: combines retrieval cache, repo-pattern results, and search output."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from framework.retrieval_cache import RetrievalCache, CachedRetrievalResult
from framework.repo_pattern_store import RepoPatternLibrary, PatternEntry
from framework.search_loop_adapter import SearchLoopAdapter

# -- import-time assertions --
assert "cache_key" in CachedRetrievalResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: CachedRetrievalResult.cache_key"
assert "result_dict" in CachedRetrievalResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: CachedRetrievalResult.result_dict"
assert "task_kind" in PatternEntry.__dataclass_fields__, \
    "INTERFACE MISMATCH: PatternEntry.task_kind"
assert "old_string_prefix" in PatternEntry.__dataclass_fields__, \
    "INTERFACE MISMATCH: PatternEntry.old_string_prefix"
assert callable(getattr(RetrievalCache, "get", None)), \
    "INTERFACE MISMATCH: RetrievalCache.get"
assert callable(getattr(RepoPatternLibrary, "query", None)), \
    "INTERFACE MISMATCH: RepoPatternLibrary.query"
assert callable(getattr(SearchLoopAdapter, "search_snippet", None)), \
    "INTERFACE MISMATCH: SearchLoopAdapter.search_snippet"


@dataclass(frozen=True)
class HybridInspectContext:
    query: str
    cache_snippet: str
    pattern_hints: List[str]
    search_snippet: str
    context_sources: List[str]
    error_notes: List[str]


def build_hybrid_inspect_context(
    query: str,
    *,
    cache: Optional[RetrievalCache] = None,
    pattern_library: Optional[RepoPatternLibrary] = None,
    search_adapter: Optional[SearchLoopAdapter] = None,
    top_k: int = 5,
    task_kind: Optional[str] = None,
) -> HybridInspectContext:
    cache_snippet = ""
    pattern_hints: List[str] = []
    search_snip = ""
    context_sources: List[str] = []
    error_notes: List[str] = []

    # Step 1: retrieval cache hit (non-blocking)
    if cache is not None:
        try:
            hit: Optional[CachedRetrievalResult] = cache.get(query, top_k)
            if hit is not None:
                rd = hit.result_dict or {}
                files = rd.get("files", [])
                if files:
                    cache_snippet = "; ".join(
                        str(f.get("path", f.get("snippet", ""))) for f in files[:3]
                    )
                    context_sources.append("retrieval_cache")
        except Exception as exc:
            error_notes.append(f"cache_error: {exc}")

    # Step 2: pattern library query (non-blocking)
    if pattern_library is not None:
        try:
            entries = pattern_library.query(task_kind=task_kind, top_n=top_k)
            for e in entries[:3]:
                hint = f"{e.task_kind}: {e.old_string_prefix[:60]}" if e.old_string_prefix else e.task_kind
                pattern_hints.append(hint)
            if pattern_hints:
                context_sources.append("pattern_library")
        except Exception as exc:
            error_notes.append(f"pattern_error: {exc}")

    # Step 3: search snippet (non-blocking)
    if search_adapter is not None:
        try:
            search_snip = search_adapter.search_snippet(query, top_k=top_k)
            if search_snip:
                context_sources.append("search")
        except Exception as exc:
            error_notes.append(f"search_error: {exc}")

    return HybridInspectContext(
        query=query,
        cache_snippet=cache_snippet,
        pattern_hints=pattern_hints,
        search_snippet=search_snip,
        context_sources=context_sources,
        error_notes=error_notes,
    )


__all__ = ["HybridInspectContext", "build_hybrid_inspect_context"]
