"""Worker runtime for bounded parallel execution."""

from __future__ import annotations

import os
import queue
import subprocess
import threading
import time
from hashlib import sha256
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .canonical_job_schema import CanonicalJob
from .canonical_session_schema import CanonicalSession
from .compat import UTC
from .inference_adapter import InferenceAdapter, InferenceRequest
from .job_schema import Job, JobAction, JobLifecycle, ValidationRequirement
from .learning_hooks import LearningHooks
from .permission_engine import PermissionEngine
from .phase2_session_bundle import build_phase2_session_bundle
from .queue_types import QueueEnvelope
from .sandbox import LocalSandboxRunner
from .state_store import StateStore
from .tool_action_observation_contract import (
    ToolActionRecord,
    ToolContractName,
    ToolContractStatus,
    ToolObservationRecord,
)
from .tool_contract_builders import (
    build_blocked_tool_observation,
    build_tool_action,
    build_tool_observation,
)
from .tool_system import ToolAction, ToolName, ToolObservation, ToolStatus
from .workspace import WorkspaceController


_RUNTIME_TO_CONTRACT_TOOL: dict[ToolName, ToolContractName] = {
    ToolName.RUN_COMMAND: ToolContractName.RUN_COMMAND,
    ToolName.RUN_TESTS: ToolContractName.RUN_TESTS,
    ToolName.APPLY_EDIT: ToolContractName.APPLY_PATCH,
    ToolName.INFERENCE: ToolContractName.READ_FILE,
}


def _runtime_tool_to_contract(tool: ToolName) -> ToolContractName:
    return _RUNTIME_TO_CONTRACT_TOOL.get(tool, ToolContractName.RUN_COMMAND)


