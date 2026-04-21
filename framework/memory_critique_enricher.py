"""Memory-backed critique enricher for retry guidance.

Looks up recent failure patterns for a (task_kind, error_type) pair, extracts
concrete examples, and appends them as additional guidance to a CritiqueResult.

Enrichment is opt-in — not automatic. Inspection gate output (packet 8):
  query_failures sig: (self, *, task_kind=None, error_type=None, limit=10) -> list[FailurePattern]
  CritiqueResult fields: ['task_kind', 'error_type', 'critique_text', 'pattern_count', 'retry_advised']
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from framework.critique_injector import CritiqueResult, build_critique, render_retry_prompt
from framework.local_memory_store import LocalMemoryStore

# -- import-time assertions --
assert "task_kind" in CritiqueResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: CritiqueResult.task_kind"
assert "error_type" in CritiqueResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: CritiqueResult.error_type"
assert callable(build_critique), "INTERFACE MISMATCH: build_critique"
assert callable(render_retry_prompt), "INTERFACE MISMATCH: render_retry_prompt"
assert callable(LocalMemoryStore.query_failures), "INTERFACE MISMATCH: LocalMemoryStore.query_failures"

_DEFAULT_MAX_EXAMPLES = 3


@dataclass
class CritiqueEnrichment:
    task_kind: str
    error_type: str
    pattern_examples: list[dict]
    extra_guidance: str

    def as_extra_instructions(self) -> str:
        """Return enrichment as formatted instruction text."""
        if not self.pattern_examples:
            return ""
        lines = [
            f"Memory-backed failure patterns for ({self.task_kind}, {self.error_type}):",
        ]
        for i, ex in enumerate(self.pattern_examples, 1):
            lines.append(f"  Example {i}: {ex.get('old_string_prefix', '')} -> error: {ex.get('error_summary', ex.get('error_type', ''))}")
        if self.extra_guidance:
            lines.append(self.extra_guidance)
        return "\n".join(lines)


def enrich_critique(
    critique: CritiqueResult,
    *,
    memory_store: Optional[LocalMemoryStore] = None,
    max_examples: int = _DEFAULT_MAX_EXAMPLES,
) -> CritiqueEnrichment:
    """Look up failure patterns for (task_kind, error_type), return enrichment."""
    store = memory_store or LocalMemoryStore()
    task_kind = critique.task_kind or ""
    error_type = critique.error_type or ""

    failures = store.query_failures(task_kind=task_kind or None, error_type=error_type or None, limit=max_examples)

    examples = [
        {
            "task_kind": f.task_kind,
            "error_type": f.error_type,
            "error_summary": f.error_summary,
            "old_string_prefix": f.old_string_prefix,
            "recurrence_count": f.recurrence_count,
        }
        for f in failures
    ]

    guidance = ""
    if examples:
        guidance = (
            f"Avoid the above patterns. The error '{error_type}' "
            f"has recurred {sum(e['recurrence_count'] for e in examples)} time(s) in memory."
        )

    return CritiqueEnrichment(
        task_kind=task_kind,
        error_type=error_type,
        pattern_examples=examples,
        extra_guidance=guidance,
    )


def render_enriched_retry_prompt(
    task_kind: str,
    *,
    target_file: str,
    file_content: str,
    old_string: str,
    last_error: Optional[str],
    new_string_hint: str = "",
    context_snippet: str = "",
    memory_store: Optional[LocalMemoryStore] = None,
    max_examples: int = _DEFAULT_MAX_EXAMPLES,
) -> str:
    """Combine render_retry_prompt with memory-backed critique enrichment."""
    store = memory_store or LocalMemoryStore()
    critique = build_critique(
        task_kind=task_kind,
        last_error=last_error,
        memory_store=store,
    )
    enrichment = enrich_critique(critique, memory_store=store, max_examples=max_examples)
    extra = enrichment.as_extra_instructions()

    base_prompt = render_retry_prompt(
        task_kind,
        target_file=target_file,
        file_content=file_content,
        old_string=old_string,
        new_string_hint=new_string_hint,
        context_snippet=context_snippet,
        last_error=last_error,
        memory_store=store,
    )
    if extra:
        return f"{base_prompt}\n\n{extra}"
    return base_prompt


__all__ = [
    "CritiqueEnrichment",
    "enrich_critique",
    "render_enriched_retry_prompt",
]
