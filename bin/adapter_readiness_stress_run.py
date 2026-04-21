"""Standalone runner for adapter readiness stress harness."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.adapter_readiness_stress import AdapterReadinessStressHarness, emit_stress_result
from framework.local_quality_score import compute_quality_score
from framework.unified_local_metrics import compute_unified_metrics
from framework.routing_policy_artifact import build_routing_policy_artifact
from framework.failure_cluster_analysis import FailureClusterAnalyzer


def main() -> int:
    quality_score = None
    unified_metrics = None
    policy_artifact = None
    failure_clusters = None

    try:
        quality_score = compute_quality_score()
    except Exception as e:
        print(f"  [warn] quality_score unavailable: {e}")

    try:
        unified_metrics = compute_unified_metrics()
    except Exception as e:
        print(f"  [warn] unified_metrics unavailable: {e}")

    try:
        policy_artifact = build_routing_policy_artifact()
    except Exception as e:
        print(f"  [warn] routing_policy unavailable: {e}")

    try:
        failure_clusters = FailureClusterAnalyzer().analyze()
    except Exception as e:
        print(f"  [warn] failure_clusters unavailable: {e}")

    harness = AdapterReadinessStressHarness()
    result = harness.run(
        quality_score=quality_score,
        unified_metrics=unified_metrics,
        policy_artifact=policy_artifact,
        failure_clusters=failure_clusters,
    )

    artifact_dir = REPO_ROOT / "artifacts" / "adapter_readiness_stress"
    out_path = emit_stress_result(result, artifact_dir=artifact_dir)

    print(f"\n{'='*55}")
    print(f"  Adapter Readiness Stress Report")
    print(f"{'='*55}")
    print(f"  Verdict           : {result.verdict}")
    print(f"  Blocking failures : {result.blocking_failures}")
    print(f"  Quality score     : {result.quality_score:.3f}")
    print(f"  Analyzed at       : {result.analyzed_at}")
    print(f"{'='*55}")
    for c in result.checks:
        status = "PASS" if c.passed else "FAIL"
        print(f"  [{status}] {c.check_name}: {c.detail}")
    print(f"{'='*55}")
    print(f"  Artifact: {out_path}")
    print(f"{'='*55}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