@dataclass(frozen=True)
class WorkerOutcome:
    job_id: str
    status: str
    return_code: int
    output: str
    error: str
    validation: dict[str, Any]
    failure_class: str = ""
    retry_recommended: bool = True


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
        self._phase2_collectors: dict[str, dict[str, Any]] = {}
        self._phase2_action_counters: dict[str, int] = {}

    def _phase2_session_id(self, job: Job) -> str:
        candidate = job.metadata.get("session_id") if isinstance(job.metadata, dict) else None
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
        return f"session-{job.job_id}"

    def _phase2_build_session(self, job: Job) -> CanonicalSession:
        metadata = job.metadata if isinstance(job.metadata, dict) else {}
        allowed_tools = list(job.allowed_tools_actions) if job.allowed_tools_actions else []
        return CanonicalSession(
            session_id=self._phase2_session_id(job),
            task_id=job.job_id,
            repo_id=str(metadata.get("repo_id") or ""),
            branch=str(metadata.get("branch") or ""),
            requester=str(metadata.get("requester") or self.worker_id),
            created_at=job.created_at_utc,
            updated_at=job.updated_at_utc,
            task_class=job.task_class.value,
            objective=str(metadata.get("objective") or ""),
            constraints=[str(c) for c in (metadata.get("constraints") or [])],
            allowed_tools=allowed_tools,
            risk_tier=str(metadata.get("risk_tier") or "standard"),
            stop_conditions=[str(c) for c in (metadata.get("stop_conditions") or [])],
            selected_model_profile=str(metadata.get("model_profile") or ""),
            selected_runtime=str(metadata.get("runtime") or "local"),
            critique_model=str(metadata.get("critique_model") or ""),
            retry_budget=int(job.retry_policy.retry_budget or 0),
            token_budget=int(metadata.get("token_budget") or 0),
            workspace_id=str(job.execution_context_id or job.job_id),
            source_mount=str(job.target.repo_root),
            scratch_mount=str(job.target.worktree_target),
            artifact_root=str(self.store.root),
            network_policy=str(metadata.get("network_policy") or "disabled"),
        )

    def _phase2_begin(self, job: Job) -> None:
        session = self._phase2_build_session(job)
        canonical_job = CanonicalJob.from_session(session, job_id=job.job_id)
        self._phase2_collectors[job.job_id] = {
            "session": session,
            "jobs": [canonical_job],
            "tool_actions": [],
            "tool_observations": [],
            "permission_decisions": [],
        }
        self._phase2_action_counters[job.job_id] = 0

    def _phase2_next_action_id(self, job: Job) -> str:
        count = self._phase2_action_counters.get(job.job_id, 0) + 1
        self._phase2_action_counters[job.job_id] = count
        return f"{job.job_id}-action-{count}"

    def _phase2_has_collector(self, job: Job) -> bool:
        return job.job_id in self._phase2_collectors

    def _phase2_record_typed_action(
        self,
        *,
        job: Job,
        action: ToolAction,
    ) -> ToolActionRecord:
        if not self._phase2_has_collector(job):
            return ToolActionRecord(
                action_id=self._phase2_next_action_id(job),
                session_id=self._phase2_session_id(job),
                job_id=job.job_id,
                tool_name=_runtime_tool_to_contract(action.tool),
                arguments=dict(action.arguments),
                requested_by="worker_runtime",
            )
        record = build_tool_action(
            action_id=self._phase2_next_action_id(job),
            session_id=self._phase2_session_id(job),
            job_id=job.job_id,
            tool_name=_runtime_tool_to_contract(action.tool),
            arguments=dict(action.arguments),
            requested_by="worker_runtime",
        )
        self._phase2_collectors[job.job_id]["tool_actions"].append(record)
        return record

    def _phase2_record_permission_decision(
        self,
        *,
        job: Job,
        action: ToolAction,
        decision_payload: dict[str, Any],
    ) -> None:
        if not self._phase2_has_collector(job):
            return
        self._phase2_collectors[job.job_id]["permission_decisions"].append(
            {
                "tool": action.tool.value,
                "arguments": dict(action.arguments),
                **decision_payload,
            }
        )

    def _phase2_record_blocked(
        self,
        *,
        job: Job,
        typed_action: ToolActionRecord,
        reason: str,
    ) -> ToolObservationRecord:
        record = build_blocked_tool_observation(action=typed_action, reason=reason)
        if self._phase2_has_collector(job):
            self._phase2_collectors[job.job_id]["tool_observations"].append(record)
        return record

    def _phase2_record_observation(
        self,
        *,
        job: Job,
        typed_action: ToolActionRecord,
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
        record = build_tool_observation(
            action=typed_action,
            status=status,
            allowed=allowed,
            duration_ms=duration_ms,
            stdout=stdout,
            stderr=stderr,
            structured_payload=structured_payload,
            side_effect_metadata=side_effect_metadata,
            error=error,
            return_code=return_code,
        )
        if self._phase2_has_collector(job):
            self._phase2_collectors[job.job_id]["tool_observations"].append(record)
        return record

    def _phase2_finalize(self, job: Job, *, final_outcome: str) -> dict[str, Any]:
        collector = self._phase2_collectors.get(job.job_id)
        if collector is None:
            return {}
        session: CanonicalSession = collector["session"]
        canonical_jobs = collector["jobs"]
        tool_actions = collector["tool_actions"]
        tool_observations = collector["tool_observations"]
        permission_decisions = list(collector["permission_decisions"])
        session.final_outcome = final_outcome
        session.updated_at = datetime.now(UTC).isoformat(timespec="seconds")
        session.tool_trace = [a.to_dict() for a in tool_actions] + [
            o.to_dict() for o in tool_observations
        ]
        session.permission_decisions = list(permission_decisions)
        typed_trace: list[dict[str, Any]] = []
        for a in tool_actions:
            typed_trace.append({"kind": "tool_action", **a.to_dict()})
        for o in tool_observations:
            typed_trace.append({"kind": "tool_observation", **o.to_dict()})
        bundle = build_phase2_session_bundle(
            session=session,
            jobs=canonical_jobs,
            tool_actions=tool_actions,
            tool_observations=tool_observations,
            permission_decisions=permission_decisions,
            final_outcome=final_outcome,
        )
        for job_obj in canonical_jobs:
            job_obj.final_outcome = final_outcome
            job_obj.status = final_outcome
        return {
            "canonical_session": session.to_dict(),
            "canonical_jobs": [j.to_dict() for j in canonical_jobs],
            "typed_tool_trace": typed_trace,
            "permission_decisions": permission_decisions,
            "session_bundle": bundle,
            "final_outcome": final_outcome,
        }

    def _phase2_clear(self, job: Job) -> None:
        self._phase2_collectors.pop(job.job_id, None)
        self._phase2_action_counters.pop(job.job_id, None)

    def run_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                envelope = self.queue.get(timeout=0.25)
            except queue.Empty:
                continue
            job = envelope.job
            if self._dequeue_callback is not None:
                self._dequeue_callback(job)

            try:
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
            finally:
                self.queue.task_done()

    def _execute_job(self, job: Job) -> dict[str, Any]:
        self._phase2_begin(job)
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
                self.store.append_trace(
                    {
                        "kind": "worker_failure_diagnosis",
                        "worker_id": self.worker_id,
                        "job_id": job.job_id,
                        "attempt": attempts,
                        "failure_class": outcome.failure_class,
                        "retry_recommended": outcome.retry_recommended,
                        "return_code": outcome.return_code,
                    }
                )
                if outcome.status == "completed" and passed:
                    job.set_lifecycle(JobLifecycle.COMPLETED, reason="worker_completed")
                    self.store.save_job(job)
                    payload = {
                        "job_id": job.job_id,
                        "status": "completed",
                        "worker_id": self.worker_id,
                        "attempts_used": attempts,
                        "return_code": outcome.return_code,
                        "output": outcome.output,
                        "error": outcome.error,
                        "validation": outcome.validation,
                        "failure_class": outcome.failure_class,
                        "requested_outputs": job.requested_outputs,
                    }
                    payload.update(self._phase2_finalize(job, final_outcome="completed"))
                    return payload

                budget = max(0, job.retry_policy.retry_budget)
                if attempts <= budget and outcome.retry_recommended:
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
                        "failure_class": outcome.failure_class,
                        "retry_recommended": outcome.retry_recommended,
                        "status_reason": job.status_reason,
                        "requested_outputs": job.requested_outputs,
                    }
                    payload.update(self._phase2_finalize(job, final_outcome="escalated"))
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
                    "failure_class": outcome.failure_class,
                    "retry_recommended": outcome.retry_recommended,
                    "status_reason": job.status_reason,
                    "requested_outputs": job.requested_outputs,
                }
                payload.update(self._phase2_finalize(job, final_outcome="failed"))
                self.store.save_dead_letter_record(
                    job=job,
                    result_payload=payload,
                    reason="failed_retry_budget_exhausted",
                )
                return payload
        finally:
            self._phase2_clear(job)
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
        output_snapshot_before = self._snapshot_requested_outputs(job.requested_outputs)
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

        inner_loop = job.metadata.get("inner_loop") if isinstance(job.metadata.get("inner_loop"), dict) else {}
        if bool(inner_loop.get("enabled")):
            return self._execute_inner_loop(
                job=job,
                workspace=workspace,
                inference_output=inference.output_text,
                config=inner_loop,
                output_snapshot_before=output_snapshot_before,
            )

        output = inference.output_text
        error = ""
        rc = 0
        if job.action in {JobAction.SHELL_COMMAND, JobAction.INFERENCE_AND_SHELL}:
            command = str(job.metadata.get("shell_command") or "")
            if not command:
                rc = 2
                error = "missing_shell_command"
            else:
                rc, command_output, error = self._run_command_tool(job=job, workspace=workspace, command=command)
                output = f"{inference.output_text}\n{command_output}".strip()

        validation = self._validate(job=job, return_code=rc, output_snapshot_before=output_snapshot_before)
        status = "completed" if rc == 0 else "failed"
        failure_class = "" if (status == "completed" and bool(validation.get("passed", False))) else self._derive_failure_class(
            return_code=rc,
            error=error,
            validation=validation,
        )
        return WorkerOutcome(
            job_id=job.job_id,
            status=status,
            return_code=rc,
            output=output,
            error=error,
            validation=validation,
            failure_class=failure_class,
            retry_recommended=self._is_retryable_failure(failure_class),
        )

    def _execute_inner_loop(
        self,
        *,
        job: Job,
        workspace,
        inference_output: str,
        config: dict[str, Any],
        output_snapshot_before: dict[str, dict[str, Any]],
    ) -> WorkerOutcome:
        setup_command = str(config.get("setup_command") or "").strip()
        validate_command = str(config.get("validate_command") or "").strip()
        repair_edits = config.get("repair_edits") if isinstance(config.get("repair_edits"), list) else []
        coordinated_repairs = bool(config.get("coordinated_repairs"))
        max_cycles = max(1, int(config.get("max_cycles") or (len(repair_edits) + 1)))
        tracked_paths = [
            self._workspace_controller.resolve_in_repo(workspace, str(path))
            for path in (config.get("tracked_paths") or [])
            if str(path).strip()
        ]
        snapshots = self._snapshot_paths(tracked_paths)

        loop_notes: list[str] = []
        if setup_command:
            setup_rc, _, setup_err = self._run_command_tool(job=job, workspace=workspace, command=setup_command)
            if setup_rc != 0:
                self._restore_snapshot(snapshots, reason="setup_failed", job=job)
                return WorkerOutcome(
                    job_id=job.job_id,
                    status="failed",
                    return_code=setup_rc,
                    output=inference_output,
                    error=f"inner_loop_setup_failed:{setup_err}",
                    validation={"passed": False, "checks": [{"requirement": "inner_loop_setup", "passed": False}]},
                    failure_class="inner_loop_setup_failed",
                    retry_recommended=False,
                )
            loop_notes.append("setup_completed")

        if not validate_command:
            self._restore_snapshot(snapshots, reason="missing_validate_command", job=job)
            return WorkerOutcome(
                job_id=job.job_id,
                status="failed",
                return_code=2,
                output=inference_output,
                error="inner_loop_missing_validate_command",
                validation={"passed": False, "checks": [{"requirement": "inner_loop_config", "passed": False}]},
                failure_class="inner_loop_config_error",
                retry_recommended=False,
            )

        repair_index = 0
        for cycle in range(1, max_cycles + 1):
            rc, validate_out, validate_err = self._run_command_tool(job=job, workspace=workspace, command=validate_command)
            self.store.append_trace(
                {
                    "kind": "inner_loop_cycle",
                    "worker_id": self.worker_id,
                    "job_id": job.job_id,
                    "cycle": cycle,
                    "validate_command": validate_command,
                    "return_code": rc,
                }
            )
            if rc == 0:
                validation = self._validate(job=job, return_code=0, output_snapshot_before=output_snapshot_before)
                return WorkerOutcome(
                    job_id=job.job_id,
                    status="completed",
                    return_code=0,
                    output=f"{inference_output}\n{validate_out}".strip(),
                    error="",
                    validation=validation,
                    failure_class="",
                    retry_recommended=False,
                )

            if repair_index >= len(repair_edits):
                self._restore_snapshot(snapshots, reason="repairs_exhausted", job=job)
                validation = self._validate(job=job, return_code=rc, output_snapshot_before=output_snapshot_before)
                error_text = f"inner_loop_exhausted:{validate_err}"
                failure_class = self._derive_failure_class(
                    return_code=rc,
                    error=error_text,
                    validation=validation,
                )
                return WorkerOutcome(
                    job_id=job.job_id,
                    status="failed",
                    return_code=rc,
                    output=f"{inference_output}\n{validate_out}".strip(),
                    error=error_text,
                    validation=validation,
                    failure_class=failure_class,
                    retry_recommended=self._is_retryable_failure(failure_class),
                )

            repair = repair_edits[repair_index] if isinstance(repair_edits[repair_index], dict) else {}
            if coordinated_repairs:
                batch = [row for row in repair_edits[repair_index:] if isinstance(row, dict)]
                applied, apply_error = self._apply_edit_batch_tool(job=job, workspace=workspace, repairs=batch)
                repair_index = len(repair_edits)
                loop_notes.append(f"repair_batch:{'applied' if applied else 'failed'}")
            else:
                repair_index += 1
                applied, apply_error = self._apply_edit_tool(job=job, workspace=workspace, repair=repair)
                loop_notes.append(f"repair_{repair_index}:{'applied' if applied else 'failed'}")
            if not applied:
                self._restore_snapshot(snapshots, reason="repair_failed", job=job)
                validation = self._validate(job=job, return_code=rc, output_snapshot_before=output_snapshot_before)
                error_text = f"inner_loop_repair_failed:{apply_error}"
                failure_class = self._derive_failure_class(
                    return_code=rc,
                    error=error_text,
                    validation=validation,
                )
                return WorkerOutcome(
                    job_id=job.job_id,
                    status="failed",
                    return_code=rc,
                    output=f"{inference_output}\n{validate_out}".strip(),
                    error=error_text,
                    validation=validation,
                    failure_class=failure_class,
                    retry_recommended=self._is_retryable_failure(failure_class),
                )

        self._restore_snapshot(snapshots, reason="cycle_limit_reached", job=job)
        validation = self._validate(job=job, return_code=1, output_snapshot_before=output_snapshot_before)
        error_text = f"inner_loop_cycle_limit_reached:{'|'.join(loop_notes)}"
        failure_class = self._derive_failure_class(
            return_code=1,
            error=error_text,
            validation=validation,
        )
        return WorkerOutcome(
            job_id=job.job_id,
            status="failed",
            return_code=1,
            output=inference_output,
            error=error_text,
            validation=validation,
            failure_class=failure_class,
            retry_recommended=self._is_retryable_failure(failure_class),
        )

    def _run_command_tool(self, *, job: Job, workspace, command: str) -> tuple[int, str, str]:
        tool_action = ToolAction(
            job_id=job.job_id,
            tool=ToolName.RUN_COMMAND,
            arguments={"command": command},
        )
        typed_action = self._phase2_record_typed_action(job=job, action=tool_action)
        permission = self._permission_engine.evaluate(
            action=tool_action,
            allowed_tools_actions=job.allowed_tools_actions,
            metadata=job.metadata,
        )
        self._phase2_record_permission_decision(
            job=job,
            action=tool_action,
            decision_payload=permission.to_dict(),
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
            error = f"permission_denied:{permission.reason}"
            observation = ToolObservation(
                job_id=job.job_id,
                tool=ToolName.RUN_COMMAND,
                status=ToolStatus.BLOCKED,
                allowed=False,
                output="",
                error=error,
                return_code=126,
                metadata={"permission_reason": permission.reason},
            )
            self._phase2_record_blocked(
                job=job,
                typed_action=typed_action,
                reason=permission.reason or "permission_denied",
            )
            self.store.append_trace(
                {"kind": "tool_observation", "worker_id": self.worker_id, "job_id": job.job_id, "observation": observation.to_dict()}
            )
            return 126, "", error

        try:
            sandbox_result = self._sandbox_runner.run_command(
                command=command,
                cwd=workspace.worktree_target,
                env=self._build_env(job),
            )
            rc = sandbox_result.return_code
            command_output = sandbox_result.stdout.strip()
            error = sandbox_result.stderr.strip()
        except subprocess.TimeoutExpired:
            rc = 124
            command_output = ""
            error = "sandbox_timeout"

        observation = ToolObservation(
            job_id=job.job_id,
            tool=ToolName.RUN_COMMAND,
            status=ToolStatus.EXECUTED if rc == 0 else ToolStatus.FAILED,
            allowed=True,
            output=command_output[-4000:],
            error=error[-2000:],
            return_code=rc,
            metadata={"sandbox_mode": self._sandbox_runner.mode},
        )
        self._phase2_record_observation(
            job=job,
            typed_action=typed_action,
            status=ToolContractStatus.EXECUTED if rc == 0 else ToolContractStatus.FAILED,
            allowed=True,
            stdout=command_output[-4000:],
            stderr=error[-2000:],
            return_code=rc,
            side_effect_metadata={"sandbox_mode": self._sandbox_runner.mode, "cwd": str(workspace.worktree_target)},
        )
        self.store.append_trace(
            {"kind": "tool_observation", "worker_id": self.worker_id, "job_id": job.job_id, "observation": observation.to_dict()}
        )
        return rc, command_output, error

    def _apply_edit_tool(self, *, job: Job, workspace, repair: dict[str, Any]) -> tuple[bool, str]:
        target_path = str(repair.get("path") or "").strip()
        find_text = str(repair.get("find") or "")
        replace_text = str(repair.get("replace") or "")
        expected_before_sha = str(repair.get("expected_before_sha256") or "").strip()
        expected_after_sha = str(repair.get("expected_after_sha256") or "").strip()
        if not target_path:
            return False, "missing_repair_path"

        resolved = self._workspace_controller.resolve_in_repo(workspace, target_path)
        action = ToolAction(
            job_id=job.job_id,
            tool=ToolName.APPLY_EDIT,
            arguments={"path": str(resolved), "mode": "replace_text"},
        )
        typed_action = self._phase2_record_typed_action(job=job, action=action)
        decision = self._permission_engine.evaluate(
            action=action,
            allowed_tools_actions=job.allowed_tools_actions,
            metadata=job.metadata,
        )
        self._phase2_record_permission_decision(
            job=job,
            action=action,
            decision_payload=decision.to_dict(),
        )
        self.store.append_trace(
            {
                "kind": "tool_permission_decision",
                "worker_id": self.worker_id,
                "job_id": job.job_id,
                "tool_action": action.to_dict(),
                "permission": decision.to_dict(),
            }
        )
        if not decision.allowed:
            observation = ToolObservation(
                job_id=job.job_id,
                tool=ToolName.APPLY_EDIT,
                status=ToolStatus.BLOCKED,
                allowed=False,
                error=f"permission_denied:{decision.reason}",
                return_code=126,
                metadata={"permission_reason": decision.reason},
            )
            self._phase2_record_blocked(
                job=job,
                typed_action=typed_action,
                reason=decision.reason or "permission_denied",
            )
            self.store.append_trace(
                {"kind": "tool_observation", "worker_id": self.worker_id, "job_id": job.job_id, "observation": observation.to_dict()}
            )
            return False, "permission_denied"

        try:
            original = resolved.read_text(encoding="utf-8")
        except OSError as exc:
            return False, f"read_error:{exc}"
        original_sha = self._sha256_text(original)
        if expected_before_sha and expected_before_sha != original_sha:
            return False, "precondition_sha_mismatch"

        if find_text and find_text not in original:
            return False, "find_text_missing"

        updated = original.replace(find_text, replace_text, 1) if find_text else replace_text
        updated_sha = self._sha256_text(updated)
        if expected_after_sha and expected_after_sha != updated_sha:
            return False, "postcondition_sha_mismatch"
        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(updated, encoding="utf-8")
        except OSError as exc:
            return False, f"write_error:{exc}"

        observation = ToolObservation(
            job_id=job.job_id,
            tool=ToolName.APPLY_EDIT,
            status=ToolStatus.EXECUTED,
            allowed=True,
            output=f"edited:{resolved}",
            return_code=0,
            metadata={
                "path": str(resolved),
                "sha256_before": original_sha,
                "sha256_after": updated_sha,
            },
        )
        self._phase2_record_observation(
            job=job,
            typed_action=typed_action,
            status=ToolContractStatus.EXECUTED,
            allowed=True,
            stdout=f"edited:{resolved}",
            return_code=0,
            side_effect_metadata={
                "path": str(resolved),
                "sha256_before": original_sha,
                "sha256_after": updated_sha,
            },
        )
        self.store.append_trace(
            {"kind": "tool_observation", "worker_id": self.worker_id, "job_id": job.job_id, "observation": observation.to_dict()}
        )
        return True, ""

    def _apply_edit_batch_tool(self, *, job: Job, workspace, repairs: list[dict[str, Any]]) -> tuple[bool, str]:
        if not repairs:
            return False, "missing_repair_batch"

        preflight: list[dict[str, Any]] = []
        seen_paths: set[str] = set()
        for index, repair in enumerate(repairs, start=1):
            target_path = str(repair.get("path") or "").strip()
            find_text = str(repair.get("find") or "")
            replace_text = str(repair.get("replace") or "")
            expected_before_sha = str(repair.get("expected_before_sha256") or "").strip()
            expected_after_sha = str(repair.get("expected_after_sha256") or "").strip()
            if not target_path:
                return False, f"repair_{index}_missing_path"

            resolved = self._workspace_controller.resolve_in_repo(workspace, target_path)
            normalized = str(resolved)
            if normalized in seen_paths:
                self.store.append_trace(
                    {
                        "kind": "inner_loop_conflict",
                        "worker_id": self.worker_id,
                        "job_id": job.job_id,
                        "reason": "duplicate_edit_target",
                        "path": normalized,
                    }
                )
                return False, "conflict_duplicate_edit_target"
            seen_paths.add(normalized)

            action = ToolAction(
                job_id=job.job_id,
                tool=ToolName.APPLY_EDIT,
                arguments={"path": normalized, "mode": "replace_text"},
            )
            decision = self._permission_engine.evaluate(
                action=action,
                allowed_tools_actions=job.allowed_tools_actions,
                metadata=job.metadata,
            )
            self.store.append_trace(
                {
                    "kind": "tool_permission_decision",
                    "worker_id": self.worker_id,
                    "job_id": job.job_id,
                    "tool_action": action.to_dict(),
                    "permission": decision.to_dict(),
                }
            )
            if not decision.allowed:
                return False, f"permission_denied:{decision.reason}"

            try:
                original = resolved.read_text(encoding="utf-8")
            except OSError as exc:
                return False, f"repair_{index}_read_error:{exc}"

            original_sha = self._sha256_text(original)
            if expected_before_sha and expected_before_sha != original_sha:
                self.store.append_trace(
                    {
                        "kind": "inner_loop_conflict",
                        "worker_id": self.worker_id,
                        "job_id": job.job_id,
                        "reason": "precondition_sha_mismatch",
                        "path": normalized,
                        "expected": expected_before_sha,
                        "actual": original_sha,
                    }
                )
                return False, "precondition_sha_mismatch"
            if find_text and find_text not in original:
                return False, f"repair_{index}_find_text_missing"

            updated = original.replace(find_text, replace_text, 1) if find_text else replace_text
            updated_sha = self._sha256_text(updated)
            if expected_after_sha and expected_after_sha != updated_sha:
                self.store.append_trace(
                    {
                        "kind": "inner_loop_conflict",
                        "worker_id": self.worker_id,
                        "job_id": job.job_id,
                        "reason": "postcondition_sha_mismatch",
                        "path": normalized,
                        "expected": expected_after_sha,
                        "actual": updated_sha,
                    }
                )
                return False, "postcondition_sha_mismatch"

            preflight.append(
                {
                    "path": resolved,
                    "original": original,
                    "updated": updated,
                    "sha_before": original_sha,
                    "sha_after": updated_sha,
                }
            )

        written: list[Path] = []
        try:
            for row in preflight:
                path = row["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(row["updated"], encoding="utf-8")
                written.append(path)
        except OSError as exc:
            for row in preflight:
                if row["path"] in written:
                    try:
                        row["path"].write_text(row["original"], encoding="utf-8")
                    except OSError:
                        pass
            return False, f"batch_write_error:{exc}"

        observation = ToolObservation(
            job_id=job.job_id,
            tool=ToolName.APPLY_EDIT,
            status=ToolStatus.EXECUTED,
            allowed=True,
            output=f"edited_batch:{len(preflight)}",
            return_code=0,
            metadata={
                "paths": [str(row["path"]) for row in preflight],
                "sha256_before": {str(row["path"]): row["sha_before"] for row in preflight},
                "sha256_after": {str(row["path"]): row["sha_after"] for row in preflight},
            },
        )
        self.store.append_trace(
            {"kind": "tool_observation", "worker_id": self.worker_id, "job_id": job.job_id, "observation": observation.to_dict()}
        )
        return True, ""

    def _snapshot_paths(self, paths: list[Path]) -> dict[Path, str | None]:
        snapshot: dict[Path, str | None] = {}
        for path in paths:
            try:
                snapshot[path] = path.read_text(encoding="utf-8")
            except OSError:
                snapshot[path] = None
        return snapshot

    def _restore_snapshot(self, snapshot: dict[Path, str | None], *, reason: str, job: Job) -> None:
        if not snapshot:
            return
        restored = 0
        removed = 0
        for path, content in snapshot.items():
            try:
                if content is None:
                    if path.exists():
                        path.unlink()
                        removed += 1
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                restored += 1
            except OSError:
                continue
        self.store.append_trace(
            {
                "kind": "inner_loop_rollback",
                "worker_id": self.worker_id,
                "job_id": job.job_id,
                "reason": reason,
                "restored_files": restored,
                "removed_files": removed,
            }
        )

    @staticmethod
    def _sha256_text(payload: str) -> str:
        return sha256(payload.encode("utf-8")).hexdigest()

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

    def _snapshot_requested_outputs(self, paths: list[str]) -> dict[str, dict[str, Any]]:
        snapshot: dict[str, dict[str, Any]] = {}
        for raw in paths:
            candidate = str(raw).strip()
            if not candidate:
                continue
            path = Path(candidate)
            exists = path.exists()
            row: dict[str, Any] = {"exists": exists}
            if exists and path.is_file():
                try:
                    stat = path.stat()
                    row["mtime_ns"] = int(stat.st_mtime_ns)
                    row["size_bytes"] = int(stat.st_size)
                except OSError:
                    pass
            snapshot[candidate] = row
        return snapshot

    def _validate(
        self,
        *,
        job: Job,
        return_code: int,
        output_snapshot_before: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        passed = True
        output_snapshot_before = output_snapshot_before or {}
        output_snapshot_after = self._snapshot_requested_outputs(job.requested_outputs)
        for requirement in job.validation_requirements:
            req_ok = True
            detail = ""
            if requirement == ValidationRequirement.EXIT_CODE_ZERO:
                req_ok = return_code == 0
                detail = f"return_code={return_code}"
            elif requirement == ValidationRequirement.ARTIFACT_WRITTEN:
                missing_outputs = [
                    path
                    for path in job.requested_outputs
                    if not output_snapshot_after.get(str(path), {}).get("exists", False)
                ]
                req_ok = not missing_outputs
                detail = (
                    f"requested_outputs={len(job.requested_outputs)}; "
                    f"missing_outputs={len(missing_outputs)}"
                )
            elif requirement == ValidationRequirement.PYTHON_COMPILE:
                req_ok = self._python_compile_check(job.requested_outputs)
                detail = "python_compile"
            elif requirement == ValidationRequirement.SHELL_SYNTAX:
                req_ok = self._shell_syntax_check(job.requested_outputs)
                detail = "shell_syntax"
            checks.append({"requirement": requirement.value, "passed": req_ok, "detail": detail})
            if not req_ok:
                passed = False
        modified_outputs = 0
        for path, after in output_snapshot_after.items():
            before = output_snapshot_before.get(path, {})
            if not before.get("exists", False) and after.get("exists", False):
                modified_outputs += 1
                continue
            if before.get("exists", False) and after.get("exists", False):
                if before.get("mtime_ns") != after.get("mtime_ns") or before.get("size_bytes") != after.get("size_bytes"):
                    modified_outputs += 1
        return {
            "passed": passed,
            "checks": checks,
            "output_snapshot_before": output_snapshot_before,
            "output_snapshot_after": output_snapshot_after,
            "modified_requested_outputs": modified_outputs,
        }

    def _derive_failure_class(self, *, return_code: int, error: str, validation: dict[str, Any]) -> str:
        normalized_error = str(error or "").strip().lower()
        if normalized_error.startswith("permission_denied"):
            return "permission_denied"
        if normalized_error == "sandbox_timeout" or "sandbox_timeout" in normalized_error:
            return "sandbox_timeout"
        if normalized_error.startswith("inner_loop_missing_validate_command"):
            return "inner_loop_config_error"
        if normalized_error.startswith("inner_loop_setup_failed"):
            return "inner_loop_setup_failed"
        if "precondition_sha_mismatch" in normalized_error:
            return "inner_loop_precondition_mismatch"
        if "postcondition_sha_mismatch" in normalized_error:
            return "inner_loop_postcondition_mismatch"
        if "find_text_missing" in normalized_error:
            return "inner_loop_find_text_missing"
        if normalized_error.startswith("inner_loop_cycle_limit_reached"):
            return "inner_loop_cycle_limit"
        for row in validation.get("checks", []):
            if not isinstance(row, dict) or row.get("passed") is not False:
                continue
            requirement = str(row.get("requirement") or "")
            if requirement == ValidationRequirement.ARTIFACT_WRITTEN.value:
                return "missing_requested_outputs"
            if requirement == ValidationRequirement.PYTHON_COMPILE.value:
                return "python_compile_failure"
            if requirement == ValidationRequirement.SHELL_SYNTAX.value:
                return "shell_syntax_failure"
            if requirement == ValidationRequirement.EXIT_CODE_ZERO.value:
                return "nonzero_exit_code"
        if return_code == 126:
            return "permission_denied"
        if return_code == 124:
            return "sandbox_timeout"
        if return_code != 0:
            return "nonzero_exit_code"
        return "validation_failed"

    @staticmethod
    def _is_retryable_failure(failure_class: str) -> bool:
        if not failure_class:
            return False
        non_retryable = {
            "permission_denied",
            "inner_loop_config_error",
            "inner_loop_setup_failed",
            "inner_loop_precondition_mismatch",
            "inner_loop_postcondition_mismatch",
            "inner_loop_find_text_missing",
        }
        return failure_class not in non_retryable

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
