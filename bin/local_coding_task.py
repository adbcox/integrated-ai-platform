#!/usr/bin/env python3
"""Execute a single local coding task via Aider.

This script provides a CLI wrapper around CodingDomain.execute_task() for
executing individual coding modification tasks directly on the local repository.

Usage:
    ./bin/local_coding_task.py 'Add docstring to main function' myfile.py
    ./bin/local_coding_task.py 'Add error handling to domains/media.py health_check method'
    ./bin/local_coding_task.py 'Add type hints' file1.py file2.py file3.py
    ./bin/local_coding_task.py 'Fix error handling' --timeout 600 handler.py

Arguments:
    DESCRIPTION     Task description/instruction for Aider
    FILES           Optional files to modify; extracted from description if omitted

Options:
    --timeout SEC   Timeout in seconds (default: 300 = 5 minutes)
    --model MODEL   Override default model (default: qwen2.5-coder:14b)
    --help          Show this help message
"""

import sys
import argparse
import subprocess
import re
from pathlib import Path

# Add repo root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from domains.router import TaskRouter, ExecutorType


FILE_PATTERN = re.compile(r"\b([A-Za-z0-9_./-]+\.py)\b")
SYMBOL_HINT_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s+(?:method|function|class|symbol)\b", re.IGNORECASE)
REVERSE_SYMBOL_HINT_PATTERN = re.compile(r"\b(?:method|function|class|symbol)\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.IGNORECASE)


def extract_files_from_description(description: str, repo_root: Path) -> list[str]:
    """Extract repo-local Python file paths from a task description."""
    seen: set[str] = set()
    files: list[str] = []
    for match in FILE_PATTERN.finditer(description):
        raw_path = match.group(1)
        candidate = (repo_root / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path).resolve()
        try:
            candidate.relative_to(repo_root.resolve())
        except ValueError:
            continue
        rel_path = str(candidate.relative_to(repo_root.resolve()))
        if candidate.exists() and rel_path not in seen:
            seen.add(rel_path)
            files.append(rel_path)
    return files


def extract_focus_symbol(description: str) -> str:
    """Extract a method/function/class hint from a task description."""
    match = SYMBOL_HINT_PATTERN.search(description)
    if match:
        return match.group(1)

    match = REVERSE_SYMBOL_HINT_PATTERN.search(description)
    if match:
        return match.group(1)

    return ""


def augment_description(description: str, files: list[str], symbol: str) -> str:
    """Add focused context to the task description for Aider."""
    lines = [description.strip()]
    context_lines = []
    if files:
        context_lines.append("Focus files:")
        context_lines.extend(f"- {path}" for path in files)
    if symbol:
        context_lines.append(f"Focus symbol: {symbol}")
    if context_lines:
        lines.append("")
        lines.extend(context_lines)
    return "\n".join(lines).strip()


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
        nargs="*",
        help="Optional files to modify (relative to repo root). If omitted, they are extracted from the description.",
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
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass all validation (git clean, analysis, ambiguity checks)",
    )
    parser.add_argument(
        "--batch-mode",
        action="store_true",
        help="Frictionless automation: implies --force --skip-analysis --auto-commit",
    )
    parser.add_argument(
        "--force-local",
        action="store_true",
        help="Force local execution, bypass router (for autonomous execution)",
    )

    # Dual-model workflow flags
    dual_group = parser.add_mutually_exclusive_group()
    dual_group.add_argument(
        "--dual-model",
        action="store_true",
        default=True,
        help="Use dual-model workflow: writer + reviewer (default)",
    )
    dual_group.add_argument(
        "--single-model",
        action="store_false",
        dest="dual_model",
        help="Use single model only (no review phase)",
    )

    args = parser.parse_args()

    # Batch mode convenience
    if args.batch_mode:
        args.force = True
        args.skip_analysis = True

    # Get repo root
    repo_root = Path(__file__).parent.parent

    # Auto-commit if tree is dirty (unless --force skips)
    if not args.force:
        is_clean = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        ).stdout.strip() == ""

        if not is_clean:
            print("⚠️  Working tree is not clean. Auto-committing...")
            try:
                subprocess.run(
                    ["git", "add", "-A"],
                    check=True,
                    cwd=repo_root,
                    capture_output=True,
                )
                msg = f"WIP: {args.description[:60]}"
                subprocess.run(
                    ["git", "commit", "-m", msg],
                    check=True,
                    cwd=repo_root,
                    capture_output=True,
                )
                print("✅ Auto-committed before task")
            except subprocess.CalledProcessError as e:
                print(f"❌ Auto-commit failed: {e}", file=sys.stderr)
                return 1

    # Extract files and focused symbol from the description if needed.
    inferred_files = extract_files_from_description(args.description, repo_root)
    task_files = list(dict.fromkeys([*(args.files or []), *inferred_files]))
    focus_symbol = extract_focus_symbol(args.description)
    task_description = augment_description(args.description, task_files, focus_symbol)

    if not task_files:
        print("❌ Error: No files provided or inferred from description.", file=sys.stderr)
        return 1

    # Pre-flight analysis (unless skipped)
    if not args.skip_analysis:
        from bin.analyze_task import TaskAnalyzer

        analyzer = TaskAnalyzer(repo_root)
        can_proceed, questions = analyzer.analyze(args.description, task_files)

        if not can_proceed:
            print("⚠️  Pre-flight questions detected. Run:")
            print(f"   ./bin/analyze_task.py '{args.description}' {' '.join(task_files)}")
            print("\nOr use --skip-analysis to bypass")
            return 3

    # Validate files exist
    missing_files = []
    for file_path in task_files:
        full_path = repo_root / file_path  # repo_root already assigned above
        if not full_path.exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Error: Files not found:", file=sys.stderr)
        for f in missing_files:
            print(f"   - {f}", file=sys.stderr)
        return 1

    # Route task to optimal executor (unless --force-local)
    if not args.force_local:
        router = TaskRouter(repo_root)
        route = router.classify(args.description, task_files)

        # If not local, inform user and exit
        if route.executor != ExecutorType.LOCAL_AIDER:
            print(f"🔀 Task routed to: {route.executor.value}")
            print(f"📊 Confidence: {route.confidence:.0%}")
            print(f"💡 Reasoning: {route.reasoning}")
            print()
            print(f"💬 This task should use {route.executor.value} instead of local Aider.")
            print(f"   Please run it manually via Claude.ai or Claude Code.")
            return 2  # Exit code 2 = wrong executor
    else:
        # Force-local mode: create fake route
        route = TaskRouter.TaskRoute(ExecutorType.LOCAL_AIDER, "qwen2.5-coder:14b", 1.0, "Forced local execution")

    # Import and execute
    try:
        from domains.coding import CodingDomain

        domain = CodingDomain()

        print(f"📝 Task: {args.description}")
        print(f"📄 Files: {', '.join(task_files)}")
        if focus_symbol:
            print(f"🎯 Symbol: {focus_symbol}")
        print(f"⏱️  Timeout: {args.timeout}s")
        print(f"🎯 Routed to: Local Aider (confidence: {route.confidence:.0%})")
        print(f"🤖 Model: {route.model}")
        print()
        print("Running Aider...")
        print("-" * 70)

        result = domain.execute_task(
            task_description=task_description,
            files=task_files,
            model=args.model,
            timeout_seconds=args.timeout,
            allow_dirty=args.force,
            dual_model=args.dual_model,
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
