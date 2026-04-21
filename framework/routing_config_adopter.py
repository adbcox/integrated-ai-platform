"""RoutingConfigAdopter — derives per-task-class threshold recommendations from extended autonomy metrics.

Inspection gate output:
  route_task sig: (task_class, *, memory_store=None, allow_external=False, force_profile=None, routing_config=None) -> RoutingDecision
  routing_config parameter present: True
  ExtendedAutonomyMetrics fields: generated_at, total_task_classes, task_class_breakdown,
    overall_successes, overall_failures, overall_failure_rate, overall_first_pass_rate,
    dominant_error_type, error_type_distribution, min_attempts_threshold, max_failure_rate_threshold
  TaskClassMetricsExtended fields: task_class, total_attempts, successes, failures, failure_rate,
    first_pass_rate, dominant_error_type, error_type_distribution
  RoutingConfig fields: overrides, global_threshold
  TaskRoutingOverride fields: task_class, degraded_failure_rate_threshold
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.autonomy_metrics_extended import ExtendedAutonomyMetrics, TaskClassMetricsExtended
from framework.routing_config import DEFAULT_ROUTING_CONFIG, RoutingConfig, TaskRoutingOverride

assert hasattr(ExtendedAutonomyMetrics, "__dataclass_fields__"), "INTERFACE MISMATCH: ExtendedAutonomyMetrics not dataclass"
assert hasattr(RoutingConfig, "__dataclass_fields__"), "INTERFACE MISMATCH: RoutingConfig not dataclass"
assert hasattr(TaskRoutingOverride, "__dataclass_fields__"), "INTERFACE MISMATCH: TaskRoutingOverride not dataclass"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "routing_adoption"
_BUFFER = 0.05
_MIN_ATTEMPTS_FOR_RECOMMENDATION = 5


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class AdoptionRecommendation:
    task_class: str
    observed_failure_rate: float
    suggested_threshold: float
    reason: str
    has_recommendation: bool


@dataclass
class RoutingAdoptionResult:
    recommendations: list
    updated_config: RoutingConfig
    generated_at: str
    total_classes_considered: int
    classes_with_recommendation: int
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "generated_at": self.generated_at,
            "total_classes_considered": self.total_classes_considered,
            "classes_with_recommendation": self.classes_with_recommendation,
            "recommendations": [
                {
                    "task_class": r.task_class,
                    "observed_failure_rate": round(r.observed_failure_rate, 4),
                    "suggested_threshold": round(r.suggested_threshold, 4),
                    "reason": r.reason,
                    "has_recommendation": r.has_recommendation,
                }
                for r in self.recommendations
            ],
        }


def save_adoption_result(result: RoutingAdoptionResult, *, artifact_dir: Optional[Path] = None, dry_run: bool = False) -> RoutingAdoptionResult:
    if dry_run:
        return result
    out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "routing_adoption.json"
    out_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    result.artifact_path = str(out_path)
    return result


class RoutingConfigAdopter:
    """Derives per-task-class routing threshold recommendations from ExtendedAutonomyMetrics."""

    def adopt(
        self,
        metrics: ExtendedAutonomyMetrics,
        *,
        base_config: Optional[RoutingConfig] = None,
        buffer: float = _BUFFER,
        min_attempts: int = _MIN_ATTEMPTS_FOR_RECOMMENDATION,
    ) -> RoutingAdoptionResult:
        cfg = base_config if base_config is not None else DEFAULT_ROUTING_CONFIG
        recommendations = []
        override_map = {}

        for class_metrics in metrics.task_class_breakdown:
            if not isinstance(class_metrics, dict):
                try:
                    tc = class_metrics.task_class
                    attempts = class_metrics.total_attempts
                    rate = class_metrics.failure_rate
                except AttributeError:
                    continue
            else:
                tc = class_metrics.get("task_class", "")
                attempts = class_metrics.get("total_attempts", 0)
                rate = class_metrics.get("failure_rate", 0.0)

            if attempts < min_attempts:
                rec = AdoptionRecommendation(
                    task_class=tc,
                    observed_failure_rate=rate,
                    suggested_threshold=cfg.global_threshold,
                    reason=f"insufficient attempts ({attempts} < {min_attempts})",
                    has_recommendation=False,
                )
            else:
                suggested = min(rate + buffer, 0.99)
                rec = AdoptionRecommendation(
                    task_class=tc,
                    observed_failure_rate=rate,
                    suggested_threshold=suggested,
                    reason=f"observed_rate={rate:.3f} + buffer={buffer:.2f}",
                    has_recommendation=True,
                )
                override_map[tc] = TaskRoutingOverride(
                    task_class=tc,
                    degraded_failure_rate_threshold=suggested,
                )
            recommendations.append(rec)

        new_overrides = list(override_map.values())
        updated_config = RoutingConfig(
            overrides=new_overrides,
            global_threshold=cfg.global_threshold,
        )

        return RoutingAdoptionResult(
            recommendations=recommendations,
            updated_config=updated_config,
            generated_at=_iso_now(),
            total_classes_considered=len(recommendations),
            classes_with_recommendation=len(new_overrides),
        )


__all__ = ["AdoptionRecommendation", "RoutingAdoptionResult", "RoutingConfigAdopter", "save_adoption_result"]
