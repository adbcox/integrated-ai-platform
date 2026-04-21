"""Standalone runner for per-task-class benchmark."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.task_class_benchmark import TaskClassBenchmarkRunner


def main() -> int:
    artifact_root = REPO_ROOT / "artifacts" / "task_class_benchmark"
    runner = TaskClassBenchmarkRunner(artifact_root=artifact_root, tasks_per_class=2)
    report = runner.run()
    print(f"\n{'='*50}")
    print(f"  Task Class Benchmark")
    print(f"{'='*50}")
    for entry in report.entries:
        print(f"  {entry.task_class:30s} pass={entry.passed}/{entry.total} ({entry.pass_rate:.0%})")
    print(f"{'='*50}")
    print(f"  Overall: {report.total_passed}/{report.total_tasks} ({report.overall_pass_rate:.0%})")
    print(f"  Artifact: {report.artifact_path}")
    print(f"{'='*50}\n")
    return 0 if report.total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
