#!/usr/bin/env python3
"""LACE1-P11: Mine failure patterns from benchmark results and rag4 usage."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace1_benchmark_runner import Lace1BenchmarkRunner, BenchmarkRunReport
from framework.failure_pattern_miner import FailurePatternMiner

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE1"
RAG4_USAGE = REPO_ROOT / "artifacts" / "stage_rag4" / "usage.jsonl"


def main() -> None:
    runner = Lace1BenchmarkRunner()
    bench_report = runner.run()

    miner = FailurePatternMiner()
    fp_report = miner.mine(bench_report, rag4_usage_path=RAG4_USAGE)
    path = miner.emit(fp_report, ARTIFACT_DIR)

    print(f"failure_pattern_report: {path}")
    print(f"  benchmark_failures:         {fp_report.benchmark_failures}")
    print(f"  retrieval_zero_boost_count: {fp_report.retrieval_zero_boost_count}")
    print(f"  total_patterns:             {fp_report.total_patterns}")
    for p in fp_report.patterns:
        print(f"  [{p.severity}] {p.pattern_id}: frequency={p.frequency}")


if __name__ == "__main__":
    main()
