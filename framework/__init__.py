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
from .tool_bridge import SCHEMA_TOOL_NAMES, is_schema_action, tool_name_for
from .typed_permission_gate import PermissionRule, ToolPermission, TypedPermissionGate
from .gated_tool_dispatch import GatedDispatchError, gated_run_command, gated_run_tests
from .runtime_execution_adapter import (
    BoundedExecutionSummary,
    ExecutionStepResult,
    execute_typed_actions,
    extract_session_id,
    make_job_id,
)
from .apply_patch_dispatch import dispatch_apply_patch
from .search_loop_adapter import SearchLoopResult, SearchLoopAdapter
from .listdir_loop_adapter import DirEntry, DirListing, ListDirLoopAdapter
from .gitdiff_review_packager import DiffReviewRecord, GitDiffReviewPackager
from .loop_artifact_publisher import LoopArtifactRecord, LoopArtifactPublisher
from .search_cache_adapter import CachedSearchAdapter
from .pattern_guided_inspector import InspectHint, PatternGuidedInspector
from .loop_task_builder import TaskBuildContext, LoopTaskBuilder
from .routing_config_adopter import AdoptionRecommendation, RoutingAdoptionResult, RoutingConfigAdopter, save_adoption_result
from .critique_specializer import CritiqueSpecialization, CritiqueSpecializer
from .first_pass_metric import FirstPassStat, FirstPassReport, compute_first_pass_metrics, save_first_pass_report
from .evidence_accumulation_batch import BatchRunConfig, BatchKindResult, BatchRunResult, EvidenceAccumulationBatch
from .threshold_tuner import ThresholdRecommendation, ThresholdTuningResult, tune_thresholds, save_tuning_result
from .phase_closeout_ratifier import (
    CloseoutComponent,
    PhaseCloseoutArtifact,
    PHASE_COMPLETE,
    PHASE_PARTIAL,
    ratify_phase_closeout,
)
from .adapter_campaign_pre_authorizer import (
    PreAuthGate,
    PreAuthorizationArtifact,
    PRE_AUTH_DECISION_AUTHORIZED,
    PRE_AUTH_DECISION_DEFERRED,
    pre_authorize_adapter_campaign,
)
from .search_aware_inspect import SearchAwareInspectResult, SearchAwareInspectRunner
from .listdir_inspect_helper import TargetDiscoveryResult, ListDirInspectHelper
from .diff_result_packager import DiffResultPackage, DiffResultPackager
from .bounded_result_publisher import PublicationRecord, BoundedResultPublisher
from .loop_evidence_bundle import LoopEvidenceBundle, build_evidence_bundle, emit_evidence_bundle
from .result_artifact_manifest import ResultArtifactManifest, build_manifest, emit_manifest
from .hybrid_inspect_context import HybridInspectContext, build_hybrid_inspect_context
from .fused_prompt_context import FusedPromptContext, build_fused_prompt
from .bounded_critique_adopter import CritiqueAdoptionRecord, BoundedCritiqueAdopter
from .retry_telemetry_integration import (
    LoopRetryIntegrationRecord,
    LoopRetryStore,
    record_loop_attempt,
    record_loop_attempt_batch,
)
from .file_local_devloop import FileLocalTask, FileLocalResult, FileLocalDevloopRunner
from .devloop_benchmark import DevloopTask, DevloopBenchmarkResult, DevloopBenchmarkRunner, SYNTHETIC_TASK_FAMILY
from .session_job_adapters import make_session_adapter, make_job_adapter, session_to_context_dict
from .read_file_dispatch import dispatch_read_file
from .runtime_adoption_proof import make_bounded_context
from .context_retrieval import RetrievalQuery, RetrievedFile, RetrievalResult, retrieve_context, retrieve_file_content
from .validation_emit_adapter import emit_loop_validation
from .mvp_coding_loop import MVPTask, MVPLoopResult, MVPCodingLoopRunner, SAFE_TASK_KINDS
from .mvp_benchmark import MVPBenchmarkTaskSpec, MVPBenchmarkResult, MVPBenchmarkRunner, MVP_SYNTHETIC_TASKS
from .matrix_closure_evidence import MatrixItemState, MatrixItemRecord, derive_campaign_closure, emit_closeout_record
from .task_prompt_pack import SUPPORTED_TASK_CLASSES, PromptPack, get_prompt_pack, render_prompt
from .local_memory_store import FailurePattern, SuccessPattern, LocalMemoryStore, record_mvp_loop_outcome
from .critique_injector import CritiqueResult, build_critique, render_retry_prompt
from .task_router import RoutingDecision, route_task, route_with_memory_update
from .autonomy_evidence import TaskClassMetrics, AutonomyEvidenceResult, collect_autonomy_evidence
from .memory_compactor import MemoryCompactionResult, compact_memory
from .repo_pattern_store import PatternEntry, RepoPatternLibrary, build_repo_pattern_library, save_repo_pattern_library
from .retrieval_cache import CachedRetrievalResult, RetrievalCache
from .loop_retrieval_bridge import LoopContextBundle, LoopRetrievalBridge
from .routing_config import TaskRoutingOverride, RoutingConfig, DEFAULT_ROUTING_CONFIG, load_routing_config, save_routing_config
from .memory_critique_enricher import CritiqueEnrichment, enrich_critique, render_enriched_retry_prompt
from .readiness_evaluator import ReadinessCriterion, ReadinessEvaluation, evaluate_readiness
from .readiness_ratifier import RatificationDecision, RatificationArtifact, ratify
from .autonomy_metrics_extended import (
    TaskClassMetricsExtended,
    ExtendedAutonomyMetrics,
    collect_extended_metrics,
    save_extended_metrics,
)
from .task_repetition_harness import (
    RepetitionRunConfig,
    RepetitionRunRecord,
    RepetitionRunResult,
    TaskRepetitionHarness,
    make_synthetic_repetition_tasks,
)
from .search_action_dispatch import dispatch_search
from .list_dir_dispatch import dispatch_list_dir
from .git_diff_dispatch import dispatch_git_diff
from .publish_artifact_dispatch import dispatch_publish_artifact
from .retry_telemetry import RetryTelemetryRecord, record_retry_telemetry
from .retrieval_cache_warmer import CacheWarmingResult, warm_retrieval_cache
from .pattern_aging import PatternEvictionResult, evict_stale_patterns, persist_eviction
from .local_autonomy_dashboard import LocalAutonomyDashboard, build_local_autonomy_dashboard, emit_dashboard
from .aider_preflight import (
    AiderPreflightCheck,
    AiderPreflightResult,
    AiderPreflightChecker,
    emit_preflight_artifact,
)
from .task_class_readiness import (
    TaskClassVerdict,
    TaskClassReadinessReport,
    derive_task_class_readiness,
    emit_readiness_report,
)
from .tool_registry import DEFAULT_REGISTRY, ToolContractEntry, ToolRegistry
from .tool_schema import (
    ApplyPatchAction,
    ApplyPatchObservation,
    GitDiffAction,
    GitDiffObservation,
    ListDirAction,
    ListDirObservation,
    PublishArtifactAction,
    PublishArtifactObservation,
    ReadFileAction,
    ReadFileObservation,
    RepoMapAction,
    RepoMapObservation,
    RunCommandAction,
    RunCommandObservation,
    RunTestsAction,
    RunTestsObservation,
    SearchAction,
    SearchObservation,
)

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
    "ApplyPatchAction",
    "ApplyPatchObservation",
    "DEFAULT_REGISTRY",
    "GitDiffAction",
    "GitDiffObservation",
    "ListDirAction",
    "ListDirObservation",
    "PublishArtifactAction",
    "PublishArtifactObservation",
    "ReadFileAction",
    "ReadFileObservation",
    "RepoMapAction",
    "RepoMapObservation",
    "RunCommandAction",
    "RunCommandObservation",
    "RunTestsAction",
    "RunTestsObservation",
    "SCHEMA_TOOL_NAMES",
    "SearchAction",
    "SearchObservation",
    "ToolContractEntry",
    "ToolRegistry",
    "is_schema_action",
    "tool_name_for",
    "PermissionRule",
    "ToolPermission",
    "TypedPermissionGate",
    "GatedDispatchError",
    "gated_run_command",
    "gated_run_tests",
    "BoundedExecutionSummary",
    "ExecutionStepResult",
    "execute_typed_actions",
    "extract_session_id",
    "make_job_id",
    "dispatch_apply_patch",
    "FileLocalTask",
    "FileLocalResult",
    "FileLocalDevloopRunner",
    "DevloopTask",
    "DevloopBenchmarkResult",
    "DevloopBenchmarkRunner",
    "SYNTHETIC_TASK_FAMILY",
    "make_session_adapter",
    "make_job_adapter",
    "session_to_context_dict",
    "dispatch_read_file",
    "make_bounded_context",
    "RetrievalQuery",
    "RetrievedFile",
    "RetrievalResult",
    "retrieve_context",
    "retrieve_file_content",
    "emit_loop_validation",
    "MVPTask",
    "MVPLoopResult",
    "MVPCodingLoopRunner",
    "SAFE_TASK_KINDS",
    "MVPBenchmarkTaskSpec",
    "MVPBenchmarkResult",
    "MVPBenchmarkRunner",
    "MVP_SYNTHETIC_TASKS",
    "MatrixItemState",
    "MatrixItemRecord",
    "derive_campaign_closure",
    "emit_closeout_record",
    "SUPPORTED_TASK_CLASSES",
    "PromptPack",
    "get_prompt_pack",
    "render_prompt",
    "FailurePattern",
    "SuccessPattern",
    "LocalMemoryStore",
    "record_mvp_loop_outcome",
    "CritiqueResult",
    "build_critique",
    "render_retry_prompt",
    "RoutingDecision",
    "route_task",
    "route_with_memory_update",
    "TaskClassMetrics",
    "AutonomyEvidenceResult",
    "collect_autonomy_evidence",
    "MemoryCompactionResult",
    "compact_memory",
    "PatternEntry",
    "RepoPatternLibrary",
    "build_repo_pattern_library",
    "save_repo_pattern_library",
    "CachedRetrievalResult",
    "RetrievalCache",
    "LoopContextBundle",
    "LoopRetrievalBridge",
    "RepetitionRunConfig",
    "RepetitionRunRecord",
    "RepetitionRunResult",
    "TaskRepetitionHarness",
    "make_synthetic_repetition_tasks",
    "TaskClassMetricsExtended",
    "ExtendedAutonomyMetrics",
    "collect_extended_metrics",
    "save_extended_metrics",
    "TaskRoutingOverride",
    "RoutingConfig",
    "DEFAULT_ROUTING_CONFIG",
    "load_routing_config",
    "save_routing_config",
    "CritiqueEnrichment",
    "enrich_critique",
    "render_enriched_retry_prompt",
    "ReadinessCriterion",
    "ReadinessEvaluation",
    "evaluate_readiness",
    "RatificationDecision",
    "RatificationArtifact",
    "ratify",
    "dispatch_search",
    "dispatch_list_dir",
    "dispatch_git_diff",
    "dispatch_publish_artifact",
    "RetryTelemetryRecord",
    "record_retry_telemetry",
    "CacheWarmingResult",
    "warm_retrieval_cache",
    "PatternEvictionResult",
    "evict_stale_patterns",
    "persist_eviction",
    "TaskClassVerdict",
    "TaskClassReadinessReport",
    "derive_task_class_readiness",
    "emit_readiness_report",
    "AiderPreflightCheck",
    "AiderPreflightResult",
    "AiderPreflightChecker",
    "emit_preflight_artifact",
    "LocalAutonomyDashboard",
    "build_local_autonomy_dashboard",
    "emit_dashboard",
    "SearchLoopResult",
    "SearchLoopAdapter",
    "DirEntry",
    "DirListing",
    "ListDirLoopAdapter",
    "DiffReviewRecord",
    "GitDiffReviewPackager",
    "LoopArtifactRecord",
    "LoopArtifactPublisher",
    "LoopRetryIntegrationRecord",
    "LoopRetryStore",
    "record_loop_attempt",
    "record_loop_attempt_batch",
    "CachedSearchAdapter",
    "InspectHint",
    "PatternGuidedInspector",
    "TaskBuildContext",
    "LoopTaskBuilder",
    "AdoptionRecommendation",
    "RoutingAdoptionResult",
    "RoutingConfigAdopter",
    "save_adoption_result",
    "CritiqueSpecialization",
    "CritiqueSpecializer",
    "FirstPassStat",
    "FirstPassReport",
    "compute_first_pass_metrics",
    "save_first_pass_report",
    "BatchRunConfig",
    "BatchKindResult",
    "BatchRunResult",
    "EvidenceAccumulationBatch",
    "ThresholdRecommendation",
    "ThresholdTuningResult",
    "tune_thresholds",
    "save_tuning_result",
    "PreAuthGate",
    "PreAuthorizationArtifact",
    "PRE_AUTH_DECISION_AUTHORIZED",
    "PRE_AUTH_DECISION_DEFERRED",
    "pre_authorize_adapter_campaign",
    "CloseoutComponent",
    "PhaseCloseoutArtifact",
    "PHASE_COMPLETE",
    "PHASE_PARTIAL",
    "ratify_phase_closeout",
    "SearchAwareInspectResult",
    "SearchAwareInspectRunner",
    "TargetDiscoveryResult",
    "ListDirInspectHelper",
    "DiffResultPackage",
    "DiffResultPackager",
    "PublicationRecord",
    "BoundedResultPublisher",
    "LoopEvidenceBundle",
    "build_evidence_bundle",
    "emit_evidence_bundle",
    "ResultArtifactManifest",
    "build_manifest",
    "emit_manifest",
    "HybridInspectContext",
    "build_hybrid_inspect_context",
    "FusedPromptContext",
    "build_fused_prompt",
    "CritiqueAdoptionRecord",
    "BoundedCritiqueAdopter",
]
