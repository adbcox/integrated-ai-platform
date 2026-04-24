#!/usr/bin/env python3
"""Execute a batch of coding tasks from a file.

This script reads a task file and executes each task sequentially via Aider.

Usage:
    ./bin/batch_coding_tasks.py tasks.txt
    ./bin/batch_coding_tasks.py tasks.txt --timeout 600

Task File Format:
    description|file1.py,file2.py
    another task|target.py
    # Comments start with #
    add type hints|module.py,submodule.py

    - One task per line
    - Lines starting with # are ignored
    - Empty lines are skipped
    - Format: DESCRIPTION|FILE1,FILE2,...

Exit Codes:
    0 - All tasks succeeded
    1 - One or more tasks failed
"""

import sys
import argparse
from pathlib import Path

# Add repo root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from domains.router import TaskRouter, ExecutorType


def parse_task_file(file_path: str) -> list:
    """Parse task file and return list of (description, files) tuples."""
    tasks = []
    with open(file_path) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse task line
            if "|" not in line:
                print(f"⚠️  Warning: Line {i} missing pipe separator, skipping: {line}")
                continue

            parts = line.split("|", 1)
            description = parts[0].strip()
            files_str = parts[1].strip()

            if not description or not files_str:
                print(f"⚠️  Warning: Line {i} has empty description or files, skipping")
                continue

            files = [f.strip() for f in files_str.split(",")]
            tasks.append((description, files))

    return tasks


def main() -> int:
    """Execute batch coding tasks."""
    parser = argparse.ArgumentParser(
        prog="batch_coding_tasks.py",
        description="Execute multiple coding tasks from a file",
        add_help=True,
    )

    parser.add_argument(
        "task_file",
        help="Task file (format: description|file1,file2)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout per task in seconds (default: 300)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override model (default: qwen2.5-coder:14b)",
    )

    args = parser.parse_args()

    # Check task file exists
    if not Path(args.task_file).exists():
        print(f"❌ Error: Task file not found: {args.task_file}", file=sys.stderr)
        return 1

    # Parse tasks
    try:
        tasks = parse_task_file(args.task_file)
    except Exception as e:
        print(f"❌ Error reading task file: {e}", file=sys.stderr)
        return 1

    if not tasks:
        print("⚠️  No tasks found in file", file=sys.stderr)
        return 1

    print(f"📋 Loaded {len(tasks)} tasks from {args.task_file}")
    print()

    # Execute tasks
    try:
        from domains.coding import CodingDomain

        domain = CodingDomain()
        router = TaskRouter()
        results = []
        successful = 0
        skipped = 0

        for i, (description, files) in enumerate(tasks, 1):
            task_num = f"[{i}/{len(tasks)}]"
            print(f"{task_num} {description}")

            # Validate files exist
            repo_root = Path(__file__).parent.parent
            missing = [f for f in files if not (repo_root / f).exists()]
            if missing:
                print(
                    f"     ❌ Files not found: {', '.join(missing)}",
                    file=sys.stderr,
                )
                results.append((description, False, None, f"Files not found: {missing}"))
                continue

            # Check routing
            route = router.classify(description, files)
            if route.executor != ExecutorType.LOCAL_AIDER:
                print(f"     ⚠️  Skipped - routed to {route.executor.value} (confidence: {route.confidence:.0%})")
                results.append((description, False, None, f"Routed to {route.executor.value}"))
                skipped += 1
                continue

            # Execute task
            try:
                result = domain.execute_task(
                    task_description=description,
                    files=files,
                    model=args.model,
                    timeout_seconds=args.timeout,
                )

                if result["success"]:
                    commit = result.get("commit_hash", "")[:12]
                    print(f"     ✅ {commit}")
                    results.append((description, True, commit, None))
                    successful += 1
                else:
                    error = result.get("error", "Unknown error")
                    print(f"     ❌ {error}")
                    results.append((description, False, None, error))

            except Exception as e:
                print(f"     ❌ Exception: {e}")
                results.append((description, False, None, str(e)))

        # Summary
        print()
        print("=" * 70)
        print(f"Results: {successful}/{len(tasks)} successful, {skipped} skipped")

        if successful > 0:
            print()
            print("✅ Successful tasks:")
            for desc, success, commit, _ in results:
                if success:
                    print(f"   - {desc[:50]:50} ({commit})")

        failed = len(tasks) - successful
        if failed > 0:
            print()
            print(f"❌ Failed tasks ({failed}):")
            for desc, success, _, error in results:
                if not success:
                    error_msg = error[:40] if error else "Unknown"
                    print(f"   - {desc[:40]:40} ({error_msg})")

        print("=" * 70)

        return 0 if successful == len(tasks) else 1

    except ImportError as e:
        print(f"❌ Error: Could not import CodingDomain: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
