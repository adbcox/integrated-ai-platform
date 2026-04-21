"""AiderExecutionAdapterV1: structured local-first execution handoff for Aider."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


EXECUTION_MODE_LOCAL_FIRST = "local_first"
ADAPTER_STATUS_READY = "ready"
ADAPTER_STATUS_PENDING = "pending"
ADAPTER_STATUS_BLOCKED = "blocked"


@dataclass
class AiderHandoffRecordV1:
    package_id: str
    allowed_files: List[str]
    validation_sequence: List[str]
    adapter_status: str
    execution_mode: str
    task_class: Optional[str]
    difficulty: Optional[str]
    handoff_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "allowed_files": self.allowed_files,
            "validation_sequence": self.validation_sequence,
            "adapter_status": self.adapter_status,
            "execution_mode": self.execution_mode,
            "task_class": self.task_class,
            "difficulty": self.difficulty,
            "handoff_at": self.handoff_at,
            "notes": self.notes,
        }


class AiderExecutionAdapterV1:
    """Structure a local-first Aider execution handoff without live process control."""

    DEFAULT_VALIDATION_SEQUENCE = [
        "python3 -m pytest tests/ -x -q",
        "make check",
        "make quick",
    ]

    def build_handoff(
        self,
        package_id: str,
        allowed_files: List[str],
        task_class: Optional[str] = None,
        difficulty: Optional[str] = None,
        validation_sequence: Optional[List[str]] = None,
        notes: Optional[List[str]] = None,
    ) -> AiderHandoffRecordV1:
        seq = validation_sequence if validation_sequence is not None else self.DEFAULT_VALIDATION_SEQUENCE
        status = ADAPTER_STATUS_READY if allowed_files else ADAPTER_STATUS_BLOCKED
        return AiderHandoffRecordV1(
            package_id=package_id,
            allowed_files=allowed_files,
            validation_sequence=seq,
            adapter_status=status,
            execution_mode=EXECUTION_MODE_LOCAL_FIRST,
            task_class=task_class,
            difficulty=difficulty,
            notes=notes or [],
        )

    def is_ready(self, record: AiderHandoffRecordV1) -> bool:
        return (
            record.adapter_status == ADAPTER_STATUS_READY
            and record.execution_mode == EXECUTION_MODE_LOCAL_FIRST
            and bool(record.allowed_files)
        )
