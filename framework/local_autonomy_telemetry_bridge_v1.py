"""LocalAutonomyTelemetryBridgeV1: derive autonomy evidence from real produced artifacts."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from framework.persistent_execution_ledger_v1 import PersistentExecutionLedgerV1
from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
from framework.qualification_readiness_v1 import QualificationReadinessResultV1


LOCAL_EXECUTORS = frozenset({"aider", "ollama", "local_fast", "local_hard", "local_smart"})
CLAUDE_EXECUTORS = frozenset({"claude", "claude_code", "remote_assist"})


@dataclass
class TelemetryEvidenceSummaryV1:
    routine_local_execution_ready: bool
    first_pass_success_signal: bool
    retry_discipline_signal: bool
    escalation_rate_signal: bool
    artifact_completeness_signal: bool
    evidence_gaps: List[str]
    signal_detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "routine_local_execution_ready": self.routine_local_execution_ready,
            "first_pass_success_signal": self.first_pass_success_signal,
            "retry_discipline_signal": self.retry_discipline_signal,
            "escalation_rate_signal": self.escalation_rate_signal,
            "artifact_completeness_signal": self.artifact_completeness_signal,
            "evidence_gaps": self.evidence_gaps,
            "signal_detail": self.signal_detail,
        }


class LocalAutonomyTelemetryBridgeV1:
    """Derive structured autonomy evidence from real ledger + artifact surfaces."""

    FIRST_PASS_THRESHOLD = 0.50
    ESCALATION_RATE_LIMIT = 0.25
    LOCAL_PASS_RATE_THRESHOLD = 0.75

    def derive(
        self,
        ledger: PersistentExecutionLedgerV1,
        unified_artifact: UnifiedValidationArtifactV1,
        qualification_result: QualificationReadinessResultV1,
        local_artifact_paths: Optional[List[Path]] = None,
        retries_within_budget: bool = True,
        escalation_count: int = 0,
    ) -> TelemetryEvidenceSummaryV1:
        evidence_gaps: List[str] = []
        entries = ledger.load_records()

        local_entries = [e for e in entries if e.executor.lower() in LOCAL_EXECUTORS]
        claude_entries = [e for e in entries if e.executor.lower() in CLAUDE_EXECUTORS]

        total = len(entries)
        local_count = len(local_entries)
        local_passed = sum(1 for e in local_entries if e.all_passed)
        local_pass_rate = local_passed / local_count if local_count > 0 else 0.0

        # First-pass success signal: >= 50% of local runs passed without retry
        first_pass_rate = local_pass_rate
        first_pass_signal = first_pass_rate >= self.FIRST_PASS_THRESHOLD
        if not first_pass_signal:
            evidence_gaps.append(
                f"first_pass_success_signal: {first_pass_rate:.2f} < {self.FIRST_PASS_THRESHOLD}"
            )

        # Retry discipline signal
        retry_signal = retries_within_budget
        if not retry_signal:
            evidence_gaps.append("retry_discipline_signal: retries exceeded declared budget")

        # Escalation rate signal
        escalation_rate = escalation_count / total if total > 0 else 0.0
        escalation_signal = escalation_rate <= self.ESCALATION_RATE_LIMIT
        if not escalation_signal:
            evidence_gaps.append(
                f"escalation_rate_signal: {escalation_rate:.2f} > {self.ESCALATION_RATE_LIMIT}"
            )

        # Artifact completeness signal
        artifact_signal = unified_artifact.all_passed and qualification_result.readiness_ready
        if not artifact_signal:
            if not unified_artifact.all_passed:
                evidence_gaps.append("artifact_completeness_signal: unified_artifact has failures")
            if not qualification_result.readiness_ready:
                for gap in qualification_result.blocking_gaps:
                    evidence_gaps.append(f"qualification_gap: {gap}")

        # Local artifact presence check
        if local_artifact_paths:
            missing = [str(p) for p in local_artifact_paths if not Path(p).exists()]
            if missing:
                evidence_gaps.append(f"local_artifact_paths missing: {missing}")

        # Routine ready: local runs present, pass rate >= threshold, no gaps in core signals
        has_local = local_count > 0
        if not has_local:
            evidence_gaps.append("no local executor runs in persistent ledger")

        routine_local_execution_ready = (
            has_local
            and local_pass_rate >= self.LOCAL_PASS_RATE_THRESHOLD
            and first_pass_signal
            and retry_signal
            and escalation_signal
            and artifact_signal
        )

        return TelemetryEvidenceSummaryV1(
            routine_local_execution_ready=routine_local_execution_ready,
            first_pass_success_signal=first_pass_signal,
            retry_discipline_signal=retry_signal,
            escalation_rate_signal=escalation_signal,
            artifact_completeness_signal=artifact_signal,
            evidence_gaps=evidence_gaps,
            signal_detail={
                "total_ledger_runs": total,
                "local_executor_runs": local_count,
                "local_pass_rate": local_pass_rate,
                "claude_executor_runs": len(claude_entries),
                "escalation_rate": escalation_rate,
                "retries_within_budget": retries_within_budget,
            },
        )
