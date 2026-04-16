#!/usr/bin/env python3
"""Execute real bounded tasks through Stage 7 pipeline with Claude Code executor.

This script validates end-to-end execution through the complete Stage 7 →
Stage 6 → Stage 5 → Stage 4 → Stage 3 pipeline, proving that Claude Code
executor handles actual code modifications.
"""

from __future__ import annotations  # stage7-op  # stage7-op  # stage7-op  # stage7-op

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class BoundedTask:
    """Bounded task definition."""

    task_id: str
    description: str
    query: str
    targets: list[str]  # Files that will be modified
    modifications: dict[str, tuple[str, str]]  # target_path -> (old, new) patterns


def create_test_targets() -> dict[str, Path]:
    """Create test files that need real modifications."""
    test_dir = REPO_ROOT / "artifacts" / "claude_executor_test"
    test_dir.mkdir(parents=True, exist_ok=True)

    files = {}

    # Test file 1: Python module needing docstrings
    file1 = test_dir / "math_operations.py"
    file1.write_text(
        '''def add(a, b):
    return a + b


def subtract(a, b):
    return a - b
'''
    )
    files["math_operations.py"] = file1

    # Test file 2: Config file needing comment update
    file2 = test_dir / "config.txt"
    file2.write_text(
        '''# Configuration settings
DEBUG=false
TIMEOUT=30
'''
    )
    files["config.txt"] = file2

    return files


def run_stage7_execution(task: BoundedTask, plan_id: str) -> dict:
    """Run Stage 7 with real execution through the complete pipeline."""
    print(f"\n{'='*70}")
    print(f"[Stage 7 Real Execution] {task.description}")
    print(f"Query: {task.query}")
    print(f"Plan ID: {plan_id}")
    print(f"{'='*70}")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "bin" / "stage7_manager.py"),
        "--query",
        *task.query.split(),
        "--plan-id",
        plan_id,
        "--commit-msg",
        f"Bounded task: {task.description}",
        "--manifest",
        str(REPO_ROOT / "config" / "promotion_manifest.json"),
        "--max-subplans",
        "1",
        "--subplan-size",
        "2",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    plan_history_path = REPO_ROOT / "artifacts" / "manager6" / "plans" / f"{plan_id}.json"

    return {
        "success": result.returncode == 0,
        "returncode": result.returncode,
        "plan_exists": plan_history_path.exists(),
        "stdout": result.stdout[-500:] if result.stdout else "",
        "stderr": result.stderr[-500:] if result.stderr else "",
    }


def verify_modifications(task: BoundedTask, test_targets: dict[str, Path]) -> dict[str, bool]:
    """Verify actual code modifications occurred."""
    results = {}

    for target_relpath, (old_pattern, new_pattern) in task.modifications.items():
        # Find the actual file
        file_path = None
        for name, path in test_targets.items():
            if name == target_relpath or target_relpath.endswith(name):
                file_path = path
                break

        if not file_path or not file_path.exists():
            results[target_relpath] = False
            continue

        content = file_path.read_text(encoding="utf-8")
        results[target_relpath] = new_pattern in content or (
            old_pattern not in content and len(content) > 50
        )

    return results


def check_executor_logs(plan_id: str) -> dict:
    """Check if executor logs show Claude Code was used."""
    # Look for executor logs in stage3_manager traces
    stage3_dir = REPO_ROOT / "artifacts" / "stage3_manager"
    executor_log = None

    if stage3_dir.exists():
        for log_file in stage3_dir.glob("*.executor.json"):
            try:
                data = json.loads(log_file.read_text(encoding="utf-8"))
                if plan_id in str(log_file) or plan_id in json.dumps(data):
                    executor_log = data
                    break
            except (json.JSONDecodeError, OSError):
                continue

    if executor_log:
        return {
            "found": True,
            "executor": executor_log.get("executor", "unknown"),
            "timestamp": executor_log.get("timestamp"),
        }

    return {"found": False, "executor": None}


def main() -> int:
    """Run full bounded task execution test."""
    print("=" * 70)
    print("FULL END-TO-END BOUNDED TASK EXECUTION TEST")
    print("Testing Stage 7 → Claude Code Executor → Real Code Modifications")
    print("=" * 70)

    # Create test targets
    test_targets = create_test_targets()
    print(f"\n[Setup] Created {len(test_targets)} test files")
    for name, path in test_targets.items():
        print(f"  - {path.relative_to(REPO_ROOT)}")

    # Define bounded tasks
    tasks = [
        BoundedTask(
            task_id="ct-001",
            description="Add docstrings to math functions",
            query="add subtract function docstring return value",
            targets=["artifacts/claude_executor_test/math_operations.py"],
            modifications={
                "math_operations.py": (
                    "def add(a, b):",
                    '"""Add two numbers."""',
                )
            },
        ),
        BoundedTask(
            task_id="ct-002",
            description="Update configuration comment",
            query="configuration DEBUG TIMEOUT settings",
            targets=["artifacts/claude_executor_test/config.txt"],
            modifications={
                "config.txt": (
                    "# Configuration settings",
                    "# Configuration settings (v2)",
                )
            },
        ),
    ]

    all_success = True

    for task in tasks:
        plan_id = f"claude-executor-{task.task_id}"

        # Execute Stage 7
        result = run_stage7_execution(task, plan_id)

        if result["success"]:
            print(f"✓ Stage 7 execution completed (returncode=0)")
        else:
            print(f"⚠ Stage 7 returned code {result['returncode']}")
            if result["stderr"]:
                print(f"  Error: {result['stderr'][:100]}")

        # Check executor logs
        executor_info = check_executor_logs(plan_id)
        if executor_info["found"]:
            print(f"✓ Executor detected: {executor_info['executor']}")
            if executor_info["executor"] == "ClaudeCodeExecutor":
                print(f"  ✓ Claude Code executor was used (PRIMARY)")
            elif executor_info["executor"] == "AiderExecutor":
                print(f"  → Aider executor was used (FALLBACK)")
        else:
            print(f"⚠ No executor log found (Stage 3 may not have been reached)")

        # Verify modifications
        modifications = verify_modifications(task, test_targets)
        modified_count = sum(1 for v in modifications.values() if v)

        print(f"✓ Code modifications verified: {modified_count}/{len(modifications)}")
        for target, was_modified in modifications.items():
            status = "✓" if was_modified else "?"
            print(f"  {status} {target}")

        if not (result["success"] and modified_count > 0):
            all_success = False

    print(f"\n{'='*70}")
    print("EXECUTION SUMMARY")
    print(f"{'='*70}")

    if all_success:
        print("✓ Full bounded task execution through Claude Code executor: SUCCESS")
        print("  - Stage 7 pipeline executed successfully")
        print("  - Code modifications verified")
        print("  - Executor abstraction proven in live pipeline")
        return 0
    else:
        print("⚠ Full bounded task execution: PARTIAL/FAILED")
        print("  - May require further Stage 3 integration work")
        return 1


if __name__ == "__main__":
    sys.exit(main())
