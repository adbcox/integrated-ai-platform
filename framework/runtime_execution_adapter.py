"""Narrow runtime execution adapter binding session/workspace/gated-dispatch surfaces."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional
from uuid import uuid4

from framework.gated_tool_dispatch import GatedDispatchError, gated_run_command, gated_run_tests
from framework.tool_schema import RunCommandAction, RunTestsAction
from framework.workspace_scope import ToolPathScope, scope_from_runtime_workspace
from framework.validation_artifact_writer import (
    ValidationCheck,
    ValidationRecord,
    emit_validation_record,
)


def extract_session_id(session_like: Any) -> str:
    if isinstance(session_like, dict):
        if "session_id" not in session_like:
            raise ValueError("session_like mapping missing 'session_id' key")
        return str(session_like["session_id"])
    if hasattr(session_like, "session_id"):
        return str(session_like.session_id)
    raise ValueError(
        f"Cannot extract session_id from {type(session_like)!r}: "
        "expected object with .session_id or mapping with 'session_id' key"
    )


def make_job_id() -> str:
    return f"job-{uuid4().hex[:12]}"


@dataclass(frozen=True)
class ExecutionStepResult:
    action_type: str
    success: bool
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None


@dataclass(frozen=True)
class BoundedExecutionSummary:
    session_id: str
    job_id: str
    total_steps: int
    succeeded: int
    failed: int
    outcome: str
    steps: tuple = ()
    artifact_path: Optional[str] = None


def _adapt_workspace_scope(workspace_like: Any) -> tuple:
    required = ("source_root", "scratch_root", "artifact_root")
    missing = [a for a in required if not hasattr(workspace_like, a)]
    if missing:
        raise ValueError(
            f"workspace_like missing required attributes: {missing}"
        )
    scope = scope_from_runtime_workspace(workspace_like)
    return scope, Path(workspace_like.artifact_root)


def emit_runtime_validation_record(
    *,
    session_id: str,
    job_id: str,
    outcome: str,
    steps: tuple,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> Optional[str]:
    checks = tuple(
        ValidationCheck(
            check_name=f"step_{i}_{s.action_type}",
            outcome="pass" if s.success else "fail",
            detail=s.error,
        )
        for i, s in enumerate(steps)
    )
    record = ValidationRecord(
        emitter="runtime_execution_adapter",
        validation_type="bounded_execution",
        outcome=outcome,
        checks=checks,
        session_id=session_id,
        job_id=job_id,
    )
    return emit_validation_record(record, artifact_dir=artifact_dir, dry_run=dry_run)


def execute_typed_actions(
    session_like: Any,
    workspace_like: Any,
    gate: Any,
    actions: List[Any],
    *,
    runner: Any = None,
    extra_env: Optional[dict] = None,
) -> BoundedExecutionSummary:
    session_id = extract_session_id(session_like)
    job_id = make_job_id()
    scope, artifact_root = _adapt_workspace_scope(workspace_like)

    steps: List[ExecutionStepResult] = []

    for action in actions:
        if isinstance(action, RunCommandAction):
            try:
                obs = gated_run_command(action, scope, gate, runner=runner, extra_env=extra_env)
                steps.append(ExecutionStepResult(
                    action_type="run_command",
                    success=obs.exit_code == 0,
                    exit_code=obs.exit_code,
                    stdout=obs.stdout,
                    stderr=obs.stderr,
                ))
            except GatedDispatchError as exc:
                steps.append(ExecutionStepResult(
                    action_type="run_command",
                    success=False,
                    error=str(exc),
                ))
        elif isinstance(action, RunTestsAction):
            try:
                obs = gated_run_tests(action, scope, gate, runner=runner, extra_env=extra_env)
                steps.append(ExecutionStepResult(
                    action_type="run_tests",
                    success=obs.exit_code == 0,
                    exit_code=obs.exit_code,
                    stdout=obs.stdout,
                    stderr=obs.stderr,
                ))
            except GatedDispatchError as exc:
                steps.append(ExecutionStepResult(
                    action_type="run_tests",
                    success=False,
                    error=str(exc),
                ))
        else:
            raise TypeError(
                f"execute_typed_actions: unsupported action type {type(action)!r}; "
                "only RunCommandAction and RunTestsAction are supported"
            )

    succeeded = sum(1 for s in steps if s.success)
    failed = len(steps) - succeeded
    outcome = "pass" if failed == 0 else "fail"

    artifact_root.mkdir(parents=True, exist_ok=True)
    summary_path = artifact_root / "bounded_execution_summary.json"
    summary_dict = {
        "session_id": session_id,
        "job_id": job_id,
        "total_steps": len(steps),
        "succeeded": succeeded,
        "failed": failed,
        "outcome": outcome,
        "steps": [
            {
                "action_type": s.action_type,
                "success": s.success,
                "exit_code": s.exit_code,
                "stdout": s.stdout,
                "stderr": s.stderr,
                "error": s.error,
            }
            for s in steps
        ],
    }
    summary_path.write_text(json.dumps(summary_dict, indent=2), encoding="utf-8")

    emit_runtime_validation_record(
        session_id=session_id,
        job_id=job_id,
        outcome=outcome,
        steps=tuple(steps),
        artifact_dir=artifact_root,
    )

    return BoundedExecutionSummary(
        session_id=session_id,
        job_id=job_id,
        total_steps=len(steps),
        succeeded=succeeded,
        failed=failed,
        outcome=outcome,
        steps=tuple(steps),
        artifact_path=str(summary_path),
    )


__all__ = [
    "ExecutionStepResult",
    "BoundedExecutionSummary",
    "extract_session_id",
    "make_job_id",
    "emit_runtime_validation_record",
    "execute_typed_actions",
]
