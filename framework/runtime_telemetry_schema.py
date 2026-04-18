"""Phase 1 normalized runtime telemetry shapes.

Narrow dataclasses for the telemetry/event records emitted by the
Phase 1 local runtime surfaces (inference gateway, local command
runner, baseline validation pack).

This is intentionally NOT the full Phase 2 run ledger. It only
normalizes the fields the Phase 1 gateway and validation pack need to
emit.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class InferenceTelemetry:
    profile_name: str
    backend: str
    model: str
    timeout_seconds: int
    retry_budget: int
    prompt_hash: str
    started_at: str
    completed_at: str
    duration_ms: int
    success: bool
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CommandTelemetry:
    command: str
    cwd: str
    return_code: int
    stdout: str
    stderr: str
    started_at: str
    completed_at: str
    duration_ms: int
    success: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationRecord:
    name: str
    passed: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunBundleManifest:
    schema_version: int
    run_id: str
    session_id: str
    profile_name: str
    source_root: str
    scratch_root: str
    artifact_root: str
    command_records: list[dict[str, Any]] = field(default_factory=list)
    validation_records: list[dict[str, Any]] = field(default_factory=list)
    inference_records: list[dict[str, Any]] = field(default_factory=list)
    workspace_side_effects: list[str] = field(default_factory=list)
    artifact_bundle_ref: str = ""
    final_outcome: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


RUN_BUNDLE_SCHEMA_VERSION = 1


__all__ = [
    "RUN_BUNDLE_SCHEMA_VERSION",
    "CommandTelemetry",
    "InferenceTelemetry",
    "RunBundleManifest",
    "ValidationRecord",
]
