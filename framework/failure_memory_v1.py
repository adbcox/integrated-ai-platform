"""Failure memory surface for Phase 4 self-sufficiency uplift (P4-01)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class FailureRecordV1:
    task_id: str
    task_class: str
    failure_signature: str
    correction_hint: str
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_class": self.task_class,
            "failure_signature": self.failure_signature,
            "correction_hint": self.correction_hint,
            "recorded_at": self.recorded_at,
        }


@dataclass
class FailureSummaryV1:
    total_failures: int
    by_task_class: Dict[str, int]
    most_common_signatures: List[str]
    top_correction_hints: List[str]

    def to_dict(self) -> dict:
        return {
            "total_failures": self.total_failures,
            "by_task_class": self.by_task_class,
            "most_common_signatures": self.most_common_signatures,
            "top_correction_hints": self.top_correction_hints,
        }


class FailureMemoryV1:
    def __init__(self) -> None:
        self._records: List[FailureRecordV1] = []

    def append(self, record: FailureRecordV1) -> None:
        self._records.append(record)

    def record(
        self,
        task_id: str,
        task_class: str,
        failure_signature: str,
        correction_hint: str,
        recorded_at: Optional[str] = None,
    ) -> FailureRecordV1:
        rec = FailureRecordV1(
            task_id=task_id,
            task_class=task_class,
            failure_signature=failure_signature,
            correction_hint=correction_hint,
            recorded_at=recorded_at or datetime.now(timezone.utc).isoformat(),
        )
        self._records.append(rec)
        return rec

    def get_by_task_class(self, task_class: str) -> List[FailureRecordV1]:
        return [r for r in self._records if r.task_class == task_class]

    def get_by_task_id(self, task_id: str) -> List[FailureRecordV1]:
        return [r for r in self._records if r.task_id == task_id]

    def all_records(self) -> List[FailureRecordV1]:
        return list(self._records)

    def summarize(self) -> FailureSummaryV1:
        by_class: Dict[str, int] = {}
        sig_counts: Dict[str, int] = {}
        hint_counts: Dict[str, int] = {}

        for rec in self._records:
            by_class[rec.task_class] = by_class.get(rec.task_class, 0) + 1
            sig_counts[rec.failure_signature] = sig_counts.get(rec.failure_signature, 0) + 1
            hint_counts[rec.correction_hint] = hint_counts.get(rec.correction_hint, 0) + 1

        top_sigs = sorted(sig_counts, key=lambda k: sig_counts[k], reverse=True)[:5]
        top_hints = sorted(hint_counts, key=lambda k: hint_counts[k], reverse=True)[:5]

        return FailureSummaryV1(
            total_failures=len(self._records),
            by_task_class=by_class,
            most_common_signatures=top_sigs,
            top_correction_hints=top_hints,
        )
