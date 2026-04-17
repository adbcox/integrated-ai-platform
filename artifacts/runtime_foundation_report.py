from framework.schema_registry import SCHEMA_REGISTRY
from framework.runtime_contract_catalog import RuntimeContractCatalog

def generate_runtime_foundation_report() -> dict[str, object]:
    catalog = RuntimeContractCatalog(
        session_contracts=["ExecutionSession", "SessionAuditPlan", "SessionAuditResult", "SessionAuditSummary", "SessionPromptPlan", "SessionPromptResult", "SessionRouteRecord", "SessionWindowAudit", "SessionWindowPlan", "SessionWindowResult"],
        execution_contracts=["CompletionRecord", "ExecutionAttempt", "ExecutionAuditTrail", "ExecutionCheckpoint", "ExecutionCompletionSummary", "ExecutionDecision", "ExecutionEnvelope", "ExecutionOutcome", "ExecutionPolicy", "ExecutionRecordPlan", "ExecutionRecordResult", "ExecutionRecordSummary", "ExecutionReport", "ExecutionSnapshot", "ExecutionSnapshotResult", "ExecutionSummary", "ExecutionTracePlan", "ExecutionTraceResult", "ExecutionTraceSummary", "ExecutionWindow", "FailureRecord"],
        validation_contracts=["GateAudit", "ValidationFailureSummary", "ValidationGate", "ValidationGateAuditResult", "ValidationGateResult", "ValidationOutcome", "ValidationPlan", "ValidationPlanResult", "ValidationSessionRecord", "ValidationSummary"],
        artifact_contracts=["ArtifactIndex", "ArtifactLinkIndex", "ArtifactManifest", "ArtifactPackage", "ArtifactPackageAudit", "ArtifactPackageResult", "ArtifactRecord", "DiffSummary", "FileChangePlan", "FileChangeResult", "FileScopeRecord", "FileTarget", "FileWritePlan", "FileWriteResult", "OutputBundle", "OutputBundleAudit", "OutputBundleResult", "TaskArtifactLink", "WriteIntent"],
        routing_contracts=["ApprovalRecord", "CommandPlan", "CommandResult", "ExecutionRouteAudit", "ExecutionRoutePlan", "ExecutionRouteResult", "Job", "PromptEnvelope", "PromptResult", "PromptSegment", "RequestBatch", "RequestBatchAudit", "RequestBatchResult", "RequestContext", "RequestQueue", "RequestQueueAudit", "RequestQueueResult", "RetryPolicy", "ReviewRecord", "ReviewSummary", "RollbackRecord", "RouteAudit", "RouteConstraint", "RoutePlan", "RouteResult", "RouteSelection", "RouteSummary", "RunLedger", "RunManifest", "RunMetrics", "RunRequest", "RunResult", "RunState", "ScopeAuditResult", "ScopeGuard", "ScopeResult", "ToolInvocation", "ToolResult", "WorkspaceSchema"],
    )
    registry_keys = sorted(SCHEMA_REGISTRY.keys())
    category_counts = {
        "session_contracts": len(catalog.session_contracts),
        "execution_contracts": len(catalog.execution_contracts),
        "validation_contracts": len(catalog.validation_contracts),
        "artifact_contracts": len(catalog.artifact_contracts),
        "routing_contracts": len(catalog.routing_contracts),
    }
    categories_present = sorted([k for k, v in category_counts.items() if v > 0])
    return {
        "total_schema_count": len(SCHEMA_REGISTRY),
        "registry_keys": registry_keys,
        "category_counts": category_counts,
        "categories_present": categories_present,
    }
