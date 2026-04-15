"""Worker runtime for bounded parallel execution."""

from __future__ import annotations

import os
import queue
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .inference_adapter import InferenceAdapter, InferenceRequest
from .job_schema import Job, JobAction, JobLifecycle, ValidationRequirement
from .learning_hooks import LearningHooks
from .permission_engine import PermissionEngine
from .queue_types import QueueEnvelope
from .sandbox import LocalSandboxRunner
from .state_store import StateStore
from .tool_system import ToolAction, ToolName, ToolObservation, ToolStatus
from .workspace import WorkspaceController


@dataclass(frozen=True)
class WorkerOutcome:
    job_id: str
    status: str
    return_code: int
    output: str
    error: str
    validation: dict[str, Any]


class WorkerRuntime:
    """Single worker runtime instance that executes jobs serially."""
    _conflict_domain_locks: dict[str, threading.BoundedSemaphore] = {}
    _conflict_domain_guard = threading.Lock()

    def __init__(
        self,
        *,
        worker_id: str,
        queue_ref: "queue.PriorityQueue[QueueEnvelope]",
        inference: InferenceAdapter,
        store: StateStore,
        learning: LearningHooks,
        stop_event: threading.Event,
        context_release_callback,
        dequeue_callback=None,
        class_semaphores: dict[str, threading.BoundedSemaphore] | None = None,
        permission_engine: PermissionEngine | None = None,
        workspace_controller: WorkspaceController | None = None,
        sandbox_runner: LocalSandboxRunner | None = None,
    ) -> None:
        self.worker_id = worker_id
        self.queue = queue_ref
        self.inference = inference
        self.store = store
        self.learning = learning
        self.stop_event = stop_event
        self._context_release_callback = context_release_callback
        self._dequeue_callback = dequeue_callback
        self._class_semaphores = class_semaphores or {}
        self._permission_engine = permission_engine or PermissionEngine()
        self._workspace_controller = workspace_controller or WorkspaceController(self.store.root)
        self._sandbox_runner = sandbox_runner or LocalSandboxRunner()

    def run_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                envelope = self.queue.get(timeout=0.25)
            except queue.Empty:
                continue
            job = envelope.job
            if self._dequeue_callback is not None:
                self._dequeue_callback(job)

            job.set_lifecycle(JobLifecycle.DISPATCHED, reason=f"worker={self.worker_id}")
            self.store.save_job(job)
            self.store.append_trace({
                "kind": "worker_job_start",
                "worker_id": self.worker_id,
                "job_id": job.job_id,
            })
            result_payload = self._execute_job(job)
            result_path = self.store.save_result(job.job_id, result_payload)
            learning_event = self.learning.emit(job=job, result=result_payload, result_path=result_path)
            self.store.append_trace({
                "kind": "worker_job_end",
                "worker_id": self.worker_id,
                "job_id": job.job_id,
                "status": result_payload.get("status"),
                "learning_event": learning_event.to_dict(),
            })
            self._context_release_callback(job)
            self.queue.task_done()

    def _execute_job(self, job: Job) -> dict[str, Any]:
        conflict_domain = self._resolve_conflict_domain(job)
        conflict_lock = self._acquire_conflict_lock(conflict_domain, job)
        class_limit = self._class_semaphores.get(job.task_class.value)
        if class_limit is not None:
            self.store.append_trace(
                {
                    "kind": "class_slot_wait_start",
                    "worker_id": self.worker_id,
                    "job_id": job.job_id,
                    "task_class": job.task_class.value,
                }
            )
            class_limit.acquire()
            self.store.append_trace(
                {
                    "kind": "class_slot_acquired",
                    "worker_id": self.worker_id,
                    "job_id": job.job_id,
                    "task_class": job.task_class.value,
                }
            )

        try:
            job.set_lifecycle(JobLifecycle.RUNNING, reason=f"worker={self.worker_id}")
            self.store.save_job(job)

            attempts = 0
            while True:
                attempts += 1
                job.attempts_used = attempts
                job.updated_at_utc = datetime.now(UTC).isoformat(timespec="seconds")
                self.store.save_job(job)

                outcome = self._execute_attempt(job)
                passed = bool(outcome.validation.get("passed", False))
                if outcome.status == "completed" and passed:
                    job.set_lifecycle(JobLifecycle.COMPLETED, reason="worker_completed")
                    self.store.save_job(job)
                    return {
                        "job_id": job.job_id,
                        "status": "completed",
                        "worker_id": self.worker_id,
                        "attempts_used": attempts,
                        "return_code": outcome.return_code,
                        "output": outcome.output,
                        "error": outcome.error,
                        "validation": outcome.validation,
                        "requested_outputs": job.requested_outputs,
                    }

                budget = max(0, job.retry_policy.retry_budget)
                if attempts <= budget:
                    job.set_lifecycle(JobLifecycle.RETRY_WAITING, reason="retry_budget_available")
                    self.store.save_job(job)
                    if job.retry_policy.retry_backoff_seconds > 0:
                        time.sleep(job.retry_policy.retry_backoff_seconds)
                    continue

                if job.escalation_policy.allow_auto_escalation and job.escalation_policy.escalate_on_retry_exhaustion:
                    job.set_lifecycle(JobLifecycle.ESCALATED, reason=job.escalation_policy.escalation_label)
                    self.store.save_job(job)
                    payload = {
                        "job_id": job.job_id,
                        "status": "escalated",
                        "worker_id": self.worker_id,
                        "attempts_used": attempts,
                        "return_code": outcome.return_code,
                        "output": outcome.output,
                        "error": outcome.error,
                        "validation": outcome.validation,
                        "status_reason": job.status_reason,
                        "requested_outputs": job.requested_outputs,
                    }
                    self.store.save_dead_letter_record(
                        job=job,
                        result_payload=payload,
                        reason="escalated_retry_budget_exhausted",
                    )
                    return payload

                job.set_lifecycle(JobLifecycle.FAILED, reason="retry_budget_exhausted")
                self.store.save_job(job)
                payload = {
                    "job_id": job.job_id,
                    "status": "failed",
                    "worker_id": self.worker_id,
                    "attempts_used": attempts,
                    "return_code": outcome.return_code,
                    "output": outcome.output,
                    "error": outcome.error,
                    "validation": outcome.validation,
                    "status_reason": job.status_reason,
                    "requested_outputs": job.requested_outputs,
                }
                self.store.save_dead_letter_record(
                    job=job,
                    result_payload=payload,
                    reason="failed_retry_budget_exhausted",
                )
                return payload
        finally:
            if class_limit is not None:
                class_limit.release()
                self.store.append_trace(
                    {
                        "kind": "class_slot_released",
                        "worker_id": self.worker_id,
                        "job_id": job.job_id,
                        "task_class": job.task_class.value,
                        "final_lifecycle": job.lifecycle.value,
                    }
                )
            self._release_conflict_lock(conflict_domain, conflict_lock, job)

    def _execute_attempt(self, job: Job) -> WorkerOutcome:
        workspace = self._workspace_controller.for_job(job)
        prompt = str(job.metadata.get("inference_prompt") or "")
        context = {
            "task_class": job.task_class.value,
            "requested_outputs": job.requested_outputs,
            "artifact_inputs": self._artifact_context(job.artifact_inputs),
            "workspace": {
                "repo_root": str(workspace.repo_root),
                "worktree_target": str(workspace.worktree_target),
                "artifact_root": str(workspace.artifact_root),
            },
        }
        inference = self.inference.run(InferenceRequest(job_id=job.job_id, prompt=prompt, context=context))

        output = inference.output_text
        error = ""
        rc = 0
        if job.action in {JobAction.SHELL_COMMAND, JobAction.INFERENCE_AND_SHELL}:
            command = str(job.metadata.get("shell_command") or "")
            if not command:
                rc = 2
                error = "missing_shell_command"
            else:
                tool_action = ToolAction(
                    job_id=job.job_id,
                    tool=ToolName.RUN_COMMAND,
                    arguments={"command": command},
                )
                permission = self._permission_engine.evaluate(
                    action=tool_action,
                    allowed_tools_actions=job.allowed_tools_actions,
                    metadata=job.metadata,
                )
                self.store.append_trace(
                    {
                        "kind": "tool_permission_decision",
                        "worker_id": self.worker_id,
                        "job_id": job.job_id,
                        "tool_action": tool_action.to_dict(),
                        "permission": permission.to_dict(),
                    }
                )
                if not permission.allowed:
                    rc = 126
                    error = f"permission_denied:{permission.reason}"
                    observation = ToolObservation(
                        job_id=job.job_id,
                        tool=ToolName.RUN_COMMAND,
                        status=ToolStatus.BLOCKED,
                        allowed=False,
                        output=output,
                        error=error,
                        return_code=rc,
                        metadata={"permission_reason": permission.reason},
                    )
                    self.store.append_trace(
                        {
                            "kind": "tool_observation",
                            "worker_id": self.worker_id,
                            "job_id": job.job_id,
                            "observation": observation.to_dict(),
                        }
                    )
                else:
                    try:
                        sandbox_result = self._sandbox_runner.run_command(
                            command=command,
                            cwd=workspace.worktree_target,
                            env=self._build_env(job),
                        )
                        rc = sandbox_result.return_code
                        output = f"{inference.output_text}\n{sandbox_result.stdout}".strip()
                        error = sandbox_result.stderr.strip()
                        observation = ToolObservation(
                            job_id=job.job_id,
                            tool=ToolName.RUN_COMMAND,
                            status=ToolStatus.EXECUTED if rc == 0 else ToolStatus.FAILED,
                            allowed=True,
                            output=output[-4000:],
                            error=error[-2000:],
                            return_code=rc,
                            metadata={"sandbox_mode": self._sandbox_runner.mode},
                        )
                    except subprocess.TimeoutExpired:
                        rc = 124
                        error = "sandbox_timeout"
                        observation = ToolObservation(
                            job_id=job.job_id,
                            tool=ToolName.RUN_COMMAND,
                            status=ToolStatus.FAILED,
                            allowed=True,
                            output=output,
                            error=error,
                            return_code=rc,
                            metadata={"sandbox_mode": self._sandbox_runner.mode},
                        )
                    self.store.append_trace(
                        {
                            "kind": "tool_observation",
                            "worker_id": self.worker_id,
                            "job_id": job.job_id,
                            "observation": observation.to_dict(),
                        }
                    )

        validation = self._validate(job=job, return_code=rc)
        status = "completed" if rc == 0 else "failed"
        return WorkerOutcome(
            job_id=job.job_id,
            status=status,
            return_code=rc,
            output=output,
            error=error,
            validation=validation,
        )

    def _artifact_context(self, inputs: list[str]) -> list[dict[str, Any]]:
        artifacts: list[dict[str, Any]] = []
        for raw in inputs:
            path = Path(raw)
            exists = path.exists()
            row: dict[str, Any] = {
                "path": str(path),
                "exists": exists,
            }
            if exists and path.is_file():
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    text = ""
                row["size_bytes"] = path.stat().st_size
                row["preview"] = text[:240]
            artifacts.append(row)
        return artifacts

    def _validate(self, *, job: Job, return_code: int) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        passed = True
        for requirement in job.validation_requirements:
            req_ok = True
            detail = ""
            if requirement == ValidationRequirement.EXIT_CODE_ZERO:
                req_ok = return_code == 0
                detail = f"return_code={return_code}"
            elif requirement == ValidationRequirement.ARTIFACT_WRITTEN:
                req_ok = any(Path(path).exists() for path in job.requested_outputs)
                detail = f"requested_outputs={len(job.requested_outputs)}"
            elif requirement == ValidationRequirement.PYTHON_COMPILE:
                req_ok = self._python_compile_check(job.requested_outputs)
                detail = "python_compile"
            elif requirement == ValidationRequirement.SHELL_SYNTAX:
                req_ok = self._shell_syntax_check(job.requested_outputs)
                detail = "shell_syntax"
            checks.append({"requirement": requirement.value, "passed": req_ok, "detail": detail})
            if not req_ok:
                passed = False
        return {"passed": passed, "checks": checks}

    def _python_compile_check(self, paths: list[str]) -> bool:
        for raw in paths:
            path = Path(raw)
            if path.suffix != ".py":
                continue
            proc = subprocess.run(["python3", "-m", "py_compile", str(path)], capture_output=True, text=True)
            if proc.returncode != 0:
                return False
        return True

    def _shell_syntax_check(self, paths: list[str]) -> bool:
        for raw in paths:
            path = Path(raw)
            if path.suffix != ".sh":
                continue
            proc = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            if proc.returncode != 0:
                return False
        return True

    def _build_env(self, job: Job) -> dict[str, str]:
        env = os.environ.copy()
        env["FRAMEWORK_JOB_ID"] = job.job_id
        env["FRAMEWORK_TASK_CLASS"] = job.task_class.value
        env["FRAMEWORK_CONTEXT_ID"] = job.execution_context_id
        return env

    def _resolve_conflict_domain(self, job: Job) -> str:
        raw = str(job.metadata.get("conflict_domain") or "").strip().lower()
        if raw and raw != "auto":
            return raw
        return str(job.target.worktree_target).strip() or str(job.target.repo_root).strip() or "default"

    def _acquire_conflict_lock(self, conflict_domain: str, job: Job) -> threading.BoundedSemaphore | None:
        if not conflict_domain or conflict_domain == "none":
            return None
        with self._conflict_domain_guard:
            lock = self._conflict_domain_locks.get(conflict_domain)
            if lock is None:
                lock = threading.BoundedSemaphore(value=1)
                self._conflict_domain_locks[conflict_domain] = lock
        self.store.append_trace(
            {
                "kind": "conflict_domain_wait_start",
                "worker_id": self.worker_id,
                "job_id": job.job_id,
                "conflict_domain": conflict_domain,
            }
        )
        lock.acquire()
        self.store.append_trace(
            {
                "kind": "conflict_domain_acquired",
                "worker_id": self.worker_id,
                "job_id": job.job_id,
                "conflict_domain": conflict_domain,
            }
        )
        return lock

    def _release_conflict_lock(
        self,
        conflict_domain: str,
        lock: threading.BoundedSemaphore | None,
        job: Job,
    ) -> None:
        if lock is None:
            return
        lock.release()
        self.store.append_trace(
            {
                "kind": "conflict_domain_released",
                "worker_id": self.worker_id,
                "job_id": job.job_id,
                "conflict_domain": conflict_domain,
                "final_lifecycle": job.lifecycle.value,
            }
        )


class WorkerPool:
    """Bounded worker pool that runs worker runtime loops."""

    def __init__(self, workers: list[WorkerRuntime], stop_event: threading.Event) -> None:
        self.workers = workers
        self.stop_event = stop_event
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        for worker in self.workers:
            t = threading.Thread(target=worker.run_loop, name=f"framework-{worker.worker_id}", daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self, *, join_timeout_seconds: float = 2.0) -> None:
        self.stop_event.set()
        for thread in self._threads:
            thread.join(timeout=join_timeout_seconds)
