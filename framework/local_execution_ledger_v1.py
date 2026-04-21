"""LocalExecutionLedgerV1: record and serialize local execution run entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json


@dataclass
class LedgerEntryV1:
    run_id: str
    package_id: str
    package_label: str
    executor: str
    route: str
    validations_run: List[str]
    validation_results: Dict[str, bool]
    artifacts_produced: List[str]
    escalation_status: str
    final_outcome: str
    recorded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    notes: List[str] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(self.validation_results.values()) if self.validation_results else False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "package_id": self.package_id,
            "package_label": self.package_label,
            "executor": self.executor,
            "route": self.route,
            "validations_run": self.validations_run,
            "validation_results": self.validation_results,
            "artifacts_produced": self.artifacts_produced,
            "escalation_status": self.escalation_status,
            "final_outcome": self.final_outcome,
            "recorded_at": self.recorded_at,
            "all_passed": self.all_passed,
            "notes": self.notes,
        }


class LocalExecutionLedgerV1:
    """In-session ledger of local execution runs; optionally serializes to JSON."""

    def __init__(self) -> None:
        self._entries: List[LedgerEntryV1] = []

    def append(self, entry: LedgerEntryV1) -> None:
        self._entries.append(entry)

    def record(
        self,
        run_id: str,
        package_id: str,
        package_label: str,
        executor: str,
        route: str,
        validation_results: Dict[str, bool],
        artifacts_produced: Optional[List[str]] = None,
        escalation_status: str = "NOT_ESCALATED",
        notes: Optional[List[str]] = None,
    ) -> LedgerEntryV1:
        all_ok = all(validation_results.values()) if validation_results else False
        entry = LedgerEntryV1(
            run_id=run_id,
            package_id=package_id,
            package_label=package_label,
            executor=executor,
            route=route,
            validations_run=list(validation_results.keys()),
            validation_results=validation_results,
            artifacts_produced=artifacts_produced or [],
            escalation_status=escalation_status,
            final_outcome="PASS" if all_ok else "FAIL",
            notes=notes or [],
        )
        self._entries.append(entry)
        return entry

    def all_entries(self) -> List[LedgerEntryV1]:
        return list(self._entries)

    @property
    def total_runs(self) -> int:
        return len(self._entries)

    @property
    def passed_runs(self) -> int:
        return sum(1 for e in self._entries if e.all_passed)

    @property
    def pass_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.passed_runs / self.total_runs

    def serialize(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._entries]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_runs": self.total_runs,
            "passed_runs": self.passed_runs,
            "pass_rate": self.pass_rate,
            "entries": self.serialize(),
        }
