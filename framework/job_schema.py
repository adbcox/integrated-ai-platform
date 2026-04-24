"""Structured job model for framework scheduling and execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .compat import StrEnum, UTC


class JobClass(StrEnum):
    CODING_TASK = "coding_task"
    MULTI_FILE_ORCHESTRATION = "multi_file_orchestration"
    RETRIEVAL_ORCHESTRATION = "retrieval_orchestration"
    RESUMABLE_CHECKPOINTED = "resumable_checkpointed"
    SAFE_CONTRACTS = "safe_contracts"
    BOUNDED_ARCHITECTURE = "bounded_architecture"
    FRAMEWORK_BOOTSTRAP = "framework_bootstrap"
    LEARNING_ARTIFACT_SYNTHESIS = "learning_artifact_synthesis"
    BENCHMARK_ANALYSIS = "benchmark_analysis"
    CAMPAIGN_ARTIFACT_PROCESSING = "campaign_artifact_processing"
    VALIDATION_CHECK_EXECUTION = "validation_check_execution"
    TRUSTED_PATTERN_REFRESH = "trusted_pattern_refresh"
    REPLAY_QUEUE_GENERATION = "replay_queue_generation"
    REPLAY_QUEUE_EXECUTION = "replay_queue_execution"


class JobPriority(StrEnum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class JobLifecycle(StrEnum):
    ACCEPTED = "accepted"
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    RETRY_WAITING = "retry_waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"
    CANCELED = "canceled"


class JobAction(StrEnum):
    SHELL_COMMAND = "shell_command"
    INFERENCE_ONLY = "inference_only"
    INFERENCE_AND_SHELL = "inference_and_shell"


class ValidationRequirement(StrEnum):
    NONE = "none"
    EXIT_CODE_ZERO = "exit_code_zero"
    ARTIFACT_WRITTEN = "artifact_written"
    PYTHON_COMPILE = "python_compile"
    SHELL_SYNTAX = "shell_syntax"


@dataclass(frozen=True)
class RetryPolicy:
    retry_budget: int = 0
    retry_backoff_seconds: int = 0


@dataclass(frozen=True)
class EscalationPolicy:
    allow_auto_escalation: bool = False
    escalate_on_retry_exhaustion: bool = True
    escalation_label: str = "manual_review"


@dataclass(frozen=True)
class WorkTarget:
    repo_root: str
    worktree_target: str


@dataclass(frozen=True)
class LearningHooksConfig:
    emit_lessons: bool = True
    emit_prevention_candidates: bool = True
    emit_reuse_candidates: bool = True
    task_class_priors: list[str] = field(default_factory=list)


@dataclass
class Job:
    task_class: JobClass
    priority: JobPriority
    target: WorkTarget
    action: JobAction
    requested_outputs: list[str]
    allowed_tools_actions: list[str]
    artifact_inputs: list[str] = field(default_factory=list)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    escalation_policy: EscalationPolicy = field(default_factory=EscalationPolicy)
    validation_requirements: list[ValidationRequirement] = field(default_factory=list)
    learning_hooks: LearningHooksConfig = field(default_factory=LearningHooksConfig)
    metadata: dict[str, Any] = field(default_factory=dict)
    job_id: str = field(default_factory=lambda: f"job-{uuid4().hex[:12]}")
    lifecycle: JobLifecycle = JobLifecycle.ACCEPTED
    status_reason: str = ""
    created_at_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds"))
    task_category: str = ""  # New field
    complexity_estimate: int = 5  # New field
    pattern_type: str = ""  # New field
    updated_at_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds"))
    attempts_used: int = 0
    execution_context_id: str = ""

    def set_lifecycle(self, lifecycle: JobLifecycle, *, reason: str = "") -> None:
        self.lifecycle = lifecycle
        self.status_reason = reason
        self.updated_at_utc = datetime.now(UTC).isoformat(timespec="seconds")

    @property
    def repo_root_path(self) -> Path:
        return Path(self.target.repo_root).resolve()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["task_class"] = self.task_class.value
        payload["priority"] = self.priority.value
        payload["lifecycle"] = self.lifecycle.value
        payload["action"] = self.action.value
        payload["validation_requirements"] = [item.value for item in self.validation_requirements]
        return payload


def parse_job(payload: dict[str, Any]) -> Job:
    """Rehydrate a persisted job payload into a `Job` instance."""

    target_raw = payload.get("target") if isinstance(payload.get("target"), dict) else {}
    retry_raw = payload.get("retry_policy") if isinstance(payload.get("retry_policy"), dict) else {}
    escalation_raw = payload.get("escalation_policy") if isinstance(payload.get("escalation_policy"), dict) else {}
    learning_raw = payload.get("learning_hooks") if isinstance(payload.get("learning_hooks"), dict) else {}
    raw_validation = payload.get("validation_requirements") if isinstance(payload.get("validation_requirements"), list) else []

    job = Job(
        task_class=JobClass(str(payload.get("task_class", JobClass.BOUNDED_ARCHITECTURE.value))),
        priority=JobPriority(str(payload.get("priority", JobPriority.P2.value))),
        target=WorkTarget(
            repo_root=str(target_raw.get("repo_root") or "."),
            worktree_target=str(target_raw.get("worktree_target") or "."),
        ),
        action=JobAction(str(payload.get("action", JobAction.SHELL_COMMAND.value))),
        requested_outputs=[str(item) for item in (payload.get("requested_outputs") or [])],
        allowed_tools_actions=[str(item) for item in (payload.get("allowed_tools_actions") or [])],
        artifact_inputs=[str(item) for item in (payload.get("artifact_inputs") or [])],
        retry_policy=RetryPolicy(
            retry_budget=int(retry_raw.get("retry_budget") or 0),
            retry_backoff_seconds=int(retry_raw.get("retry_backoff_seconds") or 0),
        ),
        escalation_policy=EscalationPolicy(
            allow_auto_escalation=bool(escalation_raw.get("allow_auto_escalation")),
            escalate_on_retry_exhaustion=bool(escalation_raw.get("escalate_on_retry_exhaustion", True)),
            escalation_label=str(escalation_raw.get("escalation_label") or "manual_review"),
        ),
        validation_requirements=[ValidationRequirement(str(item)) for item in raw_validation],
        learning_hooks=LearningHooksConfig(
            emit_lessons=bool(learning_raw.get("emit_lessons", True)),
            emit_prevention_candidates=bool(learning_raw.get("emit_prevention_candidates", True)),
            emit_reuse_candidates=bool(learning_raw.get("emit_reuse_candidates", True)),
            task_class_priors=[str(item) for item in (learning_raw.get("task_class_priors") or [])],
        ),
        metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        job_id=str(payload.get("job_id") or f"job-{uuid4().hex[:12]}"),
    )

    job.lifecycle = JobLifecycle(str(payload.get("lifecycle") or JobLifecycle.ACCEPTED.value))
    job.status_reason = str(payload.get("status_reason") or "")
    job.created_at_utc = str(payload.get("created_at_utc") or job.created_at_utc)
    job.updated_at_utc = str(payload.get("updated_at_utc") or job.updated_at_utc)
    job.attempts_used = int(payload.get("attempts_used") or 0)
    job.execution_context_id = str(payload.get("execution_context_id") or "")
    return job
