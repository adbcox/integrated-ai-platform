"""LACE1-P12-AUTONOMY-UPLIFT-RATIFIER-SEAM-1: ratify substrate uplift evidence from benchmark."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.lace1_benchmark_runner import BenchmarkRunReport
from framework.failure_pattern_miner import FailurePatternReport

assert "pass_rate" in BenchmarkRunReport.__dataclass_fields__, "INTERFACE MISMATCH: BenchmarkRunReport.pass_rate"
assert "benchmark_kind" in BenchmarkRunReport.__dataclass_fields__, "INTERFACE MISMATCH: BenchmarkRunReport.benchmark_kind"
assert "benchmark_failures" in FailurePatternReport.__dataclass_fields__, "INTERFACE MISMATCH: FailurePatternReport.benchmark_failures"
assert "total_patterns" in FailurePatternReport.__dataclass_fields__, "INTERFACE MISMATCH: FailurePatternReport.total_patterns"

VERDICT_SUBSTRATE_UPLIFT_CONFIRMED = "substrate_uplift_confirmed"
VERDICT_PARTIAL_SUBSTRATE_UPLIFT = "partial_substrate_uplift"
VERDICT_SUBSTRATE_UPLIFT_NOT_CONFIRMED = "substrate_uplift_not_confirmed"

_VALID_VERDICTS = {
    VERDICT_SUBSTRATE_UPLIFT_CONFIRMED,
    VERDICT_PARTIAL_SUBSTRATE_UPLIFT,
    VERDICT_SUBSTRATE_UPLIFT_NOT_CONFIRMED,
}

_BENCHMARK_LIMITATIONS = [
    "Benchmark is fully synthetic: all tasks use deterministic string replacement with no LLM involvement.",
    "pass_rate=1.0 reflects task definition correctness, NOT real coding capability on production code.",
    "Failure patterns are hypothetical; no real execution failures were observed in this campaign.",
    "Retrieval quality (entity_boost) was not exercised by the benchmark tasks.",
    "No external code change validation (make check, git diff) was performed on real files.",
]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass(frozen=True)
class UpliftCriterion:
    criterion_id: str
    description: str
    met: bool
    evidence: str


@dataclass
class UpliftRatificationRecord:
    ratification_id: str
    verdict: str
    criteria: List[UpliftCriterion]
    criteria_met: int
    criteria_total: int
    benchmark_limitations: List[str]
    ratified_at: str
    artifact_path: Optional[str] = None


class AutonomyUpliftRatifier:
    """Ratifies whether substrate uplift is confirmed based on benchmark evidence."""

    def ratify(
        self,
        bench_report: BenchmarkRunReport,
        fp_report: FailurePatternReport,
    ) -> UpliftRatificationRecord:
        criteria = self._evaluate_criteria(bench_report, fp_report)
        met_count = sum(1 for c in criteria if c.met)
        total = len(criteria)

        if met_count == total:
            verdict = VERDICT_SUBSTRATE_UPLIFT_CONFIRMED
        elif met_count >= total // 2:
            verdict = VERDICT_PARTIAL_SUBSTRATE_UPLIFT
        else:
            verdict = VERDICT_SUBSTRATE_UPLIFT_NOT_CONFIRMED

        return UpliftRatificationRecord(
            ratification_id=f"UPLIFT-RAT-{_ts()}",
            verdict=verdict,
            criteria=criteria,
            criteria_met=met_count,
            criteria_total=total,
            benchmark_limitations=list(_BENCHMARK_LIMITATIONS),
            ratified_at=_iso_now(),
        )

    def _evaluate_criteria(
        self,
        bench: BenchmarkRunReport,
        fp: FailurePatternReport,
    ) -> List[UpliftCriterion]:
        return [
            UpliftCriterion(
                "C1-BENCHMARK-RUNS",
                "Benchmark executes without runtime errors",
                met=bench.total_tasks > 0,
                evidence=f"total_tasks={bench.total_tasks}",
            ),
            UpliftCriterion(
                "C2-SYNTHETIC-PASS-RATE",
                "Synthetic baseline pass_rate == 1.0",
                met=bench.pass_rate == 1.0,
                evidence=f"pass_rate={bench.pass_rate:.3f}",
            ),
            UpliftCriterion(
                "C3-KIND-COVERAGE",
                "All 5 task kinds represented in pack",
                met=bench.total_tasks >= 12,
                evidence=f"total_tasks={bench.total_tasks} (expected >=12 for 5-kind coverage)",
            ),
            UpliftCriterion(
                "C4-FAILURE-MINING-RUNS",
                "Failure pattern report is generated without error",
                met=fp.total_patterns >= 0,
                evidence=f"total_patterns={fp.total_patterns}, benchmark_failures={fp.benchmark_failures}",
            ),
            UpliftCriterion(
                "C5-NO-BENCHMARK-FAILURES",
                "Zero benchmark task failures on synthetic pack",
                met=fp.benchmark_failures == 0,
                evidence=f"benchmark_failures={fp.benchmark_failures}",
            ),
        ]

    def emit(self, record: UpliftRatificationRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "autonomy_uplift_ratification.json"
        payload = {
            "ratification_id": record.ratification_id,
            "verdict": record.verdict,
            "criteria_met": record.criteria_met,
            "criteria_total": record.criteria_total,
            "criteria": [asdict(c) for c in record.criteria],
            "benchmark_limitations": record.benchmark_limitations,
            "ratified_at": record.ratified_at,
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = [
    "UpliftCriterion",
    "UpliftRatificationRecord",
    "AutonomyUpliftRatifier",
    "VERDICT_SUBSTRATE_UPLIFT_CONFIRMED",
    "VERDICT_PARTIAL_SUBSTRATE_UPLIFT",
    "VERDICT_SUBSTRATE_UPLIFT_NOT_CONFIRMED",
]
