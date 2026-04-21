"""RoutingPolicyArtifact: combines routing config, threshold suggestions, and readiness."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.routing_config import RoutingConfig, DEFAULT_ROUTING_CONFIG
from framework.threshold_suggester import ThresholdSuggestions
from framework.task_class_readiness import TaskClassReadinessReport

# -- import-time assertions --
assert "global_threshold" in RoutingConfig.__dataclass_fields__ or \
    any("threshold" in f.lower() for f in RoutingConfig.__dataclass_fields__), \
    "INTERFACE MISMATCH: RoutingConfig missing threshold field"
assert "overall_signal" in ThresholdSuggestions.__dataclass_fields__, \
    "INTERFACE MISMATCH: ThresholdSuggestions.overall_signal"
assert "overall_verdict" in TaskClassReadinessReport.__dataclass_fields__, \
    "INTERFACE MISMATCH: TaskClassReadinessReport.overall_verdict"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class RoutingPolicyArtifact:
    current_threshold: float
    overall_signal: str
    readiness_verdict: str
    suggestions_count: int
    policy_health: str
    built_at: str


def build_routing_policy_artifact(
    *,
    routing_config: Optional[RoutingConfig] = None,
    threshold_suggestions: Optional[ThresholdSuggestions] = None,
    readiness_report: Optional[TaskClassReadinessReport] = None,
) -> RoutingPolicyArtifact:
    cfg = routing_config if routing_config is not None else DEFAULT_ROUTING_CONFIG
    current_threshold = float(getattr(cfg, "global_threshold", 0.5))

    overall_signal = "unknown"
    suggestions_count = 0
    if threshold_suggestions is not None:
        overall_signal = threshold_suggestions.overall_signal
        suggestions_count = len(threshold_suggestions.suggestions)

    readiness_verdict = "unknown"
    if readiness_report is not None:
        readiness_verdict = readiness_report.overall_verdict

    # Conservative policy_health
    if readiness_verdict == "not_ready":
        policy_health = "degraded"
    elif readiness_verdict == "unknown" or overall_signal == "unknown":
        policy_health = "unknown"
    elif overall_signal == "reduce_threshold":
        policy_health = "degraded"
    elif readiness_verdict == "ready" and overall_signal in ("hold", "increase_threshold"):
        policy_health = "healthy"
    else:
        policy_health = "marginal"

    return RoutingPolicyArtifact(
        current_threshold=current_threshold,
        overall_signal=overall_signal,
        readiness_verdict=readiness_verdict,
        suggestions_count=suggestions_count,
        policy_health=policy_health,
        built_at=_iso_now(),
    )


def emit_routing_policy(
    artifact: RoutingPolicyArtifact,
    *,
    artifact_dir: Path = Path("artifacts") / "routing_policy",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "routing_policy.json"
    out_path.write_text(
        json.dumps(
            {
                "current_threshold": artifact.current_threshold,
                "overall_signal": artifact.overall_signal,
                "readiness_verdict": artifact.readiness_verdict,
                "suggestions_count": artifact.suggestions_count,
                "policy_health": artifact.policy_health,
                "built_at": artifact.built_at,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(out_path)


__all__ = ["RoutingPolicyArtifact", "build_routing_policy_artifact", "emit_routing_policy"]
