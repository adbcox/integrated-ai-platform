"""LoopTaskBuilder — assembles context-injected MVPTask inputs with safe fallback.

Inspection gate output:
  MVPTask fields: session_id, target_path, old_string, new_string, task_kind, replace_all,
                  enable_revert, retrieval_query
  LoopRetrievalBridge.build_context sig: (self, query_text: str, top_k: int = 5, *, task_kind: Optional[str] = None) -> LoopContextBundle
  PatternGuidedInspector.hints_for sig: (self, task_kind: str, top_n: int = 5) -> list[InspectHint]
  MVPTask.retrieval_query: exists — context-injection path is viable
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from framework.loop_retrieval_bridge import LoopContextBundle, LoopRetrievalBridge
from framework.mvp_coding_loop import MVPTask
from framework.pattern_guided_inspector import InspectHint, PatternGuidedInspector

assert "retrieval_query" in MVPTask.__dataclass_fields__, "INTERFACE MISMATCH: MVPTask.retrieval_query missing"
assert callable(LoopRetrievalBridge), "INTERFACE MISMATCH: LoopRetrievalBridge not callable"
assert callable(PatternGuidedInspector), "INTERFACE MISMATCH: PatternGuidedInspector not callable"


@dataclass
class TaskBuildContext:
    query_text: str
    context_snippet: str
    pattern_hints: list
    cache_hit: bool
    source: str


class LoopTaskBuilder:
    """Assembles contextualized MVPTask inputs from retrieval bridge and pattern hints."""

    def __init__(
        self,
        retrieval_bridge: Optional[LoopRetrievalBridge] = None,
        pattern_inspector: Optional[PatternGuidedInspector] = None,
    ) -> None:
        self._bridge = retrieval_bridge
        self._inspector = pattern_inspector

    def build(
        self,
        *,
        session_id: str,
        target_path: str,
        old_string: str,
        new_string: str,
        task_kind: str,
        query_text: str = "",
        top_k: int = 5,
        replace_all: bool = False,
        enable_revert: bool = True,
    ) -> tuple:
        build_ctx = self.build_context_only(
            query_text=query_text or old_string[:50],
            task_kind=task_kind,
            top_k=top_k,
        )
        retrieval_query = build_ctx.query_text if "retrieval_query" in MVPTask.__dataclass_fields__ else None
        task = MVPTask(
            session_id=session_id,
            target_path=target_path,
            old_string=old_string,
            new_string=new_string,
            task_kind=task_kind,
            replace_all=replace_all,
            enable_revert=enable_revert,
            retrieval_query=retrieval_query,
        )
        return task, build_ctx

    def build_context_only(
        self,
        *,
        query_text: str,
        task_kind: str = "",
        top_k: int = 5,
    ) -> TaskBuildContext:
        context_snippet = ""
        cache_hit = False
        source = "none"

        if self._bridge is not None:
            try:
                bundle = self._bridge.build_context(query_text, top_k=top_k, task_kind=task_kind or None)
                context_snippet = bundle.context_snippet
                cache_hit = bundle.cache_hit
                source = bundle.source
            except Exception:  # noqa: BLE001
                pass

        pattern_hints: list = []
        if self._inspector is not None and task_kind:
            try:
                pattern_hints = self._inspector.hints_for(task_kind, top_n=top_k)
            except Exception:  # noqa: BLE001
                pass

        return TaskBuildContext(
            query_text=query_text,
            context_snippet=context_snippet,
            pattern_hints=pattern_hints,
            cache_hit=cache_hit,
            source=source,
        )


__all__ = ["TaskBuildContext", "LoopTaskBuilder"]
