"""Bounded MVP coding loop: inspect → patch → validate → safe-stop."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from framework.apply_patch_dispatch import dispatch_apply_patch
from framework.context_retrieval import RetrievalQuery, retrieve_context
from framework.read_file_dispatch import dispatch_read_file
from framework.runtime_execution_adapter import execute_typed_actions
from framework.tool_schema import ApplyPatchAction, ReadFileAction, RunTestsAction
from framework.validation_emit_adapter import emit_loop_validation
from framework.workspace_scope import ToolPathScope

SAFE_TASK_KINDS = frozenset({"text_replacement", "helper_insertion", "metadata_addition"})


@dataclass(frozen=True)
class MVPTask:
    session_id: str
    target_path: str
    old_string: str
    new_string: str
    task_kind: str = "text_replacement"
    replace_all: bool = False
    enable_revert: bool = True
    retrieval_query: str = ""


@dataclass(frozen=True)
class MVPLoopResult:
    task_kind: str
    success: bool
    inspect_ok: bool
    patch_applied: bool
    test_passed: bool
    reverted: bool = False
    artifact_path: Optional[str] = None
    validation_artifact_path: Optional[str] = None
    error: Optional[str] = None


class MVPCodingLoopRunner:
    def __init__(
        self,
        session_like: Any,
        workspace_like: Any,
        gate: Any,
        scope: ToolPathScope,
        *,
        runner: Any = None,
        source_root: Optional[Path] = None,
    ):
        self._session_like = session_like
        self._workspace_like = workspace_like
        self._gate = gate
        self._scope = scope
        self._runner = runner
        self._source_root = source_root

    def run_task(self, task: MVPTask) -> MVPLoopResult:
        if not isinstance(task, MVPTask):
            raise TypeError(f"Expected MVPTask; got {type(task)!r}")

        job_id = f"mvp-{uuid4().hex[:12]}"

        # Validate task kind
        if task.task_kind not in SAFE_TASK_KINDS:
            return self._fail(
                task, job_id,
                error=f"unsafe task_kind: {task.task_kind!r}",
                inspect_ok=False, patch_applied=False,
            )

        # Inspect target file
        inspect_action = ReadFileAction(path=task.target_path)
        inspect_obs = dispatch_read_file(inspect_action, self._scope)
        if inspect_obs.error:
            return self._fail(
                task, job_id,
                error=f"inspect failed: {inspect_obs.error}",
                inspect_ok=False, patch_applied=False,
            )

        original_content = inspect_obs.content

        # Optional retrieval (non-blocking)
        if task.retrieval_query and self._source_root:
            try:
                retrieve_context(
                    RetrievalQuery(query=task.retrieval_query, top_k=3),
                    self._source_root,
                )
            except Exception:
                pass

        # Patch
        patch_action = ApplyPatchAction(
            path=task.target_path,
            old_string=task.old_string,
            new_string=task.new_string,
            replace_all=task.replace_all,
        )
        patch_obs = dispatch_apply_patch(patch_action, self._scope)

        if not patch_obs.applied:
            return self._fail(
                task, job_id,
                error=f"patch failed: {patch_obs.error}",
                inspect_ok=True, patch_applied=False,
            )

        # Validate via test run
        exec_summary = execute_typed_actions(
            self._session_like,
            self._workspace_like,
            self._gate,
            [RunTestsAction()],
            runner=self._runner,
        )
        test_passed = exec_summary.outcome == "pass"

        reverted = False
        if not test_passed and task.enable_revert:
            try:
                target = self._scope.resolve_path(task.target_path, writable=True)
                target.write_text(original_content, encoding="utf-8")
                reverted = True
            except Exception:
                pass

        artifact_path = self._write_artifact(task, job_id, patch_applied=True, test_passed=test_passed, reverted=reverted)
        val_path = self._emit_validation(task, job_id, patch_applied=True, test_passed=test_passed, reverted=reverted, artifact_path=artifact_path)

        success = patch_obs.applied and test_passed and not reverted
        return MVPLoopResult(
            task_kind=task.task_kind,
            success=success,
            inspect_ok=True,
            patch_applied=True,
            test_passed=test_passed,
            reverted=reverted,
            artifact_path=artifact_path,
            validation_artifact_path=val_path,
        )

    def _fail(
        self, task: MVPTask, job_id: str, *, error: str, inspect_ok: bool, patch_applied: bool
    ) -> MVPLoopResult:
        artifact_path = self._write_artifact(task, job_id, patch_applied=patch_applied, test_passed=False, reverted=False, error=error)
        val_path = self._emit_validation(task, job_id, patch_applied=patch_applied, test_passed=False, reverted=False, artifact_path=artifact_path)
        return MVPLoopResult(
            task_kind=task.task_kind,
            success=False,
            inspect_ok=inspect_ok,
            patch_applied=patch_applied,
            test_passed=False,
            artifact_path=artifact_path,
            validation_artifact_path=val_path,
            error=error,
        )

    def _write_artifact(
        self, task: MVPTask, job_id: str, *, patch_applied: bool, test_passed: bool, reverted: bool, error: Optional[str] = None,
    ) -> Optional[str]:
        try:
            artifact_root = Path(self._workspace_like.artifact_root)
            artifact_root.mkdir(parents=True, exist_ok=True)
            path = artifact_root / "mvp_loop_result.json"
            data = {
                "session_id": task.session_id,
                "job_id": job_id,
                "task_kind": task.task_kind,
                "target_path": task.target_path,
                "patch_applied": patch_applied,
                "test_passed": test_passed,
                "reverted": reverted,
                "success": patch_applied and test_passed and not reverted,
                "error": error,
            }
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return str(path)
        except OSError:
            return None

    def _emit_validation(
        self, task: MVPTask, job_id: str, *, patch_applied: bool, test_passed: bool, reverted: bool, artifact_path: Optional[str]
    ) -> Optional[str]:
        try:
            outcome = "pass" if (patch_applied and test_passed and not reverted) else "fail"
            artifact_dir = Path(self._workspace_like.artifact_root)
            artifact_dir.mkdir(parents=True, exist_ok=True)
            return emit_loop_validation(
                session_id=task.session_id,
                job_id=job_id,
                outcome=outcome,
                step_results=(
                    {"step": "patch", "success": patch_applied},
                    {"step": "test", "success": test_passed},
                ),
                artifact_dir=artifact_dir,
            )
        except Exception:
            return None


__all__ = ["MVPTask", "MVPLoopResult", "MVPCodingLoopRunner", "SAFE_TASK_KINDS"]
