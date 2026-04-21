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
from .bounded_retry_controller import RetryDecisionRecord, BoundedRetryController
from .unified_local_metrics import UnifiedLocalMetrics, compute_unified_metrics, emit_unified_metrics
from .task_class_benchmark import TaskClassBenchmarkEntry, TaskClassBenchmarkReport, TaskClassBenchmarkRunner
from .local_quality_score import LocalQualityScore, compute_quality_score, emit_quality_score
from .threshold_suggester import ThresholdSuggestion, ThresholdSuggestions, derive_threshold_suggestions, emit_threshold_suggestions
from .routing_policy_artifact import RoutingPolicyArtifact, build_routing_policy_artifact, emit_routing_policy
from .evidence_backed_task_expander import (
    EXPANSION_CANDIDATES, TaskExpansionDecision, TaskExpansionRecord,
    EvidenceBackedTaskExpander, emit_expansion_record,
)
from .failure_cluster_analysis import FailureCluster, FailureClusterReport, FailureClusterAnalyzer, emit_failure_clusters
from .adapter_readiness_stress import StressCheck, StressHarnessResult, AdapterReadinessStressHarness, emit_stress_result
from .controlled_adapter_scaffold import ScaffoldGate, AdapterScaffoldPlan, ControlledAdapterScaffold, emit_scaffold_plan
from .terminal_autonomy_ratifier import RatificationCriterion, TerminalRatificationRecord, TerminalAutonomyRatifier, emit_terminal_ratification
from .aider_promotion_reratifier import AiderPromotionDecision, AiderPromotionReratifier, emit_aider_promotion_decision
from .terminal_promotion_reratifier import TerminalPromotionDecision, TerminalPromotionReratifier, emit_terminal_promotion_decision
from .aider_runtime_adapter import AiderRuntimeAdapter, _EXPERIMENTAL_FLAG
from .cmdb_authority_pilot import CmdbAuthorityRecord, CmdbAuthorityPilot, read_cmdb_authority
from .cmdb_authority_boundary import AuthorityDomain, PROMOTION_AUTHORITY, RUNTIME_AUTHORITY, CMDB_AUTHORITY, ALL_AUTHORITIES, validate_boundary_non_overlap, emit_authority_boundary
from .cmdb_authority_contract import CmdbServiceRecord, CmdbOwnershipBoundary, CmdbAuthorityContract, build_cmdb_authority_contract, emit_cmdb_authority_contract
from .cmdb_read_model import CmdbReadModelEntry, CmdbReadModelOutput, CmdbReadModel, emit_cmdb_read_model
from .cmdb_authority_proof_harness import CmdbProofCriterion, CmdbProofResult, CmdbAuthorityProofHarness, emit_cmdb_proof_result
from .cmdb_operating_context import SubsystemEntry, HostSlot, CmdbOperatingContext, build_local_operating_context, emit_cmdb_operating_context
from .cmdb_authoritative_promotion_ratifier import CmdbRatificationCriterion, CmdbAuthoritativePromotionDecision, CmdbAuthoritativePromotionRatifier, emit_cmdb_authoritative_promotion_decision
from .cmdb_terminal_authoritative_reratifier import CmdbTerminalDecision, CmdbTerminalAuthoritativeReratifier, emit_cmdb_terminal_decision
from .cmdb_integration_gate import CmdbGateDecision, CmdbIntegrationGate, evaluate_cmdb_gate, GATE_PASS, GATE_BLOCK
from .domain_branch_contract import DOMAIN_BRANCH_RUNNER_VERSION, DomainBranchPolicy, DomainBranchManifest, DomainBranchRunner
from .expansion_closeout_ratifier import (
    EXPANSION_COMPLETE,
    EXPANSION_PARTIAL,
    ExpansionCloseoutComponent,
    ExpansionCloseoutArtifact,
    ratify_expansion_closeout,
)
from .domain_branch_second_wave import (
    ATHLETE_ANALYTICS_POLICY,
    OFFICE_AUTOMATION_POLICY,
    SECOND_WAVE_MANIFEST,
    SecondWaveDomainRunner,
)
from .domain_branch_first_wave import (
    MEDIA_CONTROL_POLICY,
    MEDIA_LAB_POLICY,
    MEETING_INTELLIGENCE_POLICY,
    FIRST_WAVE_MANIFEST,
    FirstWaveDomainRunner,
)
from .codex_defer_adapter import (
    CODEX_AVAILABLE,
    CODEX_DECISION_AVAILABLE,
    CODEX_DECISION_DEFERRED,
    CodexDeferArtifact,
    emit_codex_defer,
)
from .codex_adapter_contract import (
    CodexAdapterPolicy,
    CodexAdapterConfig,
    CodexAdapterRequest,
    CodexAdapterArtifact,
    CODEX_DEFER_REASON,
    DEFAULT_CODEX_POLICY,
)
from .aider_adapter_evidence import (
    AIDER_STATUS_DONE,
    AIDER_STATUS_PARTIAL,
    AIDER_STATUS_DEFERRED,
    AiderAdapterEvidenceRecord,
    AiderAdapterEvidenceReport,
    gather_aider_evidence,
)
from .aider_adapter_contract import (
    AiderAdapterPolicy,
    AiderAdapterConfig,
    AiderAdapterRequest,
    AiderAdapterArtifact,
    DEFAULT_AIDER_POLICY,
)
from .expansion_readiness_inspector import (
    ExpansionReadinessItem,
    ExpansionReadinessReport,
    READINESS_EXPANSION_READY,
    READINESS_EXPANSION_PARTIAL,
    READINESS_EXPANSION_BLOCKED,
    inspect_expansion_readiness,
)
from .promotion_baseline_inspector import (
    BLOCKER_CLASS_HARD,
    BLOCKER_CLASS_SOFT,
    BLOCKER_CLASS_NONE,
    CURRENT_STATE_PARTIAL,
    CURRENT_STATE_DEFERRED,
    CURRENT_STATE_SEED_COMPLETE,
    CURRENT_STATE_DONE,
    PromotionCandidate,
    PromotionBaselineReport,
    inspect_promotion_baseline,
)
from .aider_live_execution_gate import (
    LIVE_GATE_PASS,
    LIVE_GATE_BLOCK,
    AiderLiveGateCheck,
    AiderLiveGateReport,
    evaluate_aider_live_gate,
)
from .aider_live_proof import (
    PROOF_STATUS_LIVE_PROVEN,
    PROOF_STATUS_DRY_RUN_ONLY,
    PROOF_STATUS_BLOCKED,
    AiderLiveProofRecord,
    AiderLiveProofReport,
    run_aider_live_proof,
)
from .aider_promotion_ratifier import (
    AIDER_PROMOTION_DONE,
    AIDER_PROMOTION_PARTIAL,
    AiderPromotionArtifact,
    ratify_aider_promotion,
)
from .codex_availability_gate import (
    CODEX_GATE_PASS,
    CODEX_GATE_BLOCK,
    CodexAvailabilityCheck,
    CodexAvailabilityReport,
    evaluate_codex_availability,
)
from .codex_promotion_ratifier import (
    CODEX_PROMOTION_DONE,
    CODEX_LONG_TERM_DEFERRED,
    CodexPromotionArtifact,
    ratify_codex_promotion,
)
from .cmdb_promotion_evidence import (
    CMDB_PROOF_SUFFICIENT,
    CMDB_PROOF_INSUFFICIENT,
    CMDB_PROOF_CRITERIA,
    CmdbProofCriterionResult,
    CmdbEvidenceReport,
    evaluate_cmdb_promotion_evidence,
)
from .cmdb_promotion_ratifier import (
    CMDB_PROMOTION_DONE,
    CMDB_PROMOTION_DEFERRED,
    CmdbPromotionArtifact,
    ratify_cmdb_promotion,
)
from .domain_branch_proof_harness import (
    BRANCH_VERDICT_DONE,
    BRANCH_VERDICT_SCAFFOLD_COMPLETE_PRODUCT_DEFERRED,
    BRANCH_VERDICT_BLOCKED,
    BRANCH_PROOF_CRITERIA,
    BranchProofCriterionResult,
    BranchProofResult,
    DomainBranchProofHarness,
)
from .domain_branch_first_wave_ratifier import (
    FirstWavePromotionRecord,
    FirstWavePromotionArtifact,
    ratify_first_wave_promotion,
)
from .domain_branch_second_wave_ratifier import (
    SecondWavePromotionRecord,
    SecondWavePromotionArtifact,
    ratify_second_wave_promotion,
)
from .terminal_promotion_ratifier import (
    TERMINAL_PROMOTION_COMPLETE,
    TERMINAL_PROMOTION_PARTIAL,
    TerminalPromotionRecord,
    TerminalPromotionArtifact,
    ratify_terminal_promotion,
)
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
from .aider_preflight_blocker_inspector import (
    BLOCKER_PERMISSION_GATE,
    BLOCKER_CONFIG_KEYS,
    PreflightBlockerRecord,
    PreflightBlockerArtifact,
    inspect_preflight_blockers,
)
from .aider_permission_gate_provider import (
    BOUNDED_AIDER_TOOL_PERMISSION,
    BOUNDED_AIDER_GATE,
    make_wired_preflight_checker,
    check_permission_gate_active,
)
from .aider_config_provider import (
    BOUNDED_AIDER_CONFIG,
    make_fully_wired_preflight_checker,
    check_config_keys_present,
    check_all_blocking_checks_pass,
)
from .aider_live_gate_wired import (
    evaluate_wired_aider_gate,
    run_wired_aider_proof,
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
    "BLOCKER_PERMISSION_GATE",
    "BLOCKER_CONFIG_KEYS",
    "PreflightBlockerRecord",
    "PreflightBlockerArtifact",
    "inspect_preflight_blockers",
    "BOUNDED_AIDER_TOOL_PERMISSION",
    "BOUNDED_AIDER_GATE",
    "make_wired_preflight_checker",
    "check_permission_gate_active",
    "BOUNDED_AIDER_CONFIG",
    "make_fully_wired_preflight_checker",
    "check_config_keys_present",
    "check_all_blocking_checks_pass",
    "evaluate_wired_aider_gate",
    "run_wired_aider_proof",
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
    "RetryDecisionRecord",
    "BoundedRetryController",
    "UnifiedLocalMetrics",
    "compute_unified_metrics",
    "emit_unified_metrics",
    "TaskClassBenchmarkEntry",
    "TaskClassBenchmarkReport",
    "TaskClassBenchmarkRunner",
    "LocalQualityScore",
    "compute_quality_score",
    "emit_quality_score",
    "ThresholdSuggestion",
    "ThresholdSuggestions",
    "derive_threshold_suggestions",
    "emit_threshold_suggestions",
    "RoutingPolicyArtifact",
    "build_routing_policy_artifact",
    "emit_routing_policy",
    "EXPANSION_CANDIDATES",
    "TaskExpansionDecision",
    "TaskExpansionRecord",
    "EvidenceBackedTaskExpander",
    "emit_expansion_record",
    "FailureCluster",
    "FailureClusterReport",
    "FailureClusterAnalyzer",
    "emit_failure_clusters",
    "StressCheck",
    "StressHarnessResult",
    "AdapterReadinessStressHarness",
    "emit_stress_result",
    "ScaffoldGate",
    "AdapterScaffoldPlan",
    "ControlledAdapterScaffold",
    "emit_scaffold_plan",
    "RatificationCriterion",
    "TerminalRatificationRecord",
    "TerminalAutonomyRatifier",
    "emit_terminal_ratification",
    "AiderPromotionDecision",
    "AiderPromotionReratifier",
    "emit_aider_promotion_decision",
    "TerminalPromotionDecision",
    "TerminalPromotionReratifier",
    "emit_terminal_promotion_decision",
    "AuthorityDomain",
    "PROMOTION_AUTHORITY",
    "RUNTIME_AUTHORITY",
    "CMDB_AUTHORITY",
    "ALL_AUTHORITIES",
    "validate_boundary_non_overlap",
    "emit_authority_boundary",
    "CmdbServiceRecord",
    "CmdbOwnershipBoundary",
    "CmdbAuthorityContract",
    "build_cmdb_authority_contract",
    "emit_cmdb_authority_contract",
    "CmdbReadModelEntry",
    "CmdbReadModelOutput",
    "CmdbReadModel",
    "emit_cmdb_read_model",
    "CmdbProofCriterion",
    "CmdbProofResult",
    "CmdbAuthorityProofHarness",
    "emit_cmdb_proof_result",
    "SubsystemEntry",
    "HostSlot",
    "CmdbOperatingContext",
    "build_local_operating_context",
    "emit_cmdb_operating_context",
    "CmdbRatificationCriterion",
    "CmdbAuthoritativePromotionDecision",
    "CmdbAuthoritativePromotionRatifier",
    "emit_cmdb_authoritative_promotion_decision",
    "CmdbTerminalDecision",
    "CmdbTerminalAuthoritativeReratifier",
    "emit_cmdb_terminal_decision",
    "ExpansionReadinessItem",
    "ExpansionReadinessReport",
    "READINESS_EXPANSION_READY",
    "READINESS_EXPANSION_PARTIAL",
    "READINESS_EXPANSION_BLOCKED",
    "inspect_expansion_readiness",
    "AiderAdapterPolicy",
    "AiderAdapterConfig",
    "AiderAdapterRequest",
    "AiderAdapterArtifact",
    "DEFAULT_AIDER_POLICY",
    "AiderRuntimeAdapter",
    "AIDER_STATUS_DONE",
    "AIDER_STATUS_PARTIAL",
    "AIDER_STATUS_DEFERRED",
    "AiderAdapterEvidenceRecord",
    "AiderAdapterEvidenceReport",
    "gather_aider_evidence",
    "CodexAdapterPolicy",
    "CodexAdapterConfig",
    "CodexAdapterRequest",
    "CodexAdapterArtifact",
    "CODEX_DEFER_REASON",
    "DEFAULT_CODEX_POLICY",
    "CODEX_AVAILABLE",
    "CODEX_DECISION_AVAILABLE",
    "CODEX_DECISION_DEFERRED",
    "CodexDeferArtifact",
    "emit_codex_defer",
    "CmdbAuthorityRecord",
    "CmdbAuthorityPilot",
    "read_cmdb_authority",
    "CmdbGateDecision",
    "CmdbIntegrationGate",
    "evaluate_cmdb_gate",
    "GATE_PASS",
    "GATE_BLOCK",
    "DOMAIN_BRANCH_RUNNER_VERSION",
    "DomainBranchPolicy",
    "DomainBranchManifest",
    "DomainBranchRunner",
    "MEDIA_CONTROL_POLICY",
    "MEDIA_LAB_POLICY",
    "MEETING_INTELLIGENCE_POLICY",
    "FIRST_WAVE_MANIFEST",
    "FirstWaveDomainRunner",
    "ATHLETE_ANALYTICS_POLICY",
    "OFFICE_AUTOMATION_POLICY",
    "SECOND_WAVE_MANIFEST",
    "SecondWaveDomainRunner",
    "EXPANSION_COMPLETE",
    "EXPANSION_PARTIAL",
    "ExpansionCloseoutComponent",
    "ExpansionCloseoutArtifact",
    "ratify_expansion_closeout",
    "BLOCKER_CLASS_HARD",
    "BLOCKER_CLASS_SOFT",
    "BLOCKER_CLASS_NONE",
    "CURRENT_STATE_PARTIAL",
    "CURRENT_STATE_DEFERRED",
    "CURRENT_STATE_SEED_COMPLETE",
    "CURRENT_STATE_DONE",
    "PromotionCandidate",
    "PromotionBaselineReport",
    "inspect_promotion_baseline",
    "LIVE_GATE_PASS",
    "LIVE_GATE_BLOCK",
    "AiderLiveGateCheck",
    "AiderLiveGateReport",
    "evaluate_aider_live_gate",
    "PROOF_STATUS_LIVE_PROVEN",
    "PROOF_STATUS_DRY_RUN_ONLY",
    "PROOF_STATUS_BLOCKED",
    "AiderLiveProofRecord",
    "AiderLiveProofReport",
    "run_aider_live_proof",
    "AIDER_PROMOTION_DONE",
    "AIDER_PROMOTION_PARTIAL",
    "AiderPromotionArtifact",
    "ratify_aider_promotion",
    "CODEX_GATE_PASS",
    "CODEX_GATE_BLOCK",
    "CodexAvailabilityCheck",
    "CodexAvailabilityReport",
    "evaluate_codex_availability",
    "CODEX_PROMOTION_DONE",
    "CODEX_LONG_TERM_DEFERRED",
    "CodexPromotionArtifact",
    "ratify_codex_promotion",
    "CMDB_PROOF_SUFFICIENT",
    "CMDB_PROOF_INSUFFICIENT",
    "CMDB_PROOF_CRITERIA",
    "CmdbProofCriterionResult",
    "CmdbEvidenceReport",
    "evaluate_cmdb_promotion_evidence",
    "CMDB_PROMOTION_DONE",
    "CMDB_PROMOTION_DEFERRED",
    "CmdbPromotionArtifact",
    "ratify_cmdb_promotion",
    "BRANCH_VERDICT_DONE",
    "BRANCH_VERDICT_SCAFFOLD_COMPLETE_PRODUCT_DEFERRED",
    "BRANCH_VERDICT_BLOCKED",
    "BRANCH_PROOF_CRITERIA",
    "BranchProofCriterionResult",
    "BranchProofResult",
    "DomainBranchProofHarness",
    "FirstWavePromotionRecord",
    "FirstWavePromotionArtifact",
    "ratify_first_wave_promotion",
    "SecondWavePromotionRecord",
    "SecondWavePromotionArtifact",
    "ratify_second_wave_promotion",
    "TERMINAL_PROMOTION_COMPLETE",
    "TERMINAL_PROMOTION_PARTIAL",
    "TerminalPromotionRecord",
    "TerminalPromotionArtifact",
    "ratify_terminal_promotion",
]
