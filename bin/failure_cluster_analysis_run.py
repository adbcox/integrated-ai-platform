"""Standalone runner for failure cluster analysis."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.failure_cluster_analysis import FailureClusterAnalyzer, emit_failure_clusters


def main() -> int:
    analyzer = FailureClusterAnalyzer()
    report = analyzer.analyze()
    artifact_dir = REPO_ROOT / "artifacts" / "failure_clusters"
    out_path = emit_failure_clusters(report, artifact_dir=artifact_dir)

    print(f"\n{'='*50}")
    print(f"  Failure Cluster Analysis")
    print(f"{'='*50}")
    print(f"  Total failures analyzed : {report.total_failures_analyzed}")
    print(f"  Clusters identified     : {len(report.clusters)}")
    print(f"  Top cluster             : {report.top_cluster_key or 'none'}")
    print(f"  Artifact                : {out_path}")
    print(f"{'='*50}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
