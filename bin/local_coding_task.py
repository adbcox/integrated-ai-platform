#!/usr/bin/env python3
"""Execute a single local coding task via Aider.

This script provides a CLI wrapper around CodingDomain.execute_task() for
executing individual coding modification tasks directly on the local repository.

Usage:
    ./bin/local_coding_task.py 'Add docstring to main function' myfile.py
    ./bin/local_coding_task.py 'Add type hints' file1.py file2.py file3.py
    ./bin/local_coding_task.py 'Fix error handling' --timeout 600 handler.py

Arguments:
    DESCRIPTION     Task description/instruction for Aider
    FILES           One or more files to modify (must exist in repo)

Options:
    --timeout SEC   Timeout in seconds (default: 300 = 5 minutes)
    --model MODEL   Override default model (default: qwen2.5-coder:14b)
    --help          Show this help message
"""

import sys
import argparse
from pathlib import Path

# Add repo root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def main() -> int:
    """Execute a coding task and return exit code."""
    parser = argparse.ArgumentParser(
        prog="local_coding_task.py",
        description="Execute a coding task via local Aider",
        add_help=True,
    )

    parser.add_argument(
        "description",
        help="Task description/instruction for Aider",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Files to modify (relative to repo root)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds (default: 300)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override model (default: qwen2.5-coder:14b)",
    )

    args = parser.parse_args()

    # Validate files exist
    repo_root = Path(__file__).parent.parent
    missing_files = []
    for file_path in args.files:
        full_path = repo_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Error: Files not found:", file=sys.stderr)
        for f in missing_files:
            print(f"   - {f}", file=sys.stderr)
        return 1

    # Import and execute
    try:
        from domains.coding import CodingDomain

        domain = CodingDomain()

        print(f"📝 Task: {args.description}")
        print(f"📄 Files: {', '.join(args.files)}")
        print(f"🔧 Model: {args.model or domain.model}")
        print(f"⏱️  Timeout: {args.timeout}s")
        print()
        print("Running Aider...")
        print("-" * 70)

        result = domain.execute_task(
            task_description=args.description,
            files=args.files,
            model=args.model,
            timeout_seconds=args.timeout,
        )

        print("-" * 70)
        print()

        if result["success"]:
            commit_hash = result.get("commit_hash", "")[:12]
            print(f"✅ Success!")
            print(f"   Commit: {commit_hash}")

            # Show output summary
            output = result.get("output", "")
            if "@@" in output:  # Shows there were code changes
                print(f"   Output: {len(output)} chars captured")
            return 0
        else:
            error = result.get("error", "Unknown error")
            print(f"❌ Failed: {error}")

            # Show output for debugging
            output = result.get("output", "")
            if output and len(output) < 500:
                print(f"\nOutput:\n{output}")
            return 1

    except ImportError as e:
        print(f"❌ Error: Could not import CodingDomain: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
