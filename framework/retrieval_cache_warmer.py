"""Pre-populates RetrievalCache entries from recent LocalMemoryStore success patterns."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from framework.context_retrieval import RetrievalQuery, RetrievalResult, retrieve_context
from framework.local_memory_store import LocalMemoryStore, SuccessPattern
from framework.retrieval_cache import RetrievalCache

# -- import-time assertions --
assert callable(RetrievalCache.get), "INTERFACE MISMATCH: RetrievalCache.get"
assert callable(RetrievalCache.put), "INTERFACE MISMATCH: RetrievalCache.put"
assert callable(LocalMemoryStore.query_successes), \
    "INTERFACE MISMATCH: LocalMemoryStore.query_successes"
assert "task_kind" in SuccessPattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: SuccessPattern.task_kind"
assert "old_string_prefix" in SuccessPattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: SuccessPattern.old_string_prefix"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class CacheWarmingResult:
    queries_attempted: int
    cache_hits_before: int
    entries_written: int
    errors: list = field(default_factory=list)
    warmed_at: str = field(default_factory=_iso_now)


def warm_retrieval_cache(
    memory_store: LocalMemoryStore,
    cache: RetrievalCache,
    source_root: Path,
    *,
    top_k: int = 5,
    max_patterns: int = 20,
) -> CacheWarmingResult:
    patterns = memory_store.query_successes(limit=max_patterns)
    result = CacheWarmingResult(
        queries_attempted=0,
        cache_hits_before=0,
        entries_written=0,
    )

    for pattern in patterns:
        query_text = f"{pattern.task_kind} {pattern.old_string_prefix}".strip()
        if not query_text:
            continue
        result.queries_attempted += 1
        try:
            existing = cache.get(query_text, top_k)
            if existing is not None:
                result.cache_hits_before += 1
                continue
            retrieval = retrieve_context(
                RetrievalQuery(query=query_text, top_k=top_k, include_snippets=True),
                source_root=Path(source_root),
            )
            result_dict = dataclasses.asdict(retrieval)
            cache.put(query_text, top_k, result_dict)
            result.entries_written += 1
        except Exception as exc:  # noqa: BLE001
            result.errors.append(str(exc))

    return result


__all__ = ["CacheWarmingResult", "warm_retrieval_cache"]
