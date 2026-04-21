"""CMDB-AUTHORITATIVE-PROMOTION-RATIFIER-SEAM-1: decide cmdb_done or cmdb_deferred from P2-P6 evidence."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class CmdbRatificationCriterion:
    criterion_name: str
    passed: bool
    evidence_source: str
    detail: str


@dataclass
class CmdbAuthoritativePromotionDecision:
    decision: str  # "cmdb_done" | "cmdb_deferred"
    criteria: List[CmdbRatificationCriterion]
    criteria_passed: int
    criteria_total: int
    blocking_reasons: List[str]
    decided_at: str
    artifact_path: Optional[str]


class CmdbAuthoritativePromotionRatifier:
    """Decides cmdb_done or cmdb_deferred from 4 evidence artifacts."""

    def ratify(
        self,
        *,
        proof_result: dict,
        read_model_output: dict,
        operating_context: dict,
        authority_boundary: dict,
    ) -> CmdbAuthoritativePromotionDecision:
        criteria: List[CmdbRatificationCriterion] = []
        blocking_reasons: List[str] = []

        # Criterion 1: proof_verdict_proven
        proof_verdict = proof_result.get("proof_verdict", "")
        c1_passed = proof_verdict == "proven"
        if not c1_passed:
            blocking_reasons.append(f"proof_verdict_proven: proof_verdict={proof_verdict!r}")
        criteria.append(CmdbRatificationCriterion(
            criterion_name="proof_verdict_proven",
            passed=c1_passed,
            evidence_source="proof_harness_result.json",
            detail=f"proof_verdict={proof_verdict!r}",
        ))

        # Criterion 2: read_model_complete
        rmc = read_model_output.get("read_model_complete", False)
        c2_passed = rmc is True
        if not c2_passed:
            blocking_reasons.append(f"read_model_complete: read_model_complete={rmc!r}")
        criteria.append(CmdbRatificationCriterion(
            criterion_name="read_model_complete",
            passed=c2_passed,
            evidence_source="read_model_output.json",
            detail=f"read_model_complete={rmc!r}",
        ))

        # Criterion 3: operating_context_complete
        occ = operating_context.get("context_complete", False)
        c3_passed = occ is True
        if not c3_passed:
            blocking_reasons.append(f"operating_context_complete: context_complete={occ!r}")
        criteria.append(CmdbRatificationCriterion(
            criterion_name="operating_context_complete",
            passed=c3_passed,
            evidence_source="operating_context.json",
            detail=f"context_complete={occ!r}",
        ))

        # Criterion 4: boundary_no_overlap
        violations = authority_boundary.get("overlap_violations", None)
        c4_passed = violations == []
        if not c4_passed:
            blocking_reasons.append(f"boundary_no_overlap: overlap_violations={violations!r}")
        criteria.append(CmdbRatificationCriterion(
            criterion_name="boundary_no_overlap",
            passed=c4_passed,
            evidence_source="authority_boundary.json",
            detail=f"overlap_violations={violations!r}",
        ))

        criteria_passed = sum(1 for c in criteria if c.passed)
        criteria_total = len(criteria)
        decision = "cmdb_done" if criteria_passed == criteria_total else "cmdb_deferred"

        return CmdbAuthoritativePromotionDecision(
            decision=decision,
            criteria=criteria,
            criteria_passed=criteria_passed,
            criteria_total=criteria_total,
            blocking_reasons=blocking_reasons if decision == "cmdb_deferred" else [],
            decided_at=_iso_now(),
            artifact_path=None,
        )


def emit_cmdb_authoritative_promotion_decision(
    decision: CmdbAuthoritativePromotionDecision,
    *,
    artifact_dir: Path = Path("artifacts") / "cmdb_authoritative_adoption",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "cmdb_authoritative_promotion_decision.json"
    out_path.write_text(
        json.dumps(
            {
                "decision": decision.decision,
                "criteria_passed": decision.criteria_passed,
                "criteria_total": decision.criteria_total,
                "blocking_reasons": decision.blocking_reasons,
                "decided_at": decision.decided_at,
                "criteria": [
                    {
                        "criterion_name": c.criterion_name,
                        "passed": c.passed,
                        "evidence_source": c.evidence_source,
                        "detail": c.detail,
                    }
                    for c in decision.criteria
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    decision.artifact_path = str(out_path)
    return str(out_path)


__all__ = [
    "CmdbRatificationCriterion",
    "CmdbAuthoritativePromotionDecision",
    "CmdbAuthoritativePromotionRatifier",
    "emit_cmdb_authoritative_promotion_decision",
]
