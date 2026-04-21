"""SearchLoopAdapter — wraps dispatch_search for loop pre-step context retrieval.

Inspection gate output:
  dispatch_search sig: (action: SearchAction, scope: ToolPathScope, *, source_root: Optional[Path] = None) -> SearchObservation
  SearchAction fields: ['query', 'path', 'pattern']
  SearchObservation fields: ['query', 'matches', 'error']
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.search_action_dispatch import dispatch_search
from framework.tool_schema import SearchAction
from framework.workspace_scope import ToolPathScope

assert callable(dispatch_search), "INTERFACE MISMATCH: dispatch_search not callable"

_DEFAULT_SOURCE_ROOT = Path(".")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class SearchLoopResult:
    query: str
    matches: tuple
    context_snippet: str
    match_count: int
    searched_at: str


class SearchLoopAdapter:
    """Stateless adapter wrapping dispatch_search for loop pre-step use."""

    def __init__(self, source_root: Optional[Path] = None) -> None:
        self._source_root = Path(source_root) if source_root is not None else _DEFAULT_SOURCE_ROOT

    def search(self, query: str, top_k: int = 5) -> SearchLoopResult:
        try:
            action = SearchAction(query=query)
            scope = ToolPathScope(source_root=self._source_root)
            obs = dispatch_search(action, scope, source_root=self._source_root)
            matches = tuple(obs.matches) if obs.matches else ()
            limited = matches[:top_k]
            snippet = "\n".join(limited) if limited else ""
            if obs.error:
                snippet = f"[search error: {obs.error}]"
            return SearchLoopResult(
                query=query,
                matches=limited,
                context_snippet=snippet,
                match_count=len(limited),
                searched_at=_iso_now(),
            )
        except Exception as exc:  # noqa: BLE001
            return SearchLoopResult(
                query=query,
                matches=(),
                context_snippet=f"[search error: {exc}]",
                match_count=0,
                searched_at=_iso_now(),
            )

    def search_snippet(self, query: str, top_k: int = 5) -> str:
        return self.search(query, top_k=top_k).context_snippet


__all__ = ["SearchLoopResult", "SearchLoopAdapter"]
