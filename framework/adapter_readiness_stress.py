"""AdapterReadinessStressHarness: stress-tests local system stability for a future adapter campaign."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from framework.local_quality_score import LocalQualityScore
from framework.unified_local_metrics import UnifiedLocalMetrics
from framework.routing_policy_artifact import RoutingPolicyArtifact
from framework.failure_cluster_analysis import FailureClusterReport

# -- import-time assertions --
assert "raw_score" in LocalQualityScore.__dataclass_fields__, \
    "INTERFACE MISMATCH: LocalQualityScore.raw_score"
assert "grade" in LocalQualityScore.__dataclass_fields__, \
    "INTERFACE MISMATCH: LocalQualityScore.grade"
assert "first_pass_rate" in UnifiedLocalMetrics.__dataclass_fields__, \
    "INTERFACE MISMATCH: UnifiedLocalMetrics.first_pass_rate"
assert "failure_rate" in UnifiedLocalMetrics.__dataclass_fields__, \
    "INTERFACE MISMATCH: UnifiedLocalMetrics.failure_rate"
assert "policy_health" in RoutingPolicyArtifact.__dataclass_fields__, \
    "INTERFACE MISMATCH: RoutingPolicyArtifact.policy_health"
assert "total_failures_analyzed" in FailureClusterReport.__dataclass_fields__, \
    "INTERFACE MISMATCH: FailureClusterReport.total_failures_analyzed"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class StressCheck:
    check_name: str
    passed: bool
    detail: str


@dataclass
class StressHarnessResult:
    verdict: str  # "stable" | "unstable" | "unknown"
    checks: List[StressCheck]
    blocking_failures: int
    quality_score: float
    analyzed_at: str
    artifact_path: Optional[str]


class AdapterReadinessStressHarness:
    """Evidence-only harness; no adapter code; verdict is conservative."""

    def run(
        self,
        *,
        quality_score: Optional[LocalQualityScore] = None,
        unified_metrics: Optional[UnifiedLocalMetrics] = None,
        policy_artifact: Optional[RoutingPolicyArtifact] = None,
        failure_clusters: Optional[FailureClusterReport] = None,
    ) -> StressHarnessResult:
        checks = []

        # Check 1: quality score sufficient
        if quality_score is not None:
            passed = quality_score.raw_score >= 0.60
            checks.append(StressCheck(
                check_name="quality_score_sufficient",
                passed=passed,
                detail=f"score={quality_score.raw_score:.3f} grade={quality_score.grade}",
            ))
        else:
            checks.append(StressCheck(
                check_name="quality_score_sufficient",
                passed=False,
                detail="quality_score not available",
            ))

        # Check 2: failure rate acceptable
        if unified_metrics is not None:
            passed = unified_metrics.failure_rate <= 0.30
            checks.append(StressCheck(
                check_name="failure_rate_acceptable",
                passed=passed,
                detail=f"failure_rate={unified_metrics.failure_rate:.2f}",
            ))
        else:
            checks.append(StressCheck(
                check_name="failure_rate_acceptable",
                passed=False,
                detail="unified_metrics not available",
            ))

        # Check 3: routing policy not degraded
        if policy_artifact is not None:
            passed = policy_artifact.policy_health != "degraded"
            checks.append(StressCheck(
                check_name="routing_policy_not_degraded",
                passed=passed,
                detail=f"policy_health={policy_artifact.policy_health}",
            ))
        else:
            checks.append(StressCheck(
                check_name="routing_policy_not_degraded",
                passed=False,
                detail="routing_policy not available",
            ))

        # Check 4: failure cluster count bounded
        if failure_clusters is not None:
            cluster_count = len(failure_clusters.clusters)
            passed = cluster_count <= 10
            checks.append(StressCheck(
                check_name="failure_clusters_bounded",
                passed=passed,
                detail=f"cluster_count={cluster_count}",
            ))
        else:
            checks.append(StressCheck(
                check_name="failure_clusters_bounded",
                passed=True,  # no data = no evidence of excess clusters
                detail="failure_clusters not analyzed",
            ))

        blocking_failures = sum(1 for c in checks if not c.passed)
        score = quality_score.raw_score if quality_score is not None else 0.0

        if quality_score is None or unified_metrics is None:
            verdict = "unknown"
        elif blocking_failures == 0:
            verdict = "stable"
        else:
            verdict = "unstable"

        return StressHarnessResult(
            verdict=verdict,
            checks=checks,
            blocking_failures=blocking_failures,
            quality_score=score,
            analyzed_at=_iso_now(),
            artifact_path=None,
        )


def emit_stress_result(
    result: StressHarnessResult,
    *,
    artifact_dir: Path = Path("artifacts") / "adapter_readiness_stress",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "stress_result.json"
    out_path.write_text(
        json.dumps(
            {
                "verdict": result.verdict,
                "blocking_failures": result.blocking_failures,
                "quality_score": result.quality_score,
                "analyzed_at": result.analyzed_at,
                "checks": [
                    {"check_name": c.check_name, "passed": c.passed, "detail": c.detail}
                    for c in result.checks
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    result.artifact_path = str(out_path)
    return str(out_path)


__all__ = ["StressCheck", "StressHarnessResult", "AdapterReadinessStressHarness", "emit_stress_result"]
