"""SearchAwareInspectRunner: combines SearchLoopAdapter search + dispatch_read_file inspect."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from framework.search_loop_adapter import SearchLoopAdapter, SearchLoopResult
from framework.read_file_dispatch import dispatch_read_file
from framework.tool_schema import ReadFileAction, ReadFileObservation
from framework.workspace_scope import ToolPathScope

# -- import-time assertions --
assert "context_snippet" in SearchLoopResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: SearchLoopResult.context_snippet"
assert "matches" in SearchLoopResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: SearchLoopResult.matches"
assert "content" in ReadFileObservation.__dataclass_fields__, \
    "INTERFACE MISMATCH: ReadFileObservation.content"
assert "error" in ReadFileObservation.__dataclass_fields__, \
    "INTERFACE MISMATCH: ReadFileObservation.error"
assert callable(getattr(SearchLoopAdapter, "search", None)), \
    "INTERFACE MISMATCH: SearchLoopAdapter.search"
assert callable(dispatch_read_file), \
    "INTERFACE MISMATCH: dispatch_read_file"


@dataclass(frozen=True)
class SearchAwareInspectResult:
    path: str
    content: Optional[str]
    inspect_error: Optional[str]
    search_query: str
    context_snippet: str
    search_error: Optional[str]
    search_match_count: int


class SearchAwareInspectRunner:
    """Runs search then dispatch_read_file; search failure is non-blocking."""

    def __init__(
        self,
        *,
        search_adapter: Optional[SearchLoopAdapter] = None,
        top_k: int = 5,
        source_root: Optional[Path] = None,
    ):
        self._adapter = search_adapter or SearchLoopAdapter()
        self._top_k = top_k
        self._source_root = Path(source_root) if source_root is not None else Path(".")

    def run(
        self,
        path: str,
        *,
        search_query: str = "",
        scope: Optional[ToolPathScope] = None,
    ) -> SearchAwareInspectResult:
        # Search step (non-blocking)
        context_snippet = ""
        search_error: Optional[str] = None
        search_match_count = 0
        if search_query.strip():
            try:
                result: SearchLoopResult = self._adapter.search(search_query, top_k=self._top_k)
                context_snippet = result.context_snippet or ""
                search_match_count = result.match_count
            except Exception as exc:
                search_error = str(exc)

        # Inspect step
        content: Optional[str] = None
        inspect_error: Optional[str] = None
        try:
            eff_scope = scope if scope is not None else ToolPathScope(source_root=self._source_root)
            # resolve relative to source_root so dispatch_read_file finds the file
            abs_path = str((eff_scope.source_root / path).resolve())
            action = ReadFileAction(path=abs_path)
            obs: ReadFileObservation = dispatch_read_file(action, eff_scope)
            content = obs.content
            inspect_error = obs.error
        except Exception as exc:
            inspect_error = str(exc)

        return SearchAwareInspectResult(
            path=path,
            content=content,
            inspect_error=inspect_error,
            search_query=search_query,
            context_snippet=context_snippet,
            search_error=search_error,
            search_match_count=search_match_count,
        )


__all__ = ["SearchAwareInspectResult", "SearchAwareInspectRunner"]
