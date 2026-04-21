"""BoundedCritiqueAdopter: wires build_critique + enrich_critique into the retry decision path."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from framework.critique_injector import CritiqueResult, build_critique
from framework.memory_critique_enricher import CritiqueEnrichment, enrich_critique

# -- import-time assertions --
assert "retry_advised" in CritiqueResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: CritiqueResult.retry_advised"
assert "critique_text" in CritiqueResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: CritiqueResult.critique_text"
assert "task_kind" in CritiqueResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: CritiqueResult.task_kind"
assert "extra_guidance" in CritiqueEnrichment.__dataclass_fields__, \
    "INTERFACE MISMATCH: CritiqueEnrichment.extra_guidance"
assert callable(build_critique), \
    "INTERFACE MISMATCH: build_critique"
assert callable(enrich_critique), \
    "INTERFACE MISMATCH: enrich_critique"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class CritiqueAdoptionRecord:
    task_kind: str
    last_error: Optional[str]
    should_retry: bool
    critique_text: str
    extra_guidance: str
    evaluated_at: str


class BoundedCritiqueAdopter:
    """Builds and enriches critique; memory_store=None is allowed."""

    def __init__(self, *, memory_store=None):
        self._memory_store = memory_store

    def evaluate(
        self,
        task_kind: str,
        last_error: Optional[str],
        *,
        last_error_type: Optional[str] = None,
    ) -> CritiqueAdoptionRecord:
        critique: CritiqueResult = build_critique(
            task_kind=task_kind,
            last_error=last_error,
            last_error_type=last_error_type,
            memory_store=self._memory_store,
        )
        enrichment: CritiqueEnrichment = enrich_critique(
            critique,
            memory_store=self._memory_store,
        )
        return CritiqueAdoptionRecord(
            task_kind=task_kind,
            last_error=last_error,
            should_retry=critique.retry_advised,
            critique_text=critique.critique_text,
            extra_guidance=enrichment.extra_guidance or "",
            evaluated_at=_iso_now(),
        )


__all__ = ["CritiqueAdoptionRecord", "BoundedCritiqueAdopter"]
