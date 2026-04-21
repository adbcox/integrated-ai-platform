"""Bounded file-local coding loop: patch → test → artifact, one attempt."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from framework.apply_patch_dispatch import dispatch_apply_patch
from framework.runtime_execution_adapter import execute_typed_actions
from framework.tool_schema import ApplyPatchAction, RunTestsAction
from framework.workspace_scope import ToolPathScope

_SAFE_TASK_KINDS = frozenset({"text_replacement", "helper_insertion", "metadata_addition"})


@dataclass(frozen=True)
class FileLocalTask:
    session_id: str
    target_path: str
    old_string: str
    new_string: str
    task_kind: str = "text_replacement"
    replace_all: bool = False


@dataclass(frozen=True)
class FileLocalResult:
    task_kind: str
    success: bool
    patch_applied: bool
    test_passed: bool
    artifact_path: Optional[str] = None
    error: Optional[str] = None


class FileLocalDevloopRunner:
    def __init__(
        self,
        session_like: Any,
        workspace_like: Any,
        gate: Any,
        scope: ToolPathScope,
        *,
        runner: Any = None,
    ):
        self._session_like = session_like
        self._workspace_like = workspace_like
        self._gate = gate
        self._scope = scope
        self._runner = runner

    def run_task(self, task: FileLocalTask) -> FileLocalResult:
        if not isinstance(task, FileLocalTask):
            raise TypeError(f"Expected FileLocalTask; got {type(task)!r}")
        if task.task_kind not in _SAFE_TASK_KINDS:
            return FileLocalResult(
                task_kind=task.task_kind,
                success=False,
                patch_applied=False,
                test_passed=False,
                error=f"unsafe task_kind: {task.task_kind!r}; allowed: {sorted(_SAFE_TASK_KINDS)}",
            )

        patch_action = ApplyPatchAction(
            path=task.target_path,
            old_string=task.old_string,
            new_string=task.new_string,
            replace_all=task.replace_all,
        )
        patch_obs = dispatch_apply_patch(patch_action, self._scope)

        if not patch_obs.applied:
            artifact_path = self._write_artifact(task, patch_applied=False, test_passed=False, error=patch_obs.error)
            return FileLocalResult(
                task_kind=task.task_kind,
                success=False,
                patch_applied=False,
                test_passed=False,
                artifact_path=artifact_path,
                error=patch_obs.error,
            )

        exec_summary = execute_typed_actions(
            self._session_like,
            self._workspace_like,
            self._gate,
            [RunTestsAction()],
            runner=self._runner,
        )
        test_passed = exec_summary.outcome == "pass"
        artifact_path = self._write_artifact(task, patch_applied=True, test_passed=test_passed)

        return FileLocalResult(
            task_kind=task.task_kind,
            success=patch_obs.applied and test_passed,
            patch_applied=patch_obs.applied,
            test_passed=test_passed,
            artifact_path=artifact_path,
        )

    def _write_artifact(
        self,
        task: FileLocalTask,
        *,
        patch_applied: bool,
        test_passed: bool,
        error: Optional[str] = None,
    ) -> Optional[str]:
        try:
            artifact_root = Path(self._workspace_like.artifact_root)
            artifact_root.mkdir(parents=True, exist_ok=True)
            path = artifact_root / "file_local_devloop_result.json"
            data = {
                "session_id": task.session_id,
                "task_kind": task.task_kind,
                "target_path": task.target_path,
                "patch_applied": patch_applied,
                "test_passed": test_passed,
                "success": patch_applied and test_passed,
                "error": error,
            }
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return str(path)
        except OSError:
            return None


__all__ = ["FileLocalTask", "FileLocalResult", "FileLocalDevloopRunner"]
