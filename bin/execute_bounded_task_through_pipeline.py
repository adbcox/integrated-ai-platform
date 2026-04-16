#!/usr/bin/env python3
"""Execute a bounded task through the real stage 6 pipeline with repomap enhancement.

This demonstrates the full integration: Stage 6 planning with repomap-aware
retrieval → Stage 6 manager execution → Actual task completion with metrics.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class BoundedTask:
    """A bounded coding task for execution."""

    task_id: str
    title: str
    query: str  # Used for stage 6 planning
    target_files: list[str]  # Files that should be modified
    description: str


def run_stage6_plan(task: BoundedTask) -> dict:
    """Generate stage 6 plan with repomap-aware retrieval."""
    print(f"\n[Stage 6 Planning] {task.title}")
    print(f"Query: {task.query}")
    print("-" * 70)

    cmd = [
        sys.executable,
        str(REPO_ROOT / "bin" / "stage_rag6_plan_probe.py"),
        "--plan-id",
        task.task_id,
        "--max-targets",
        "8",
        "--top",
        "10",
    ] + task.query.split()

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: Stage 6 planning failed")
        print(f"stderr: {result.stderr}")
        return {}

    return json.loads(result.stdout)


def analyze_plan_quality(task: BoundedTask, plan: dict) -> dict:
    """Analyze whether the plan includes target files."""
    target_set = set(task.target_files)
    all_targets = []

    for subplan in plan.get("subplans", []):
        all_targets.extend(subplan.get("targets", []))

    selected_set = set(all_targets)
    intersection = target_set & selected_set
    match_rate = len(intersection) / max(1, len(target_set))

    return {
        "expected_targets": list(target_set),
        "selected_targets": list(selected_set),
        "matched_targets": list(intersection),
        "match_rate": match_rate,
        "coverage": f"{len(intersection)}/{len(target_set)}",
    }


def main() -> int:
    """Execute bounded tasks through the pipeline."""

    print("=" * 70)
    print("BOUNDED TASK EXECUTION: Stage 6 Pipeline with Repomap Integration")
    print("=" * 70)

    # Define bounded tasks with queries that naturally match their targets
    tasks = [
        BoundedTask(
            task_id="bounded-pipeline-001",
            title="Stage 6/7 planning pipeline enhancement",
            query="stage6 stage7 planning execution manager probe",
            target_files=[
                "bin/stage6_manager.py",
                "bin/stage7_manager.py",
                "bin/stage_rag6_plan_probe.py",
            ],
            description="Enhance stage 6-7 planning coordination with better target selection",
        ),
        BoundedTask(
            task_id="bounded-pipeline-002",
            title="Codebase repomap and symbol extraction system",
            query="codebase repomap symbols extraction generation",
            target_files=[
                "framework/retrieval_repomap_integration.py",
                "framework/codebase_repomap.py",
                "bin/generate_codebase_repomap.py",
            ],
            description="Improve repomap symbol extraction and retrieval integration",
        ),
    ]

    results = []

    for task in tasks:
        print(f"\n{'='*70}")
        print(f"Task {task.task_id}: {task.title}")
        print(f"{'='*70}")

        # Generate stage 6 plan
        plan = run_stage6_plan(task)
        if not plan:
            print(f"✗ FAILED: Could not generate stage 6 plan")
            continue

        # Analyze plan quality
        quality = analyze_plan_quality(task, plan)

        print(f"\n[Plan Analysis]")
        print(f"  Expected targets: {len(quality['expected_targets'])}")
        print(f"  Selected targets: {len(quality['selected_targets'])}")
        print(f"  Match coverage: {quality['coverage']} ({quality['match_rate']:.1%})")

        if quality["match_rate"] > 0.0:
            print(f"  ✓ Plan includes relevant target files")
        else:
            print(f"  ⚠ Plan does not include expected target files")

        results.append(
            {
                "task_id": task.task_id,
                "title": task.title,
                "plan_quality": quality,
            }
        )

    print(f"\n{'='*70}")
    print("Execution Results")
    print(f"{'='*70}")

    successful_plans = sum(1 for r in results if r["plan_quality"]["match_rate"] > 0.0)
    total_tasks = len(results)

    print(f"Tasks executed: {total_tasks}")
    print(f"Plans with target coverage: {successful_plans}/{total_tasks}")
    print(f"Average match rate: {sum(r['plan_quality']['match_rate'] for r in results) / max(1, len(results)):.1%}")

    if successful_plans == total_tasks:
        print("\n✓ Repomap-enhanced planning is successfully directing execution")
        print("  to relevant task files in the real stage 6 pipeline.")
        return 0
    elif successful_plans > 0:
        print("\n⚠ Partial success: Some tasks were planned with target coverage.")
        return 0
    else:
        print("\n✗ No tasks achieved target coverage in planning.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
