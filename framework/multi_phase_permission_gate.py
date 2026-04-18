from __future__ import annotations

from typing import Any

from framework.permission_engine import PermissionDecision, PermissionEngine
from framework.tool_system import ToolAction, ToolName, ToolObservation, ToolStatus


def gate_multi_phase_action(
    *,
    action: ToolAction,
    engine: PermissionEngine,
    allowed_tools: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ToolObservation:
    if not isinstance(action, ToolAction):
        raise TypeError("action must be a ToolAction")
    if not isinstance(engine, PermissionEngine):
        raise TypeError("engine must be a PermissionEngine")

    resolved_tools = list(allowed_tools) if allowed_tools else []
    resolved_metadata: dict[str, Any] = dict(metadata) if metadata else {}

    decision: PermissionDecision = engine.evaluate(
        action=action,
        allowed_tools_actions=resolved_tools,
        metadata=resolved_metadata,
    )

    status = ToolStatus.ALLOWED if decision.allowed else ToolStatus.BLOCKED
    return ToolObservation(
        job_id=action.job_id,
        tool=action.tool,
        status=status,
        allowed=decision.allowed,
        output="",
        error="" if decision.allowed else decision.reason,
        return_code=0,
        metadata={
            "permission_decision": decision.to_dict(),
            "multi_phase_gate": "v1",
        },
    )


def gate_multi_phase_tool_name(
    *,
    job_id: str,
    tool_name: ToolName,
    arguments: dict[str, Any] | None = None,
    engine: PermissionEngine,
    allowed_tools: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ToolObservation:
    action = ToolAction(
        job_id=job_id,
        tool=tool_name,
        arguments=dict(arguments) if arguments else {},
        requested_by="multi_phase_permission_gate",
    )
    return gate_multi_phase_action(
        action=action,
        engine=engine,
        allowed_tools=allowed_tools,
        metadata=metadata,
    )


__all__ = [
    "gate_multi_phase_action",
    "gate_multi_phase_tool_name",
]
