"""CmdbPromotionRatifier — LAPC1 P8.

Derives cmdb_done or cmdb_deferred from CmdbEvidenceReport.
Decision: cmdb_done only if all 5 criteria passed.
Inspection gate confirmed:
  CmdbEvidenceReport fields: criterion_results, overall_result, criteria_passed,
                               criteria_total, generated_at, artifact_path
  CMDB_PROOF_SUFFICIENT = 'cmdb_proof_sufficient'
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.cmdb_promotion_evidence import (
    CmdbEvidenceReport as _CmdbEvidenceReport,
    CMDB_PROOF_SUFFICIENT as _CMDB_PROOF_SUFFICIENT,
)

assert "criteria_passed" in _CmdbEvidenceReport.__dataclass_fields__, "INTERFACE MISMATCH: CmdbEvidenceReport.criteria_passed"
assert "criteria_total" in _CmdbEvidenceReport.__dataclass_fields__, "INTERFACE MISMATCH: CmdbEvidenceReport.criteria_total"
assert "overall_result" in _CmdbEvidenceReport.__dataclass_fields__, "INTERFACE MISMATCH: CmdbEvidenceReport.overall_result"
assert _CMDB_PROOF_SUFFICIENT == "cmdb_proof_sufficient", "INTERFACE MISMATCH: CMDB_PROOF_SUFFICIENT value"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "cmdb_promotion"

CMDB_PROMOTION_DONE = "cmdb_done"
CMDB_PROMOTION_DEFERRED = "cmdb_deferred"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class CmdbPromotionArtifact:
    decision: str
    rationale: str
    criteria_passed: int
    criteria_total: int
    evidence_result: str
    ratified_at: str
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "decision": self.decision,
            "rationale": self.rationale,
            "criteria_passed": self.criteria_passed,
            "criteria_total": self.criteria_total,
            "evidence_result": self.evidence_result,
            "ratified_at": self.ratified_at,
        }


def ratify_cmdb_promotion(
    evidence_report: Optional[_CmdbEvidenceReport] = None,
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> CmdbPromotionArtifact:
    if evidence_report is not None:
        criteria_passed = evidence_report.criteria_passed
        criteria_total = evidence_report.criteria_total
        evidence_result = evidence_report.overall_result
    else:
        criteria_passed = 0
        criteria_total = 5
        evidence_result = "not_evaluated"

    done = (criteria_passed == criteria_total == 5)

    if done:
        decision = CMDB_PROMOTION_DONE
        rationale = (
            f"All {criteria_total} CMDB proof criteria passed. "
            "Local governance files readable and integration gate functional. "
            "CMDB promoted to done."
        )
    else:
        decision = CMDB_PROMOTION_DEFERRED
        rationale = (
            f"CMDB deferred. {criteria_passed}/{criteria_total} criteria passed. "
            f"evidence_result={evidence_result!r}. "
            "All 5 criteria required for cmdb_done."
        )

    artifact = CmdbPromotionArtifact(
        decision=decision,
        rationale=rationale,
        criteria_passed=criteria_passed,
        criteria_total=criteria_total,
        evidence_result=evidence_result,
        ratified_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "LAPC1_cmdb_promotion.json"
        out_path.write_text(
            json.dumps(artifact.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        artifact.artifact_path = str(out_path)

    return artifact


__all__ = [
    "CMDB_PROMOTION_DONE",
    "CMDB_PROMOTION_DEFERRED",
    "CmdbPromotionArtifact",
    "ratify_cmdb_promotion",
]
