#!/usr/bin/env python3
"""Extended autonomy metrics reporter.

Usage: python3 bin/autonomy_metrics_report.py [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.autonomy_metrics_extended import collect_extended_metrics, save_extended_metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Print extended autonomy metrics.")
    parser.add_argument("--artifact-dir", default="artifacts/autonomy_metrics")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    metrics = collect_extended_metrics()

    print(f"\n{'TASK CLASS':<28} {'ATTEMPTS':>9} {'PASS':>6} {'FAIL':>6} {'FAIL%':>8} {'FPR%':>8} {'DOM ERR'}")
    print("-" * 90)
    for m in metrics.task_class_breakdown:
        print(
            f"{m.task_class:<28} "
            f"{m.total_attempts:>9} "
            f"{m.successes:>6} "
            f"{m.failures:>6} "
            f"{m.failure_rate:.1%}".rjust(8) + " "
            f"{m.first_pass_rate:.1%}".rjust(8) + " "
            f"{m.dominant_error_type or '-'}"
        )
    print("-" * 90)
    print(
        f"{'OVERALL':<28} "
        f"{metrics.overall_successes + metrics.overall_failures:>9} "
        f"{metrics.overall_successes:>6} "
        f"{metrics.overall_failures:>6} "
        f"{metrics.overall_failure_rate:.1%}".rjust(8) + " "
        f"{metrics.overall_first_pass_rate:.1%}".rjust(8)
    )
    print()
    print(metrics.threshold_report())
    print()

    path = save_extended_metrics(metrics, artifact_dir=Path(args.artifact_dir), dry_run=args.dry_run)
    if path:
        print(f"Artifact: {path}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
