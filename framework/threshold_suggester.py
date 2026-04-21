"""ThresholdSuggester: derives advisory threshold suggestions from quality score + readiness + routing config."""
from __future__ import annotations

import inspect as _inspect
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from framework.local_quality_score import LocalQualityScore
from framework.task_class_readiness import TaskClassReadinessReport
from framework.routing_config import RoutingConfig

# -- import-time assertions via inspection --
_quality_fields = set(LocalQualityScore.__dataclass_fields__.keys())
assert "raw_score" in _quality_fields, "INTERFACE MISMATCH: LocalQualityScore.raw_score"
assert "grade" in _quality_fields, "INTERFACE MISMATCH: LocalQualityScore.grade"

_config_fields = set(RoutingConfig.__dataclass_fields__.keys())
# Find equivalent threshold-bearing fields (not hardcoded to exact name)
_THRESHOLD_FIELD = (
    "global_threshold"
    if "global_threshold" in _config_fields
    else next((f for f in _config_fields if "threshold" in f.lower()), None)
)
assert _THRESHOLD_FIELD is not None, \
    "INTERFACE MISMATCH: RoutingConfig missing threshold-bearing field"

assert "overall_verdict" in TaskClassReadinessReport.__dataclass_fields__, \
    "INTERFACE MISMATCH: TaskClassReadinessReport.overall_verdict"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class ThresholdSuggestion:
    field: str
    current_value: float
    suggested_value: float
    rationale: str


@dataclass(frozen=True)
class ThresholdSuggestions:
    suggestions: Tuple[ThresholdSuggestion, ...]
    overall_signal: str
    computed_at: str


def derive_threshold_suggestions(
    quality_score: LocalQualityScore,
    *,
    readiness_report: Optional[TaskClassReadinessReport] = None,
    current_config: Optional[RoutingConfig] = None,
) -> ThresholdSuggestions:
    current_threshold = 0.5
    if current_config is not None:
        current_threshold = float(getattr(current_config, _THRESHOLD_FIELD, 0.5))

    suggestions = []
    score = quality_score.raw_score
    readiness = "unknown" if readiness_report is None else readiness_report.overall_verdict

    # Suggest a threshold based on quality score
    if score >= 0.80 and readiness in ("ready", "unknown"):
        suggested = max(current_threshold, round(score * 0.85, 2))
        if abs(suggested - current_threshold) > 0.02:
            suggestions.append(ThresholdSuggestion(
                field=_THRESHOLD_FIELD,
                current_value=current_threshold,
                suggested_value=suggested,
                rationale=f"Quality score {score:.2f} (grade={quality_score.grade}) supports higher threshold",
            ))
    elif score < 0.55 or readiness == "not_ready":
        suggested = min(current_threshold, round(score * 0.75, 2))
        if abs(suggested - current_threshold) > 0.02:
            suggestions.append(ThresholdSuggestion(
                field=_THRESHOLD_FIELD,
                current_value=current_threshold,
                suggested_value=suggested,
                rationale=f"Quality score {score:.2f} (grade={quality_score.grade}) suggests lower threshold",
            ))

    if readiness == "not_ready":
        overall_signal = "reduce_threshold"
    elif score >= 0.80 and readiness == "ready":
        overall_signal = "increase_threshold"
    elif score >= 0.55:
        overall_signal = "hold"
    else:
        overall_signal = "reduce_threshold"

    return ThresholdSuggestions(
        suggestions=tuple(suggestions),
        overall_signal=overall_signal,
        computed_at=_iso_now(),
    )


def emit_threshold_suggestions(
    suggestions: ThresholdSuggestions,
    *,
    artifact_dir: Path = Path("artifacts") / "threshold_suggestions",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "threshold_suggestions.json"
    out_path.write_text(
        json.dumps(
            {
                "overall_signal": suggestions.overall_signal,
                "suggestions": [
                    {"field": s.field, "current_value": s.current_value,
                     "suggested_value": s.suggested_value, "rationale": s.rationale}
                    for s in suggestions.suggestions
                ],
                "computed_at": suggestions.computed_at,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(out_path)


__all__ = ["ThresholdSuggestion", "ThresholdSuggestions", "derive_threshold_suggestions", "emit_threshold_suggestions"]
