#!/usr/bin/env python3
"""LACE1-P10: Run the LACE1 synthetic baseline benchmark."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace1_benchmark_runner import Lace1BenchmarkRunner

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE1"


def main() -> None:
    runner = Lace1BenchmarkRunner()
    report = runner.run()
    path = runner.emit(report, ARTIFACT_DIR)

    print(f"benchmark_kind: {report.benchmark_kind}")
    print(f"total_tasks:    {report.total_tasks}")
    print(f"passed:         {report.passed}")
    print(f"failed:         {report.failed}")
    print(f"pass_rate:      {report.pass_rate:.3f}")
    print(f"artifact:       {path}")

    if report.failed > 0:
        print("\nFailed tasks:")
        for r in report.task_results:
            if not r.passed:
                print(f"  {r.task_id}: {r.failure_reason}")
        sys.exit(1)


if __name__ == "__main__":
    main()
