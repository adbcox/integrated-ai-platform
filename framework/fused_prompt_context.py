"""FusedPromptContext: injects HybridInspectContext output into render_prompt."""
from __future__ import annotations

import inspect as _inspect
from dataclasses import dataclass
from typing import List, Optional

from framework.task_prompt_pack import render_prompt, SUPPORTED_TASK_CLASSES
from framework.hybrid_inspect_context import HybridInspectContext

# -- import-time assertions --
assert callable(render_prompt), \
    "INTERFACE MISMATCH: render_prompt"
assert "query" in HybridInspectContext.__dataclass_fields__, \
    "INTERFACE MISMATCH: HybridInspectContext.query"
assert "cache_snippet" in HybridInspectContext.__dataclass_fields__, \
    "INTERFACE MISMATCH: HybridInspectContext.cache_snippet"
assert "search_snippet" in HybridInspectContext.__dataclass_fields__, \
    "INTERFACE MISMATCH: HybridInspectContext.search_snippet"

# Verify render_prompt accepts context_snippet parameter
_render_params = set(_inspect.signature(render_prompt).parameters.keys())
assert "context_snippet" in _render_params, \
    "INTERFACE MISMATCH: render_prompt missing context_snippet parameter"
assert "file_content" in _render_params, \
    "INTERFACE MISMATCH: render_prompt missing file_content parameter"


@dataclass(frozen=True)
class FusedPromptContext:
    task_class: str
    target_file: str
    prompt: str
    context_sources: List[str]
    fallback_used: bool


def build_fused_prompt(
    task_class: str,
    *,
    target_file: str,
    file_content: str,
    hybrid_context: Optional[HybridInspectContext] = None,
    old_string: str = "",
    new_string_hint: str = "",
) -> FusedPromptContext:
    fallback_used = False
    context_sources: List[str] = []

    # Compose context_snippet from hybrid context
    context_snippet = ""
    if hybrid_context is not None:
        parts = []
        if hybrid_context.cache_snippet:
            parts.append(f"[cache] {hybrid_context.cache_snippet}")
        if hybrid_context.search_snippet:
            parts.append(f"[search] {hybrid_context.search_snippet}")
        if hybrid_context.pattern_hints:
            parts.append("[patterns] " + "; ".join(hybrid_context.pattern_hints[:2]))
        context_snippet = "\n".join(parts)
        context_sources = list(hybrid_context.context_sources)

    if task_class not in SUPPORTED_TASK_CLASSES:
        # Fallback: build a simple prompt from file content
        fallback_used = True
        prompt = (
            f"Task: {task_class}\n"
            f"File: {target_file}\n"
            f"Content:\n{file_content}\n"
            + (f"Context:\n{context_snippet}" if context_snippet else "")
        )
    else:
        prompt = render_prompt(
            task_class,
            target_file=target_file,
            file_content=file_content,
            old_string=old_string,
            new_string_hint=new_string_hint,
            context_snippet=context_snippet,
        )

    return FusedPromptContext(
        task_class=task_class,
        target_file=target_file,
        prompt=prompt,
        context_sources=context_sources,
        fallback_used=fallback_used,
    )


__all__ = ["FusedPromptContext", "build_fused_prompt"]
