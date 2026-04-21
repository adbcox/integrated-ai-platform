"""Bounded dispatch for SearchAction -> SearchObservation via local retrieval."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from framework.context_retrieval import RetrievalQuery, retrieve_context
from framework.tool_schema import SearchAction, SearchObservation
from framework.workspace_scope import ToolPathScope


def dispatch_search(
    action: SearchAction,
    scope: ToolPathScope,
    *,
    source_root: Optional[Path] = None,
) -> SearchObservation:
    if not isinstance(action, SearchAction):
        raise TypeError(f"Expected SearchAction; got {type(action)!r}")
    root = Path(source_root) if source_root is not None else scope.source_root
    if not action.query.strip():
        return SearchObservation(query=action.query, matches=(), error=None)
    try:
        result = retrieve_context(
            RetrievalQuery(query=action.query, top_k=10, include_snippets=True),
            source_root=root,
        )
        matches = tuple(
            f"{f.path}: {f.snippet}" if f.snippet else f.path
            for f in result.files
        )
        return SearchObservation(query=action.query, matches=matches, error=None)
    except Exception as exc:  # noqa: BLE001
        return SearchObservation(query=action.query, matches=(), error=str(exc))


__all__ = ["dispatch_search"]
