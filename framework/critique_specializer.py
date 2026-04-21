"""CritiqueSpecializer — per-task-class critique guidance enriched with memory-backed failure patterns.

Inspection gate output:
  CritiqueResult fields: task_kind, error_type, critique_text, pattern_count, retry_advised
  enrich_critique sig: (critique: CritiqueResult, *, memory_store=None, max_examples=3) -> CritiqueEnrichment
  SUPPORTED_TASK_CLASSES: frozenset({'bug_fix', 'metadata_addition', 'helper_insertion',
    'narrow_test_update', 'text_replacement'})
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from framework.critique_injector import CritiqueResult
from framework.local_memory_store import LocalMemoryStore
from framework.memory_critique_enricher import CritiqueEnrichment, enrich_critique
from framework.task_prompt_pack import SUPPORTED_TASK_CLASSES

assert hasattr(CritiqueResult, "__dataclass_fields__"), "INTERFACE MISMATCH: CritiqueResult not dataclass"
assert callable(enrich_critique), "INTERFACE MISMATCH: enrich_critique not callable"
assert SUPPORTED_TASK_CLASSES, "INTERFACE MISMATCH: SUPPORTED_TASK_CLASSES empty"

_BASE_GUIDANCE: dict = {
    "text_replacement": (
        "Focus on exact string matching. Ensure the old_string exists verbatim in the target file. "
        "Avoid whitespace or indentation mismatches."
    ),
    "bug_fix": (
        "Identify the minimal change needed to fix the bug. Preserve surrounding logic. "
        "Verify the fix does not introduce regressions."
    ),
    "guard_clause": (
        "Add the guard clause at the top of the function before other logic. "
        "Ensure the condition is correct and the early return is safe."
    ),
    "assertion_addition": (
        "Add the assertion in the correct location. Verify the assertion message is descriptive. "
        "Ensure the assertion does not fire under normal conditions."
    ),
    "metadata_addition": (
        "Add metadata fields without breaking existing structure. "
        "Verify field names and types match schema expectations."
    ),
    "helper_insertion": (
        "Insert the helper at the appropriate scope. Verify it does not conflict with existing helpers. "
        "Ensure the helper is callable from the intended call sites."
    ),
    "narrow_test_update": (
        "Update only the targeted test. Preserve unrelated test behavior. "
        "Ensure updated assertions match the new expected behavior."
    ),
}

# Fill any SUPPORTED_TASK_CLASSES not explicitly covered
for _tc in SUPPORTED_TASK_CLASSES:
    if _tc not in _BASE_GUIDANCE:
        _BASE_GUIDANCE[_tc] = f"Apply changes carefully for task class {_tc!r}. Verify correctness after edit."


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class CritiqueSpecialization:
    task_kind: str
    base_guidance: str
    enrichment: Optional[CritiqueEnrichment]
    combined_guidance: str
    specialized_at: str

    def as_prompt_instructions(self) -> str:
        return self.combined_guidance


class CritiqueSpecializer:
    """Combines per-task-class base guidance with memory-backed critique enrichment."""

    def __init__(self, memory_store: Optional[LocalMemoryStore] = None, max_examples: int = 3) -> None:
        self._memory_store = memory_store
        self._max_examples = max_examples

    def specialize(self, task_kind: str, *, error_type: str = "other") -> CritiqueSpecialization:
        base = _BASE_GUIDANCE.get(task_kind, f"Apply changes carefully for task class {task_kind!r}.")
        critique = CritiqueResult(
            task_kind=task_kind,
            error_type=error_type,
            critique_text=base,
            pattern_count=0,
            retry_advised=True,
        )
        enrichment: Optional[CritiqueEnrichment] = None
        extra_instructions = ""
        if self._memory_store is not None:
            try:
                enrichment = enrich_critique(
                    critique,
                    memory_store=self._memory_store,
                    max_examples=self._max_examples,
                )
                extra_instructions = enrichment.as_extra_instructions()
            except Exception:  # noqa: BLE001
                pass

        combined = base
        if extra_instructions:
            combined = f"{base}\n\n{extra_instructions}"

        return CritiqueSpecialization(
            task_kind=task_kind,
            base_guidance=base,
            enrichment=enrichment,
            combined_guidance=combined,
            specialized_at=_iso_now(),
        )

    def base_guidance_for(self, task_kind: str) -> str:
        return _BASE_GUIDANCE.get(task_kind, "")


__all__ = ["CritiqueSpecialization", "CritiqueSpecializer"]
