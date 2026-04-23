"""Typed tool action/observation contract for framework runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .compat import StrEnum


class ToolName(StrEnum):
    INFERENCE = "inference"
    RUN_COMMAND = "run_command"
    RUN_TESTS = "run_tests"
    APPLY_EDIT = "apply_edit"


class ToolStatus(StrEnum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    EXECUTED = "executed"
    FAILED = "failed"


@dataclass(frozen=True)
class ToolAction:
    job_id: str
    tool: ToolName
    arguments: dict[str, Any] = field(default_factory=dict)
    requested_by: str = "worker_runtime"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tool"] = self.tool.value
        return payload


@dataclass(frozen=True)
class ToolObservation:
    job_id: str
    tool: ToolName
    status: ToolStatus
    allowed: bool
    output: str = ""
    error: str = ""
    return_code: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tool"] = self.tool.value
        payload["status"] = self.status.value
        return payload
