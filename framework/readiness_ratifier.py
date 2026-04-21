"""Terminal readiness ratification for the LASC1 campaign.

Reads a ReadinessEvaluation and emits a machine-readable RatificationArtifact.
READY means only "ready for controlled adapter campaign" — not "implement now."
Default expected outcome is DEFER on sparse evidence.

No Aider adapter code in this module.

Inspection gate output (packet 10):
  evaluate_readiness(dry_run=True) -> verdict: deferred_pending_evidence, attempts: 0
  -> Live evidence is sparse; ratification will emit DEFER by default.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from framework.readiness_evaluator import ReadinessEvaluation, evaluate_readiness

# -- import-time assertion --
assert "all_criteria_passed" in ReadinessEvaluation.__dataclass_fields__, \
    "INTERFACE MISMATCH: ReadinessEvaluation.all_criteria_passed"
assert callable(evaluate_readiness), "INTERFACE MISMATCH: evaluate_readiness"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "readiness"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RatificationDecision:
    DEFER = "deferred_pending_evidence"
    READY = "ready_for_controlled_adapter_campaign"


@dataclass
class RatificationArtifact:
    campaign_id: str
    decision: str
    ratified_at: str
    total_attempts: int
    all_criteria_passed: bool
    criteria_summary: list[dict[str, Any]]
    defer_reasons: list[str]
    next_steps: str
    artifact_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "campaign_id": self.campaign_id,
            "decision": self.decision,
            "ratified_at": self.ratified_at,
            "total_attempts": self.total_attempts,
            "all_criteria_passed": self.all_criteria_passed,
            "criteria_summary": self.criteria_summary,
            "defer_reasons": self.defer_reasons,
            "next_steps": self.next_steps,
        }


def ratify(
    evaluation: ReadinessEvaluation,
    *,
    campaign_id: str = "LOCAL-AUTONOMY-STABILITY-CLOSEOUT-CAMPAIGN-1",
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> RatificationArtifact:
    """Produce a RatificationArtifact from a ReadinessEvaluation.

    If all_criteria_passed: decision = READY (authorization for future controlled adapter campaign).
    Otherwise: decision = DEFER with structured reasons.

    No Aider adapter code is emitted in either branch.
    """
    if evaluation.all_criteria_passed:
        decision = RatificationDecision.READY
        next_steps = (
            "All readiness criteria met. A future controlled adapter campaign may reference "
            "this artifact as authorization to begin Aider adapter integration in a bounded scope. "
            "No adapter code is included in this ratification."
        )
    else:
        decision = RatificationDecision.DEFER
        reasons_text = "; ".join(evaluation.defer_reasons) if evaluation.defer_reasons else "insufficient evidence"
        next_steps = (
            f"Readiness deferred: {reasons_text}. "
            "Accumulate more evidence via TaskRepetitionHarness, then re-run ReadinessEvaluation. "
            "Do not implement Aider adapter until ratification decision is READY."
        )

    criteria_summary = [
        {
            "name": c.name,
            "passed": c.passed,
            "observed_value": round(c.observed_value, 4),
            "threshold": c.threshold,
        }
        for c in evaluation.criteria
    ]

    artifact = RatificationArtifact(
        campaign_id=campaign_id,
        decision=decision,
        ratified_at=_iso_now(),
        total_attempts=evaluation.total_attempts,
        all_criteria_passed=evaluation.all_criteria_passed,
        criteria_summary=criteria_summary,
        defer_reasons=evaluation.defer_reasons,
        next_steps=next_steps,
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        artifact_file = out_dir / "LASC1_ratification.json"
        artifact_file.write_text(
            json.dumps(artifact.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        artifact.artifact_path = str(artifact_file)

    return artifact


__all__ = [
    "RatificationDecision",
    "RatificationArtifact",
    "ratify",
]
