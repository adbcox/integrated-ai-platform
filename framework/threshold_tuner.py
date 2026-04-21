"""ThresholdTuner — derives per-task-class routing threshold recommendations from metrics and batch evidence.

Inspection gate output:
  TaskClassMetricsExtended fields: task_class, total_attempts, successes, failures, failure_rate,
    first_pass_rate, dominant_error_type, error_type_distribution
  BatchRunResult fields: config, kind_results, total_kinds, total_runs, total_successes,
    total_failures, generated_at, artifact_path
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.autonomy_metrics_extended import ExtendedAutonomyMetrics, TaskClassMetricsExtended
from framework.evidence_accumulation_batch import BatchRunResult

assert hasattr(ExtendedAutonomyMetrics, "__dataclass_fields__"), "INTERFACE MISMATCH: ExtendedAutonomyMetrics not dataclass"
assert hasattr(BatchRunResult, "__dataclass_fields__"), "INTERFACE MISMATCH: BatchRunResult not dataclass"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "threshold_tuning"
_MIN_COMBINED_ATTEMPTS = 5
_BUFFER = 0.05
_MAX_THRESHOLD = 0.95


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ThresholdRecommendation:
    task_class: str
    observed_failure_rate: float
    batch_failure_rate: float
    suggested_threshold: float
    confidence: float
    reason: str
    has_recommendation: bool

    def to_dict(self) -> dict:
        return {
            "task_class": self.task_class,
            "observed_failure_rate": round(self.observed_failure_rate, 4),
            "batch_failure_rate": round(self.batch_failure_rate, 4),
            "suggested_threshold": round(self.suggested_threshold, 4),
            "confidence": round(self.confidence, 4),
            "reason": self.reason,
            "has_recommendation": self.has_recommendation,
        }


@dataclass
class ThresholdTuningResult:
    recommendations: list
    total_classes: int
    classes_with_recommendation: int
    generated_at: str
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "generated_at": self.generated_at,
            "total_classes": self.total_classes,
            "classes_with_recommendation": self.classes_with_recommendation,
            "recommendations": [r.to_dict() for r in self.recommendations],
        }


def tune_thresholds(
    metrics: ExtendedAutonomyMetrics,
    batch_result: Optional[BatchRunResult] = None,
    *,
    buffer: float = _BUFFER,
    min_attempts: int = _MIN_COMBINED_ATTEMPTS,
) -> ThresholdTuningResult:
    # Build batch lookup: task_kind -> (total_runs, failures)
    batch_by_kind: dict = {}
    if batch_result is not None:
        for kr in batch_result.kind_results:
            batch_by_kind[kr.task_kind] = {
                "total_runs": kr.total_runs,
                "failures": kr.failure_count,
            }

    recommendations = []
    for class_metrics in metrics.task_class_breakdown:
        tc = class_metrics.task_class
        live_attempts = class_metrics.total_attempts
        live_rate = class_metrics.failure_rate

        batch_info = batch_by_kind.get(tc, {})
        batch_runs = batch_info.get("total_runs", 0)
        batch_failures = batch_info.get("failures", 0)
        batch_rate = batch_failures / batch_runs if batch_runs > 0 else 0.0

        combined_attempts = live_attempts + batch_runs
        confidence = min(combined_attempts / 20.0, 1.0)

        if combined_attempts < min_attempts:
            rec = ThresholdRecommendation(
                task_class=tc,
                observed_failure_rate=live_rate,
                batch_failure_rate=batch_rate,
                suggested_threshold=0.6,
                confidence=confidence,
                reason=f"insufficient combined evidence ({combined_attempts} < {min_attempts})",
                has_recommendation=False,
            )
        else:
            blended = (live_rate * live_attempts + batch_rate * batch_runs) / combined_attempts if combined_attempts > 0 else live_rate
            suggested = min(blended + buffer, _MAX_THRESHOLD)
            rec = ThresholdRecommendation(
                task_class=tc,
                observed_failure_rate=live_rate,
                batch_failure_rate=batch_rate,
                suggested_threshold=suggested,
                confidence=confidence,
                reason=f"blended_rate={blended:.3f} + buffer={buffer:.2f} confidence={confidence:.2f}",
                has_recommendation=True,
            )
        recommendations.append(rec)

    classes_with_rec = sum(1 for r in recommendations if r.has_recommendation)
    return ThresholdTuningResult(
        recommendations=recommendations,
        total_classes=len(recommendations),
        classes_with_recommendation=classes_with_rec,
        generated_at=_iso_now(),
    )


def save_tuning_result(
    result: ThresholdTuningResult,
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> ThresholdTuningResult:
    if dry_run:
        return result
    out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "threshold_tuning_result.json"
    out_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    result.artifact_path = str(out_path)
    return result


__all__ = ["ThresholdRecommendation", "ThresholdTuningResult", "tune_thresholds", "save_tuning_result"]
