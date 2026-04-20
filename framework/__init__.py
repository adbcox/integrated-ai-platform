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
from .local_command_runner import KNOWN_FRAMEWORK_COMMANDS, LocalCommandResult, LocalCommandRunner
from .runtime_artifact_service import RuntimeArtifactService
from .runtime_workspace_contract import RuntimeWorkspace, assert_read_only_source, build_workspace
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
    "KNOWN_FRAMEWORK_COMMANDS",
    "LocalCommandResult",
    "LocalCommandRunner",
    "RuntimeArtifactService",
    "RuntimeWorkspace",
    "assert_read_only_source",
    "build_inference_adapter",
    "build_workspace",
    "get_backend_profile",
    "select_backend_profile_auto",
]
