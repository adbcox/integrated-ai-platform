"""Phase 2 entry: deterministic builders for typed tool events."""

from __future__ import annotations

from typing import Any

from framework.tool_action_observation_contract import (
    ToolActionRecord,
    ToolContractName,
    ToolContractStatus,
    ToolObservationRecord,
)


def build_tool_action(
    *,
    action_id: str,
    session_id: str,
    job_id: str,
    tool_name: ToolContractName,
    arguments: dict[str, Any] | None = None,
    requested_by: str = "phase2_entry",
) -> ToolActionRecord:
    return ToolActionRecord(
        action_id=action_id,
        session_id=session_id,
        job_id=job_id,
        tool_name=tool_name,
        arguments=dict(arguments) if arguments else {},
        requested_by=requested_by,
    )


def build_tool_observation(
    *,
    action: ToolActionRecord,
    status: ToolContractStatus,
    allowed: bool,
    duration_ms: int = 0,
    stdout: str = "",
    stderr: str = "",
    structured_payload: dict[str, Any] | None = None,
    side_effect_metadata: dict[str, Any] | None = None,
    error: str = "",
    return_code: int = 0,
) -> ToolObservationRecord:
    return ToolObservationRecord(
        action_id=action.action_id,
        session_id=action.session_id,
        job_id=action.job_id,
        tool_name=action.tool_name,
        status=status,
        allowed=allowed,
        duration_ms=duration_ms,
        stdout=stdout,
        stderr=stderr,
        structured_payload=dict(structured_payload) if structured_payload else {},
        side_effect_metadata=dict(side_effect_metadata) if side_effect_metadata else {},
        error=error,
        return_code=return_code,
    )


def build_blocked_tool_observation(
    *,
    action: ToolActionRecord,
    reason: str,
) -> ToolObservationRecord:
    return ToolObservationRecord(
        action_id=action.action_id,
        session_id=action.session_id,
        job_id=action.job_id,
        tool_name=action.tool_name,
        status=ToolContractStatus.BLOCKED,
        allowed=False,
        duration_ms=0,
        stdout="",
        stderr="",
        structured_payload={},
        side_effect_metadata={},
        error=reason,
        return_code=126,
    )


__all__ = [
    "build_blocked_tool_observation",
    "build_tool_action",
    "build_tool_observation",
]
