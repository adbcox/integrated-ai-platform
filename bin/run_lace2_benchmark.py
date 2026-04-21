#!/usr/bin/env python3
"""LACE2-P9: Run real-file benchmark and emit artifact."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace2_benchmark_runner import Lace2BenchmarkRunner

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE2"


def main() -> None:
    runner = Lace2BenchmarkRunner()
    record = runner.run()
    path = runner.emit(record, ARTIFACT_DIR)
    print(f"run_id:        {record.run_id}")
    print(f"benchmark_kind:{record.benchmark_kind}")
    print(f"total_tasks:   {record.total_tasks}")
    print(f"passed_count:  {record.passed_count}")
    print(f"pass_rate:     {record.pass_rate}")
    print(f"kind_rates:    {record.kind_pass_rates}")
    print(f"artifact:      {path}")


if __name__ == "__main__":
    main()
