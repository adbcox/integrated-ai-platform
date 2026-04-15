"""Parallel local-first execution framework foundation.

This package introduces a scheduler + queue, worker runtime, inference abstraction,
artifact/state persistence, and learning hooks for bounded local execution.
"""

from .backend_profiles import BackendProfile, get_backend_profile, select_backend_profile_auto
from .inference_adapter import InferenceAdapter, InferenceRequest, InferenceResponse, build_inference_adapter
from .job_schema import (
    EscalationPolicy,
    Job,
    JobAction,
    JobClass,
    JobLifecycle,
    JobPriority,
    LearningHooksConfig,
    RetryPolicy,
    ValidationRequirement,
    WorkTarget,
)
from .learning_hooks import LearningEvent, LearningHooks
from .permission_engine import PermissionDecision, PermissionEngine
from .queue_types import QueueEnvelope
from .sandbox import LocalSandboxRunner, SandboxResult
from .scheduler import Scheduler
from .state_store import StateStore
from .tool_system import ToolAction, ToolName, ToolObservation, ToolStatus
from .workspace import WorkspaceContext, WorkspaceController
from .worker_runtime import WorkerPool, WorkerRuntime

__all__ = [
    "BackendProfile",
    "EscalationPolicy",
    "InferenceAdapter",
    "InferenceRequest",
    "InferenceResponse",
    "Job",
    "JobAction",
    "JobClass",
    "JobLifecycle",
    "JobPriority",
    "LearningEvent",
    "LearningHooksConfig",
    "LearningHooks",
    "LocalSandboxRunner",
    "PermissionDecision",
    "PermissionEngine",
    "QueueEnvelope",
    "RetryPolicy",
    "SandboxResult",
    "Scheduler",
    "StateStore",
    "ToolAction",
    "ToolName",
    "ToolObservation",
    "ToolStatus",
    "ValidationRequirement",
    "WorkTarget",
    "WorkspaceContext",
    "WorkspaceController",
    "WorkerPool",
    "WorkerRuntime",
    "build_inference_adapter",
    "get_backend_profile",
    "select_backend_profile_auto",
]
