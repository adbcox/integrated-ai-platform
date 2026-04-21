"""TerminalAutonomyRatifier: produces final ratification verdict for a LARAC2 campaign."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.adapter_readiness_stress import StressHarnessResult
from framework.controlled_adapter_scaffold import AdapterScaffoldPlan
from framework.adapter_campaign_pre_authorizer import RatificationArtifact

# -- import-time assertions --
assert "verdict" in StressHarnessResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: StressHarnessResult.verdict"
assert "scaffold_decision" in AdapterScaffoldPlan.__dataclass_fields__, \
    "INTERFACE MISMATCH: AdapterScaffoldPlan.scaffold_decision"
assert "decision" in RatificationArtifact.__dataclass_fields__, \
    "INTERFACE MISMATCH: RatificationArtifact.decision"
assert "all_criteria_passed" in RatificationArtifact.__dataclass_fields__, \
    "INTERFACE MISMATCH: RatificationArtifact.all_criteria_passed"

_RATIFIED = "ratified"
_DEFERRED = "deferred"
_BLOCKED = "blocked"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class RatificationCriterion:
    criterion_name: str
    passed: bool
    detail: str


@dataclass
class TerminalRatificationRecord:
    campaign_id: Optional[str]
    terminal_verdict: str  # "ratified" | "deferred" | "blocked"
    criteria: List[RatificationCriterion]
    criteria_passed: int
    criteria_total: int
    blocking_reasons: List[str]
    ratified_at: str
    artifact_path: Optional[str]


class TerminalAutonomyRatifier:
    """Produces a final terminal verdict from stress, scaffold, and pre-auth ratification inputs."""

    def ratify(
        self,
        *,
        stress_result: Optional[StressHarnessResult] = None,
        scaffold_plan: Optional[AdapterScaffoldPlan] = None,
        ratification_artifact: Optional[RatificationArtifact] = None,
    ) -> TerminalRatificationRecord:
        criteria: List[RatificationCriterion] = []
        blocking_reasons: List[str] = []

        # Criterion 1: stress harness stable
        if stress_result is not None:
            passed = stress_result.verdict == "stable"
            detail = f"stress_verdict={stress_result.verdict}"
            if not passed:
                blocking_reasons.append(f"stress not stable: {stress_result.verdict}")
        else:
            passed = False
            detail = "stress_result absent"
            blocking_reasons.append("stress_result not provided")
        criteria.append(RatificationCriterion(
            criterion_name="stress_stable", passed=passed, detail=detail
        ))

        # Criterion 2: scaffold cleared to proceed
        if scaffold_plan is not None:
            passed = scaffold_plan.scaffold_decision == "proceed"
            detail = f"scaffold_decision={scaffold_plan.scaffold_decision} gates={scaffold_plan.gates_passed}/{scaffold_plan.gates_total}"
            if not passed:
                blocking_reasons.append(f"scaffold not proceed: {scaffold_plan.scaffold_decision}")
        else:
            passed = False
            detail = "scaffold_plan absent"
            blocking_reasons.append("scaffold_plan not provided")
        criteria.append(RatificationCriterion(
            criterion_name="scaffold_proceed", passed=passed, detail=detail
        ))

        # Criterion 3: ratification artifact approved
        if ratification_artifact is not None:
            passed = (
                ratification_artifact.decision == "ratified"
                and ratification_artifact.all_criteria_passed
            )
            detail = f"decision={ratification_artifact.decision} all_criteria_passed={ratification_artifact.all_criteria_passed}"
            if not passed:
                blocking_reasons.append(f"ratification not approved: {ratification_artifact.decision}")
        else:
            passed = False
            detail = "ratification_artifact absent"
            blocking_reasons.append("ratification_artifact not provided")
        criteria.append(RatificationCriterion(
            criterion_name="ratification_approved", passed=passed, detail=detail
        ))

        criteria_passed = sum(1 for c in criteria if c.passed)
        criteria_total = len(criteria)

        if criteria_passed == criteria_total:
            terminal_verdict = _RATIFIED
        elif stress_result is None and scaffold_plan is None and ratification_artifact is None:
            terminal_verdict = _BLOCKED
        else:
            terminal_verdict = _DEFERRED

        campaign_id = (
            scaffold_plan.campaign_id if scaffold_plan is not None
            else (ratification_artifact.campaign_id if ratification_artifact is not None else None)
        )

        return TerminalRatificationRecord(
            campaign_id=campaign_id,
            terminal_verdict=terminal_verdict,
            criteria=criteria,
            criteria_passed=criteria_passed,
            criteria_total=criteria_total,
            blocking_reasons=blocking_reasons,
            ratified_at=_iso_now(),
            artifact_path=None,
        )


def emit_terminal_ratification(
    record: TerminalRatificationRecord,
    *,
    artifact_dir: Path = Path("artifacts") / "terminal_ratification",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "terminal_ratification_record.json"
    out_path.write_text(
        json.dumps(
            {
                "campaign_id": record.campaign_id,
                "terminal_verdict": record.terminal_verdict,
                "criteria_passed": record.criteria_passed,
                "criteria_total": record.criteria_total,
                "blocking_reasons": record.blocking_reasons,
                "ratified_at": record.ratified_at,
                "criteria": [
                    {
                        "criterion_name": c.criterion_name,
                        "passed": c.passed,
                        "detail": c.detail,
                    }
                    for c in record.criteria
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    record.artifact_path = str(out_path)
    return str(out_path)


__all__ = [
    "RatificationCriterion",
    "TerminalRatificationRecord",
    "TerminalAutonomyRatifier",
    "emit_terminal_ratification",
]
