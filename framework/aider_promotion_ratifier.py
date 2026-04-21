"""AiderPromotionRatifier — LAPC1 P4.

Derives aider_done or aider_partial from AiderLiveGateReport and AiderLiveProofReport.
Inspection gate confirmed:
  AiderLiveGateReport fields: checks, overall_result, live_execution_safe, blocking_checks,
                               generated_at, artifact_path
  AiderLiveProofReport fields: proof_status, records, total_runs, successful_runs, gate_result,
                                live_execution_safe, notes, generated_at, artifact_path
  PROOF_STATUS_LIVE_PROVEN = 'live_proven'
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.aider_live_execution_gate import AiderLiveGateReport as _AiderLiveGateReport
from framework.aider_live_proof import (
    AiderLiveProofReport as _AiderLiveProofReport,
    PROOF_STATUS_LIVE_PROVEN as _PROOF_STATUS_LIVE_PROVEN,
    PROOF_STATUS_BLOCKED as _PROOF_STATUS_BLOCKED,
)

assert "live_execution_safe" in _AiderLiveGateReport.__dataclass_fields__, "INTERFACE MISMATCH: AiderLiveGateReport.live_execution_safe"
assert "overall_result" in _AiderLiveGateReport.__dataclass_fields__, "INTERFACE MISMATCH: AiderLiveGateReport.overall_result"
assert "proof_status" in _AiderLiveProofReport.__dataclass_fields__, "INTERFACE MISMATCH: AiderLiveProofReport.proof_status"
assert "successful_runs" in _AiderLiveProofReport.__dataclass_fields__, "INTERFACE MISMATCH: AiderLiveProofReport.successful_runs"
assert _PROOF_STATUS_LIVE_PROVEN == "live_proven", "INTERFACE MISMATCH: PROOF_STATUS_LIVE_PROVEN value"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "aider_promotion"

AIDER_PROMOTION_DONE = "aider_done"
AIDER_PROMOTION_PARTIAL = "aider_partial"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class AiderPromotionArtifact:
    decision: str
    rationale: str
    gate_result: str
    proof_status: str
    successful_live_runs: int
    live_execution_safe: bool
    ratified_at: str
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "decision": self.decision,
            "rationale": self.rationale,
            "gate_result": self.gate_result,
            "proof_status": self.proof_status,
            "successful_live_runs": self.successful_live_runs,
            "live_execution_safe": self.live_execution_safe,
            "ratified_at": self.ratified_at,
        }


def ratify_aider_promotion(
    gate_report: Optional[_AiderLiveGateReport] = None,
    proof_report: Optional[_AiderLiveProofReport] = None,
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> AiderPromotionArtifact:
    # Resolve from provided artifacts or defaults
    if gate_report is not None:
        gate_result = gate_report.overall_result
        live_execution_safe = gate_report.live_execution_safe
    else:
        gate_result = "not_evaluated"
        live_execution_safe = False

    if proof_report is not None:
        proof_status = proof_report.proof_status
        successful_live_runs = proof_report.successful_runs
    else:
        proof_status = "not_evaluated"
        successful_live_runs = 0

    # Decision: aider_done only if gate passed AND proof is live_proven AND >= 1 success
    done = (
        live_execution_safe
        and proof_status == _PROOF_STATUS_LIVE_PROVEN
        and successful_live_runs >= 1
    )

    if done:
        decision = AIDER_PROMOTION_DONE
        rationale = (
            f"Live gate passed, live proof succeeded with {successful_live_runs} run(s). "
            "Aider promoted to done."
        )
    else:
        decision = AIDER_PROMOTION_PARTIAL
        reasons = []
        if not live_execution_safe:
            reasons.append("live execution gate blocked")
        if proof_status != _PROOF_STATUS_LIVE_PROVEN:
            reasons.append(f"proof_status={proof_status!r} (requires live_proven)")
        if successful_live_runs < 1:
            reasons.append("no successful live runs")
        rationale = (
            "Aider remains partial. Blockers: "
            + ("; ".join(reasons) if reasons else "unknown")
            + ". Upgrade path: register 'aider' in KNOWN_FRAMEWORK_COMMANDS, "
            "verify preflight passes, then rerun proof."
        )

    artifact = AiderPromotionArtifact(
        decision=decision,
        rationale=rationale,
        gate_result=gate_result,
        proof_status=proof_status,
        successful_live_runs=successful_live_runs,
        live_execution_safe=live_execution_safe,
        ratified_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "LAPC1_aider_promotion.json"
        out_path.write_text(
            json.dumps(artifact.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        artifact.artifact_path = str(out_path)

    return artifact


__all__ = [
    "AIDER_PROMOTION_DONE",
    "AIDER_PROMOTION_PARTIAL",
    "AiderPromotionArtifact",
    "ratify_aider_promotion",
]
