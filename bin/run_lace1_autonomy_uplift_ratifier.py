#!/usr/bin/env python3
"""LACE1-P12: Ratify autonomy uplift evidence from benchmark + failure mining."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace1_benchmark_runner import Lace1BenchmarkRunner
from framework.failure_pattern_miner import FailurePatternMiner
from framework.autonomy_uplift_ratifier import AutonomyUpliftRatifier

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE1"
RAG4_USAGE = REPO_ROOT / "artifacts" / "stage_rag4" / "usage.jsonl"


def main() -> None:
    bench_report = Lace1BenchmarkRunner().run()
    fp_report = FailurePatternMiner().mine(bench_report, rag4_usage_path=RAG4_USAGE)

    ratifier = AutonomyUpliftRatifier()
    record = ratifier.ratify(bench_report, fp_report)
    path = ratifier.emit(record, ARTIFACT_DIR)

    print(f"verdict:        {record.verdict}")
    print(f"criteria_met:   {record.criteria_met}/{record.criteria_total}")
    print(f"artifact:       {path}")
    print(f"\nbenchmark_limitations ({len(record.benchmark_limitations)}):")
    for lim in record.benchmark_limitations:
        print(f"  - {lim}")


if __name__ == "__main__":
    main()
