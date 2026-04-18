"""Phase 2 entry: typed Action->Observation substrate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class _StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class ToolContractName(_StrEnum):
    READ_FILE = "read_file"
    SEARCH = "search"
    LIST_DIR = "list_dir"
    REPO_MAP = "repo_map"
    APPLY_PATCH = "apply_patch"
    GIT_DIFF = "git_diff"
    RUN_COMMAND = "run_command"
    RUN_TESTS = "run_tests"
    PUBLISH_ARTIFACT = "publish_artifact"


class ToolContractStatus(_StrEnum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    EXECUTED = "executed"
    FAILED = "failed"


@dataclass
class ToolActionRecord:
    action_id: str
    session_id: str
    job_id: str
    tool_name: ToolContractName
    arguments: dict[str, Any] = field(default_factory=dict)
    requested_by: str = "phase2_entry"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tool_name"] = self.tool_name.value
        return payload


@dataclass
class ToolObservationRecord:
    action_id: str
    session_id: str
    job_id: str
    tool_name: ToolContractName
    status: ToolContractStatus
    allowed: bool
    duration_ms: int = 0
    stdout: str = ""
    stderr: str = ""
    structured_payload: dict[str, Any] = field(default_factory=dict)
    side_effect_metadata: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    return_code: int = 0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tool_name"] = self.tool_name.value
        payload["status"] = self.status.value
        return payload


__all__ = [
    "ToolActionRecord",
    "ToolContractName",
    "ToolContractStatus",
    "ToolObservationRecord",
]
