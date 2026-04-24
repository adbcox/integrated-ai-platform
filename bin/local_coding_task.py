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
import subprocess
from pathlib import Path

# Add repo root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from domains.router import TaskRouter, ExecutorType


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
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip pre-flight analysis",
    )
    parser.add_argument(
        "--auto-test",
        action="store_true",
        help="Generate and run tests after successful execution",
    )

    args = parser.parse_args()

    # Get repo root
    repo_root = Path(__file__).parent.parent

    # Pre-flight analysis (unless skipped)
    if not args.skip_analysis:
        from bin.analyze_task import TaskAnalyzer

        analyzer = TaskAnalyzer(repo_root)
        can_proceed, questions = analyzer.analyze(args.description, args.files)

        if not can_proceed:
            print("⚠️  Pre-flight questions detected. Run:")
            print(f"   ./bin/analyze_task.py '{args.description}' {' '.join(args.files)}")
            print("\nOr use --skip-analysis to bypass")
            return 3

    # Validate files exist
    missing_files = []
    for file_path in args.files:
        full_path = repo_root / file_path  # repo_root already assigned above
        if not full_path.exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Error: Files not found:", file=sys.stderr)
        for f in missing_files:
            print(f"   - {f}", file=sys.stderr)
        return 1

    # Route task to optimal executor
    router = TaskRouter(repo_root)
    route = router.classify(args.description, args.files)

    # If not local, inform user and exit
    if route.executor != ExecutorType.LOCAL_AIDER:
        print(f"🔀 Task routed to: {route.executor.value}")
        print(f"📊 Confidence: {route.confidence:.0%}")
        print(f"💡 Reasoning: {route.reasoning}")
        print()
        print(f"💬 This task should use {route.executor.value} instead of local Aider.")
        print(f"   Please run it manually via Claude.ai or Claude Code.")
        return 2  # Exit code 2 = wrong executor

    # Import and execute
    try:
        from domains.coding import CodingDomain

        domain = CodingDomain()

        print(f"📝 Task: {args.description}")
        print(f"📄 Files: {', '.join(args.files)}")
        print(f"⏱️  Timeout: {args.timeout}s")
        print(f"🎯 Routed to: Local Aider (confidence: {route.confidence:.0%})")
        print(f"🤖 Model: {route.model}")
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
            model_used = result.get("model", "Unknown")
            print(f"✅ Success!")
            print(f"   Commit: {commit_hash}")
            print(f"   Model Used: {model_used}")

            # Show output summary
            output = result.get("output", "")
            if "@@" in output:  # Shows there were code changes
                print(f"   Output: {len(output)} chars captured")

            # Review the current changes before continuing.
            print()
            print("=" * 70)
            from bin.review_changes import review_current_changes

            review_result = review_current_changes(repo_root=repo_root)
            print("=" * 70)

            if not review_result.get("proceed", True):
                print("❌ Review requested fixes. Stop here and address the suggestions.")
                return 1

            # Auto-generate tests if requested
            if args.auto_test:
                print()
                print("=" * 70)
                test_result = subprocess.run(
                    [
                        sys.executable,
                        str(Path(__file__).parent / "generate_tests.py"),
                        "--commit",
                        commit_hash if commit_hash else "HEAD",
                    ],
                    cwd=repo_root,
                )
                print("=" * 70)
                if test_result.returncode != 0:
                    print("⚠️  Test generation failed")
                    return 1

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
