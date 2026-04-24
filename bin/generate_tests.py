#!/usr/bin/env python3
"""Generate and run pytest tests for changed functions after task execution."""

import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Tuple, List
import ast
import re

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGenerator:
    """Generate pytest tests from changed functions."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def get_changed_functions(self, commit_sha: str = "HEAD") -> Dict[str, str]:
        """Extract changed code from git diff.

        Returns: {file_path: diff_content}
        """
        try:
            result = subprocess.run(
                ["git", "diff", f"{commit_sha}~1..{commit_sha}"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                timeout=10,
            )

            if result.returncode != 0 or not result.stdout:
                return {}

            # Parse diff to extract changed files
            changes = {}
            current_file = None
            current_diff = []

            for line in result.stdout.split("\n"):
                if line.startswith("diff --git"):
                    if current_file and current_diff:
                        changes[current_file] = "\n".join(current_diff)
                    parts = line.split()
                    current_file = parts[-1].lstrip("b/")
                    current_diff = [line]
                elif current_file:
                    current_diff.append(line)

            if current_file and current_diff:
                changes[current_file] = "\n".join(current_diff)

            # Filter to Python files only
            return {f: diff for f, diff in changes.items() if f.endswith(".py")}
        except Exception as e:
            print(f"Error getting changes: {e}", file=sys.stderr)
            return {}

    def generate_test_code(self, changes: Dict[str, str]) -> str:
        """Generate test code using local LLM."""
        if not changes:
            return ""

        # Build context for test generation
        diffs = "\n\n".join(
            f"File: {file}\n{diff[:500]}" for file, diff in changes.items()
        )

        prompt = f"""Generate comprehensive pytest tests for these code changes:

{diffs}

Requirements:
1. Test happy path and edge cases
2. Use pytest fixtures for setup/teardown
3. Mock external dependencies (subprocess, network calls)
4. Include clear test names and docstrings
5. Return ONLY the complete test file code starting with imports

Generate tests that validate:
- Correct behavior on valid inputs
- Error handling on invalid inputs
- Edge cases and boundary conditions
- Integration with dependencies"""

        try:
            # Use ollama to generate tests
            result = subprocess.run(
                ["ollama", "run", "qwen2.5-coder:14b", "--", prompt],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            print(f"Warning: Test generation failed: {e}", file=sys.stderr)

        return ""

    def write_tests(self, test_code: str) -> Path:
        """Write generated tests to test file."""
        test_dir = self.repo_root / "tests"
        test_dir.mkdir(exist_ok=True)

        test_file = test_dir / "test_auto_generated.py"

        # Add pytest imports if missing
        if "import pytest" not in test_code:
            test_code = "import pytest\n\n" + test_code

        with open(test_file, "w") as f:
            f.write(test_code)

        return test_file

    def run_tests(self, test_file: Path) -> Tuple[bool, str]:
        """Run pytest and return (passed, output)."""
        try:
            result = subprocess.run(
                ["pytest", str(test_file), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.repo_root,
            )

            output = result.stdout + result.stderr
            return result.returncode == 0, output
        except subprocess.TimeoutExpired:
            return False, "Test execution timed out"
        except Exception as e:
            return False, f"Error running tests: {e}"

    def commit_tests(self, test_file: Path, commit_sha: str) -> bool:
        """Commit test file."""
        try:
            # Stage test file
            subprocess.run(
                ["git", "add", str(test_file.relative_to(self.repo_root))],
                cwd=self.repo_root,
                timeout=10,
                capture_output=True,
            )

            # Create commit
            original_msg = subprocess.run(
                ["git", "log", "-1", "--format=%B", commit_sha],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
            ).stdout.strip()

            message = f"test: auto-generated tests for {original_msg.split(chr(10))[0]}"

            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                timeout=10,
            )

            return result.returncode == 0
        except Exception as e:
            print(f"Error committing: {e}", file=sys.stderr)
            return False


def main() -> int:
    """Generate and validate tests for task commit."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate pytest tests for changed functions"
    )
    parser.add_argument(
        "--commit",
        default="HEAD",
        help="Commit to analyze (default: HEAD)"
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Skip running tests"
    )
    parser.add_argument(
        "--skip-commit",
        action="store_true",
        help="Skip committing test file"
    )

    args = parser.parse_args()
    repo_root = Path.cwd()

    generator = TestGenerator(repo_root)

    # Get changes
    print(f"🔍 Analyzing changes in {args.commit}...")
    changes = generator.get_changed_functions(args.commit)

    if not changes:
        print("ℹ️  No Python files changed")
        return 0

    print(f"📊 Found {len(changes)} changed Python file(s)")
    for file in changes.keys():
        print(f"   - {file}")

    # Generate tests
    print("\n🤖 Generating tests with local LLM...")
    test_code = generator.generate_test_code(changes)

    if not test_code or len(test_code) < 50:
        print("❌ Test generation failed or produced empty output")
        return 1

    # Write tests
    print("📝 Writing tests...")
    test_file = generator.write_tests(test_code)
    print(f"   Written to {test_file.relative_to(repo_root)}")

    # Run tests
    if args.skip_run:
        print("⏭️  Skipping test execution")
        return 0

    print("\n🧪 Running tests...")
    passed, output = generator.run_tests(test_file)

    # Show output
    lines = output.split("\n")
    for line in lines[-30:]:  # Last 30 lines
        if line.strip():
            print(f"   {line}")

    if not passed:
        print("\n❌ Tests failed - skipping commit")
        return 1

    print("\n✅ All tests passed!")

    # Commit
    if not args.skip_commit:
        print("📦 Committing tests...")
        if generator.commit_tests(test_file, args.commit):
            print("✅ Tests committed")
        else:
            print("⚠️  Test file created but could not commit")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
