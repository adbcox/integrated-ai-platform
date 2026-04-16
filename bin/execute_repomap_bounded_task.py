#!/usr/bin/env python3
"""Execute a real bounded multi-file task using repomap-aware retrieval.

This script demonstrates the full Developer Assistance capability integrated
with the framework pipeline:
1. Use repomap to select relevant files for a task
2. Generate a realistic multi-file editing task
3. Execute through aider with proper context management
4. Measure success and capture metrics for benchmarking
"""

from __future__ import annotations  # stage7-op

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.retrieval_repomap_integration import RepomapAwareRetrieval


@dataclass
class BoundedTask:
    """Specification for a bounded multi-file coding task."""

    task_id: str
    title: str
    description: str
    query: str
    query_tokens: list[str]
    max_targets: int
    expected_edits: int  # How many files we expect to edit
    aider_message: str  # The instruction for aider


def load_repomap() -> dict:
    """Load the generated repomap."""
    repomap_path = REPO_ROOT / "artifacts" / "repomap" / "latest.json"
    if not repomap_path.exists():
        raise FileNotFoundError(f"Repomap not found at {repomap_path}")
    return json.loads(repomap_path.read_text(encoding="utf-8"))


def select_targets_for_task(task: BoundedTask) -> list[str]:
    """Use repomap-aware retrieval to select files for the task."""
    repomap_path = REPO_ROOT / "artifacts" / "repomap" / "latest.json"
    retrieval = RepomapAwareRetrieval(repomap_path)

    targets = retrieval.select_targets(
        query=task.query,
        query_tokens=task.query_tokens,
        max_targets=task.max_targets,
        include_dependents=True,
    )

    selected_paths = [t.path for t in targets]

    # Verify scope is reasonable
    scope = retrieval.estimate_context_scope(targets)
    if not scope["within_budget"]:
        raise RuntimeError(
            f"Task context exceeds budget: {scope['estimated_tokens']} tokens > 32K"
        )

    return selected_paths


def execute_task_with_aider(task: BoundedTask, target_files: list[str]) -> dict:
    """Execute the task using aider on selected files."""

    # Prepare file arguments for aider
    file_args = [str(REPO_ROOT / f) for f in target_files]

    # Build aider command
    aider_cmd = [
        sys.executable,
        "-m",
        "aider",
        "--no-check-update",
        "--no-show-release-notes",
        "--analytics-disable",
        "--no-auto-commits",
        "--no-dirty-commits",
        "--yes-always",
        "--no-fancy-input",
        "--no-browser",
        "--timeout",
        "30",
        "--message",
        task.aider_message,
    ] + file_args

    print(f"\n[Executing Task] {task.title}")
    print(f"Task ID: {task.task_id}")
    print(f"Files: {len(target_files)} targets")
    print(f"Command: aider {' '.join(file_args)}")

    result = subprocess.run(aider_cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=120)

    success = result.returncode == 0

    metrics = {
        "task_id": task.task_id,
        "title": task.title,
        "status": "success" if success else "failed",
        "exit_code": result.returncode,
        "target_count": len(target_files),
        "expected_edits": task.expected_edits,
        "aider_output_lines": len(result.stdout.split("\n")),
        "aider_error_lines": len(result.stderr.split("\n")) if result.stderr else 0,
    }

    return metrics


def main() -> int:
    """Execute a bounded multi-file task and report metrics."""

    print("=" * 70)
    print("BOUNDED MULTI-FILE TASK EXECUTION: Repomap-Aware Retrieval")
    print("=" * 70)

    # Verify repomap exists
    repomap_path = REPO_ROOT / "artifacts" / "repomap" / "latest.json"
    if not repomap_path.exists():
        print("ERROR: Repomap not found. Run: python3 bin/generate_codebase_repomap.py")
        return 1

    print(f"\n[1/4] Repomap verified: {repomap_path}")

    # Define a bounded task: improve documentation in stage managers
    task = BoundedTask(
        task_id="bounded-001",
        title="Add docstring improvements to stage managers",
        description="Enhance docstrings in stage managers to document RAG integration points",
        query="stage manager rag retrieval integration documentation",
        query_tokens=["stage", "manager", "rag", "retrieval", "integration", "documentation"],
        max_targets=8,
        expected_edits=3,
        aider_message="Add/improve docstrings in stage managers to document RAG planning and retrieval integration points. Keep changes minimal and focused on documentation only.",
    )

    print(f"\n[2/4] Task prepared: {task.title}")
    print(f"Query: {task.query}")

    # Select targets using repomap
    print("\n[3/4] Selecting targets with repomap-aware retrieval...")
    try:
        targets = select_targets_for_task(task)
        print(f"Selected {len(targets)} files:")
        for f in targets:
            print(f"  - {f}")
    except Exception as e:
        print(f"ERROR selecting targets: {e}")
        return 1

    # Execute task with aider
    print("\n[4/4] Executing task with aider...")
    try:
        metrics = execute_task_with_aider(task, targets)
        print("\n✓ Task execution complete!")
        print(f"\nMetrics:")
        for key, value in metrics.items():
            if key != "task_id":
                print(f"  {key}: {value}")

        return 0 if metrics["status"] == "success" else 1

    except Exception as e:
        print(f"ERROR executing task: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
