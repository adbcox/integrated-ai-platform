"""PersistentExecutionLedgerV1: file-backed execution ledger persisted as JSONL."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PersistentLedgerEntryV1:
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

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PersistentLedgerEntryV1":
        return cls(
            run_id=d["run_id"],
            package_id=d["package_id"],
            package_label=d.get("package_label", ""),
            executor=d["executor"],
            route=d.get("route", ""),
            validations_run=d.get("validations_run", []),
            validation_results=d.get("validation_results", {}),
            artifacts_produced=d.get("artifacts_produced", []),
            escalation_status=d.get("escalation_status", "NOT_ESCALATED"),
            final_outcome=d.get("final_outcome", "UNKNOWN"),
            recorded_at=d.get("recorded_at", ""),
            notes=d.get("notes", []),
        )


class PersistentExecutionLedgerV1:
    """JSONL-backed persistent execution ledger."""

    DEFAULT_PATH = Path("artifacts/substrate/persistent_execution_ledger.jsonl")

    def __init__(self, ledger_path: Optional[Path] = None) -> None:
        self._path = ledger_path or self.DEFAULT_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Optional[List[PersistentLedgerEntryV1]] = None

    def append_record(
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
    ) -> PersistentLedgerEntryV1:
        all_ok = all(validation_results.values()) if validation_results else False
        entry = PersistentLedgerEntryV1(
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
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")
        self._cache = None  # invalidate cache
        return entry

    def load_records(self) -> List[PersistentLedgerEntryV1]:
        if self._cache is not None:
            return list(self._cache)
        if not self._path.exists():
            return []
        entries: List[PersistentLedgerEntryV1] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(PersistentLedgerEntryV1.from_dict(json.loads(line)))
            except Exception:
                pass
        self._cache = entries
        return list(entries)

    def summarize(self) -> Dict[str, Any]:
        entries = self.load_records()
        total = len(entries)
        passed = sum(1 for e in entries if e.all_passed)
        pass_rate = passed / total if total > 0 else 0.0
        executors = {}
        for e in entries:
            executors[e.executor] = executors.get(e.executor, 0) + 1
        return {
            "total_runs": total,
            "passed_runs": passed,
            "pass_rate": pass_rate,
            "executor_counts": executors,
            "ledger_path": str(self._path),
        }
