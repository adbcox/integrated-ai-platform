"""Loop retrieval bridge — pre-processor for context injection into render_prompt.

Assembles LoopContextBundle from RetrievalCache hits and RepoPatternLibrary hints,
returning context_snippet text suitable for render_prompt() or MVPTask.retrieval_query.

This is a pre-processor only: it does not modify MVPCodingLoopRunner internals and
does not call retrieve_context() directly. Caller populates MVPTask from the bundle.

Inspection gate output (packet 4):
  MVPTask fields: ['session_id', 'target_path', 'old_string', 'new_string', 'task_kind',
                   'replace_all', 'enable_revert', 'retrieval_query']
  MVPCodingLoopRunner attrs: ['run_task']
  -> MVPTask.retrieval_query is the compatible pre-processor integration point.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from framework.retrieval_cache import RetrievalCache
from framework.repo_pattern_store import PatternEntry, RepoPatternLibrary

# -- import-time assertions --
assert callable(RetrievalCache.get), "INTERFACE MISMATCH: RetrievalCache.get"
assert callable(RetrievalCache.put), "INTERFACE MISMATCH: RetrievalCache.put"
assert callable(RepoPatternLibrary.query), "INTERFACE MISMATCH: RepoPatternLibrary.query"
assert "entries" in RepoPatternLibrary.__dataclass_fields__, \
    "INTERFACE MISMATCH: RepoPatternLibrary.entries"


@dataclass
class LoopContextBundle:
    query_text: str
    top_k: int
    context_snippet: str
    cache_hit: bool
    pattern_examples: list[dict[str, Any]] = field(default_factory=list)
    source: str = "none"


class LoopRetrievalBridge:
    """Pre-processor that assembles context from cache or pattern library."""

    def __init__(
        self,
        retrieval_cache: RetrievalCache,
        pattern_library: Optional[RepoPatternLibrary] = None,
        *,
        max_pattern_examples: int = 3,
    ) -> None:
        self._cache = retrieval_cache
        self._patterns = pattern_library
        self._max_examples = max_pattern_examples

    def build_context(
        self,
        query_text: str,
        top_k: int = 5,
        *,
        task_kind: Optional[str] = None,
    ) -> LoopContextBundle:
        """Build LoopContextBundle from cache hit or pattern library hints."""
        cached = self._cache.get(query_text, top_k)
        if cached is not None:
            snippet = self._snippet_from_cached(cached.result_dict)
            return LoopContextBundle(
                query_text=query_text,
                top_k=top_k,
                context_snippet=snippet,
                cache_hit=True,
                source="retrieval_cache",
            )

        examples: list[PatternEntry] = []
        if self._patterns is not None:
            examples = self._patterns.query(task_kind=task_kind, top_n=self._max_examples)

        snippet = self._snippet_from_patterns(examples)
        return LoopContextBundle(
            query_text=query_text,
            top_k=top_k,
            context_snippet=snippet,
            cache_hit=False,
            pattern_examples=[
                {
                    "task_kind": e.task_kind,
                    "old_string_prefix": e.old_string_prefix,
                    "new_string_prefix": e.new_string_prefix,
                    "reuse_count": e.reuse_count,
                }
                for e in examples
            ],
            source="pattern_library" if examples else "none",
        )

    def build_context_snippet(
        self,
        query_text: str,
        top_k: int = 5,
        *,
        task_kind: Optional[str] = None,
    ) -> str:
        """Convenience: return only the context_snippet string."""
        return self.build_context(query_text, top_k, task_kind=task_kind).context_snippet

    def _snippet_from_cached(self, result_dict: dict[str, Any]) -> str:
        files = result_dict.get("files", [])
        snippet = result_dict.get("snippet", "")
        parts = []
        if files:
            parts.append("Relevant files: " + ", ".join(str(f) for f in files))
        if snippet:
            parts.append(snippet)
        return "\n".join(parts)

    def _snippet_from_patterns(self, examples: list[PatternEntry]) -> str:
        if not examples:
            return ""
        lines = ["Pattern examples from memory:"]
        for e in examples:
            lines.append(
                f"  [{e.task_kind}] {e.old_string_prefix!r} -> {e.new_string_prefix!r}"
                f" (reused {e.reuse_count}x)"
            )
        return "\n".join(lines)


__all__ = [
    "LoopContextBundle",
    "LoopRetrievalBridge",
]
