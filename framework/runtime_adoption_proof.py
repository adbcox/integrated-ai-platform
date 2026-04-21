"""Import-time proof assertions and bounded context builder for Phase 2 runtime surfaces."""
from __future__ import annotations

from pathlib import Path
from typing import Any

# --- Import-time assertions: prove all Phase 2 surfaces are present ---
from framework.tool_schema import (
    ReadFileAction, ReadFileObservation,
    RunCommandAction, RunCommandObservation,
    RunTestsAction, RunTestsObservation,
    ApplyPatchAction, ApplyPatchObservation,
)
from framework.typed_permission_gate import ToolPermission, PermissionRule, TypedPermissionGate
from framework.gated_tool_dispatch import GatedDispatchError, gated_run_command, gated_run_tests
from framework.workspace_scope import ToolPathScope, scope_from_runtime_workspace
from framework.sandbox_tool_dispatch import dispatch_run_command, dispatch_run_tests
from framework.runtime_execution_adapter import execute_typed_actions, extract_session_id
from framework.validation_artifact_writer import emit_validation_record, ValidationRecord
from framework.runtime_workspace_contract import build_workspace, RuntimeWorkspace
from framework.session_job_adapters import make_session_adapter, session_to_context_dict
from framework.read_file_dispatch import dispatch_read_file

assert callable(gated_run_command), "gated_run_command must be callable"
assert callable(execute_typed_actions), "execute_typed_actions must be callable"
assert callable(emit_validation_record), "emit_validation_record must be callable"
assert callable(build_workspace), "build_workspace must be callable"
assert callable(dispatch_read_file), "dispatch_read_file must be callable"


def make_bounded_context(
    session_like: Any,
    source_root: Path,
    base_root: Path,
    *,
    allow_commands: bool = True,
) -> dict:
    sid = extract_session_id(session_like)
    run_id = f"run-{sid[:8]}"

    workspace: RuntimeWorkspace = build_workspace(
        source_root=Path(source_root),
        base_root=Path(base_root),
        run_id=run_id,
        session_id=sid,
    )
    scope = scope_from_runtime_workspace(workspace)

    if allow_commands:
        gate = TypedPermissionGate(default_permission=ToolPermission.ALLOW)
    else:
        gate = TypedPermissionGate(
            rules=[
                PermissionRule(tool_name="run_command", permission=ToolPermission.DENY),
                PermissionRule(tool_name="run_tests", permission=ToolPermission.DENY),
            ],
            default_permission=ToolPermission.ALLOW,
        )

    return {
        "session": session_like,
        "workspace": workspace,
        "scope": scope,
        "gate": gate,
        "session_id": sid,
        "run_id": run_id,
    }


__all__ = ["make_bounded_context"]
