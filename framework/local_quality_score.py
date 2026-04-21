"""LocalQualityScore: evidence-based quality signal from UnifiedLocalMetrics + TaskClassBenchmarkReport."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.unified_local_metrics import UnifiedLocalMetrics
from framework.task_class_benchmark import TaskClassBenchmarkReport

# -- import-time assertions --
assert "first_pass_rate" in UnifiedLocalMetrics.__dataclass_fields__, \
    "INTERFACE MISMATCH: UnifiedLocalMetrics.first_pass_rate"
assert "failure_rate" in UnifiedLocalMetrics.__dataclass_fields__, \
    "INTERFACE MISMATCH: UnifiedLocalMetrics.failure_rate"
assert "overall_pass_rate" in TaskClassBenchmarkReport.__dataclass_fields__, \
    "INTERFACE MISMATCH: TaskClassBenchmarkReport.overall_pass_rate"
assert "total_tasks" in TaskClassBenchmarkReport.__dataclass_fields__, \
    "INTERFACE MISMATCH: TaskClassBenchmarkReport.total_tasks"

_MIN_BENCHMARK_TASKS = 4


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _grade(score: float) -> str:
    if score >= 0.85:
        return "A"
    if score >= 0.70:
        return "B"
    if score >= 0.55:
        return "C"
    if score >= 0.40:
        return "D"
    return "F"


@dataclass(frozen=True)
class LocalQualityScore:
    raw_score: float
    grade: str
    evidence_weight: float
    first_pass_contribution: float
    benchmark_contribution: float
    reliability_contribution: float
    computed_at: str


def compute_quality_score(
    metrics: UnifiedLocalMetrics,
    *,
    benchmark_report: Optional[TaskClassBenchmarkReport] = None,
) -> LocalQualityScore:
    # First-pass rate contribution (40%)
    fp_contrib = metrics.first_pass_rate * 0.40

    # Benchmark contribution (35%)
    bench_weight = 0.0
    bench_contrib = 0.0
    if benchmark_report is not None and benchmark_report.total_tasks >= _MIN_BENCHMARK_TASKS:
        bench_contrib = benchmark_report.overall_pass_rate * 0.35
        bench_weight = 1.0
    else:
        # No or thin benchmark: degrade score conservatively
        bench_contrib = 0.20 * 0.35  # assume 20% pass rate
        bench_weight = 0.0

    # Reliability contribution: inverse of failure rate (25%)
    rel_contrib = (1.0 - min(metrics.failure_rate, 1.0)) * 0.25

    # Evidence weight: how much real evidence backs the score
    evidence_weight = (
        0.70 + 0.30 * bench_weight
    )

    raw_score = (fp_contrib + bench_contrib + rel_contrib) * evidence_weight

    return LocalQualityScore(
        raw_score=round(raw_score, 4),
        grade=_grade(raw_score),
        evidence_weight=round(evidence_weight, 4),
        first_pass_contribution=round(fp_contrib, 4),
        benchmark_contribution=round(bench_contrib, 4),
        reliability_contribution=round(rel_contrib, 4),
        computed_at=_iso_now(),
    )


def emit_quality_score(
    score: LocalQualityScore,
    *,
    artifact_dir: Path = Path("artifacts") / "local_quality_score",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "local_quality_score.json"
    out_path.write_text(
        json.dumps(
            {
                "raw_score": score.raw_score,
                "grade": score.grade,
                "evidence_weight": score.evidence_weight,
                "first_pass_contribution": score.first_pass_contribution,
                "benchmark_contribution": score.benchmark_contribution,
                "reliability_contribution": score.reliability_contribution,
                "computed_at": score.computed_at,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(out_path)


__all__ = ["LocalQualityScore", "compute_quality_score", "emit_quality_score"]
