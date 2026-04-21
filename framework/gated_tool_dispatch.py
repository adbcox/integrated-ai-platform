"""Permission-gated wrappers for typed sandbox dispatch functions."""
from __future__ import annotations

from framework.sandbox_tool_dispatch import dispatch_run_command, dispatch_run_tests
from framework.tool_schema import RunCommandAction, RunTestsAction, RunCommandObservation, RunTestsObservation
from framework.typed_permission_gate import ToolPermission, TypedPermissionGate
from framework.workspace_scope import ToolPathScope


class GatedDispatchError(PermissionError):
    def __init__(self, message: str, *, ask_required: bool = False):
        super().__init__(message)
        self.ask_required = ask_required


def gated_run_command(
    action: RunCommandAction,
    scope: ToolPathScope,
    gate: TypedPermissionGate,
    *,
    runner=None,
    extra_env=None,
) -> RunCommandObservation:
    decision = gate.evaluate(action)
    if decision == ToolPermission.DENY:
        raise GatedDispatchError(
            f"run_command denied by permission gate", ask_required=False
        )
    if decision == ToolPermission.ASK:
        raise GatedDispatchError(
            f"run_command requires interactive approval", ask_required=True
        )
    return dispatch_run_command(action, scope, runner=runner, extra_env=extra_env)


def gated_run_tests(
    action: RunTestsAction,
    scope: ToolPathScope,
    gate: TypedPermissionGate,
    *,
    runner=None,
    extra_env=None,
) -> RunTestsObservation:
    decision = gate.evaluate(action)
    if decision == ToolPermission.DENY:
        raise GatedDispatchError(
            f"run_tests denied by permission gate", ask_required=False
        )
    if decision == ToolPermission.ASK:
        raise GatedDispatchError(
            f"run_tests requires interactive approval", ask_required=True
        )
    return dispatch_run_tests(action, scope, runner=runner, extra_env=extra_env)


__all__ = ["GatedDispatchError", "gated_run_command", "gated_run_tests"]
