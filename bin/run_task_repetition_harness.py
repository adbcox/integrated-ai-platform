#!/usr/bin/env python3
"""Standalone task repetition harness runner.

Usage: python3 bin/run_task_repetition_harness.py [--task-kind KIND] [--num-runs N] [--dry-run] [--artifact-dir PATH]

Runs synthetic tasks through the MVP coding loop, records outcomes to LocalMemoryStore,
and prints a summary table. Exits 0 always.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.task_repetition_harness import (
    RepetitionRunConfig,
    TaskRepetitionHarness,
    make_synthetic_repetition_tasks,
)
from framework.local_memory_store import LocalMemoryStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Run task repetition harness.")
    parser.add_argument("--task-kind", default="text_replacement")
    parser.add_argument("--num-runs", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--artifact-dir", default="artifacts/repetition_runs")
    args = parser.parse_args()

    config = RepetitionRunConfig(
        task_kind=args.task_kind,
        num_runs=args.num_runs,
        dry_run=args.dry_run,
        artifact_dir=args.artifact_dir,
    )

    with tempfile.TemporaryDirectory() as tmp:
        tasks = make_synthetic_repetition_tasks(
            task_kind=args.task_kind,
            num_tasks=args.num_runs,
            tmp_dir=Path(tmp) / "tasks",
        )

    harness = TaskRepetitionHarness()
    result = harness.run(config, tasks)

    print(f"\n{'RUN':>4} {'TASK KIND':<24} {'SUCCESS':>8} {'DURATION':>10}")
    print("-" * 52)
    for r in result.records:
        ok = "YES" if r.success else "NO"
        print(f"{r.run_index:>4} {r.task_kind:<24} {ok:>8} {r.duration_seconds:>9.4f}s")
    print("-" * 52)
    print(f"\n{result.summary_line()}")
    print()

    if not args.dry_run:
        out_dir = Path(args.artifact_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        out_file = out_dir / f"{args.task_kind}_{ts}.json"
        out_file.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Artifact: {out_file}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
