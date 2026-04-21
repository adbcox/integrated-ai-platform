"""LocalAutonomyEvidenceBridgeV1: derive local-autonomy evidence from execution surfaces."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from framework.local_execution_ledger_v1 import LocalExecutionLedgerV1
from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
from framework.qualification_readiness_v1 import QualificationReadinessResultV1


@dataclass
class LocalAutonomyEvidenceSummaryV1:
    routine_local_execution_ready: bool
    explicit_escalation_required: bool
    claude_removed_from_routine_path_signal: bool
    evidence_gaps: List[str]
    evidence_detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "routine_local_execution_ready": self.routine_local_execution_ready,
            "explicit_escalation_required": self.explicit_escalation_required,
            "claude_removed_from_routine_path_signal": self.claude_removed_from_routine_path_signal,
            "evidence_gaps": self.evidence_gaps,
            "evidence_detail": self.evidence_detail,
        }


class LocalAutonomyEvidenceBridgeV1:
    """Derive local-autonomy evidence from ledger, artifact, and readiness surfaces."""

    LOCAL_EXECUTOR_NAMES = {"aider", "ollama", "local_fast", "local_hard", "local_smart"}
    CLAUDE_EXECUTOR_NAMES = {"claude", "claude_code", "remote_assist"}

    def derive(
        self,
        ledger: LocalExecutionLedgerV1,
        unified_artifact: UnifiedValidationArtifactV1,
        qualification_result: QualificationReadinessResultV1,
        escalation_notes: Optional[List[str]] = None,
    ) -> LocalAutonomyEvidenceSummaryV1:
        evidence_gaps: List[str] = []

        # Determine if routine local execution is ready
        local_runs = [
            e for e in ledger.all_entries()
            if e.executor.lower() in self.LOCAL_EXECUTOR_NAMES
        ]
        has_local_runs = len(local_runs) > 0
        local_pass_rate = (
            sum(1 for e in local_runs if e.all_passed) / len(local_runs)
            if local_runs else 0.0
        )

        routine_local_execution_ready = (
            has_local_runs
            and local_pass_rate >= 0.75
            and qualification_result.readiness_ready
            and unified_artifact.all_passed
        )

        if not has_local_runs:
            evidence_gaps.append("no local executor runs recorded in ledger")
        if local_pass_rate < 0.75 and has_local_runs:
            evidence_gaps.append(
                f"local executor pass_rate {local_pass_rate:.2f} < 0.75"
            )
        if not qualification_result.readiness_ready:
            for gap in qualification_result.blocking_gaps:
                evidence_gaps.append(f"qualification_gap: {gap}")
        if not unified_artifact.all_passed:
            evidence_gaps.append("unified_artifact has failing validations")

        # Check if Claude-based runs are present (signals Claude still on routine path)
        claude_runs = [
            e for e in ledger.all_entries()
            if e.executor.lower() in self.CLAUDE_EXECUTOR_NAMES
        ]
        claude_removed_from_routine_path_signal = len(claude_runs) == 0

        if not claude_removed_from_routine_path_signal:
            evidence_gaps.append(
                f"{len(claude_runs)} Claude executor run(s) still present in ledger; "
                "Claude not yet removed from routine path"
            )

        explicit_escalation_required = True  # always true for Phase 6 governance

        evidence_detail: Dict[str, Any] = {
            "total_ledger_runs": ledger.total_runs,
            "local_executor_runs": len(local_runs),
            "local_pass_rate": local_pass_rate,
            "claude_executor_runs": len(claude_runs),
            "qualification_readiness_ready": qualification_result.readiness_ready,
            "unified_artifact_all_passed": unified_artifact.all_passed,
        }
        if escalation_notes:
            evidence_detail["escalation_notes"] = escalation_notes

        return LocalAutonomyEvidenceSummaryV1(
            routine_local_execution_ready=routine_local_execution_ready,
            explicit_escalation_required=explicit_escalation_required,
            claude_removed_from_routine_path_signal=claude_removed_from_routine_path_signal,
            evidence_gaps=evidence_gaps,
            evidence_detail=evidence_detail,
        )
