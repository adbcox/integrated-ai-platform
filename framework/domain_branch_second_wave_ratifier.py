"""DomainBranchSecondWaveRatifier — LAPC1 P11.

Ratifies Athlete Analytics and Office Automation to done or scaffold_complete_product_deferred.
Inspection gate confirmed:
  SECOND_WAVE_MANIFEST.branch_count: 2
  SECOND_WAVE_MANIFEST.branch_names(): ['athlete_analytics', 'office_automation']
  DomainBranchProofHarness has evaluate_batch
  BranchProofResult fields: branch_name, verdict, criterion_results, criteria_passed, criteria_total, evaluated_at
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.domain_branch_proof_harness import (
    DomainBranchProofHarness as _DomainBranchProofHarness,
    BranchProofResult as _BranchProofResult,
    BRANCH_VERDICT_DONE as _BRANCH_VERDICT_DONE,
    BRANCH_VERDICT_SCAFFOLD_COMPLETE_PRODUCT_DEFERRED as _BRANCH_VERDICT_SCAFFOLD,
)
from framework.domain_branch_second_wave import (
    SECOND_WAVE_MANIFEST as _SECOND_WAVE_MANIFEST,
    SecondWaveDomainRunner as _SecondWaveDomainRunner,
)

assert hasattr(_DomainBranchProofHarness, "evaluate_batch"), "INTERFACE MISMATCH: DomainBranchProofHarness.evaluate_batch"
assert "branch_name" in _BranchProofResult.__dataclass_fields__, "INTERFACE MISMATCH: BranchProofResult.branch_name"
assert "verdict" in _BranchProofResult.__dataclass_fields__, "INTERFACE MISMATCH: BranchProofResult.verdict"
assert _SECOND_WAVE_MANIFEST.branch_count == 2, "INTERFACE MISMATCH: SECOND_WAVE_MANIFEST.branch_count"
assert _SECOND_WAVE_MANIFEST.branch_names() == ["athlete_analytics", "office_automation"], "INTERFACE MISMATCH: SECOND_WAVE_MANIFEST.branch_names()"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "second_wave_promotion"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class SecondWavePromotionRecord:
    branch_name: str
    verdict: str
    criteria_passed: int
    criteria_total: int
    detail: str

    def to_dict(self) -> dict:
        return {
            "branch_name": self.branch_name,
            "verdict": self.verdict,
            "criteria_passed": self.criteria_passed,
            "criteria_total": self.criteria_total,
            "detail": self.detail,
        }


@dataclass
class SecondWavePromotionArtifact:
    records: list
    any_done: bool
    all_scaffold_complete: bool
    total_branches: int
    ratified_at: str
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "any_done": self.any_done,
            "all_scaffold_complete": self.all_scaffold_complete,
            "total_branches": self.total_branches,
            "ratified_at": self.ratified_at,
            "records": [r.to_dict() for r in self.records],
        }


def ratify_second_wave_promotion(
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> SecondWavePromotionArtifact:
    harness = _DomainBranchProofHarness()
    runner = _SecondWaveDomainRunner()
    results = harness.evaluate_batch(_SECOND_WAVE_MANIFEST, runner, repetitions=2)

    records = []
    for res in results:
        records.append(SecondWavePromotionRecord(
            branch_name=res.branch_name,
            verdict=res.verdict,
            criteria_passed=res.criteria_passed,
            criteria_total=res.criteria_total,
            detail=f"{res.criteria_passed}/{res.criteria_total} criteria passed",
        ))

    any_done = any(r.verdict == _BRANCH_VERDICT_DONE for r in records)
    all_scaffold_complete = all(r.verdict == _BRANCH_VERDICT_SCAFFOLD for r in records)

    artifact = SecondWavePromotionArtifact(
        records=records,
        any_done=any_done,
        all_scaffold_complete=all_scaffold_complete,
        total_branches=len(records),
        ratified_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "LAPC1_second_wave_promotion.json"
        out_path.write_text(
            json.dumps(artifact.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        artifact.artifact_path = str(out_path)

    return artifact


__all__ = [
    "SecondWavePromotionRecord",
    "SecondWavePromotionArtifact",
    "ratify_second_wave_promotion",
]
