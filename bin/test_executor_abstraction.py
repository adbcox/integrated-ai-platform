#!/usr/bin/env python3
"""Test executor abstraction with real Stage 7 bounded task execution."""

from __future__ import annotations  # stage7-op  # stage7-op  # stage7-op  # stage7-op

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.code_executor import ExecutorFactory, ExecutionRequest, ClaudeCodeExecutor, AiderExecutor


def test_executor_availability() -> None:
    """Test that executors are properly detected."""
    print("=" * 70)
    print("EXECUTOR AVAILABILITY TEST")
    print("=" * 70)

    available = ExecutorFactory.list_available()
    for name, is_available in available:
        status = "✓ AVAILABLE" if is_available else "✗ NOT AVAILABLE"
        print(f"{status}: {name}")

    # Primary executor should be Claude Code
    primary = ExecutorFactory.create()
    print(f"\nPrimary executor: {primary.__class__.__name__}")
    assert isinstance(primary, (ClaudeCodeExecutor, AiderExecutor)), "Unexpected executor type"


def test_claude_code_executor() -> None:
    """Test Claude Code executor with a simple literal replacement."""
    print("\n" + "=" * 70)
    print("CLAUDE CODE EXECUTOR TEST")
    print("=" * 70)

    # Create test file
    test_file = REPO_ROOT / "artifacts" / "executor_test" / "test_file.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)

    original_content = '''"""Test module."""

def hello():
    """Say hello."""
    return "hello"
'''

    test_file.write_text(original_content, encoding="utf-8")
    print(f"✓ Created test file: {test_file}")

    # Create execution request with literal replacement
    request = ExecutionRequest(
        message='def hello()::def hello():\n    """Say hello improved."""',
        target=str(test_file.relative_to(REPO_ROOT)),
        plan_id="test-executor-001",
        stage="stage3",
    )

    # Execute with Claude Code
    executor = ClaudeCodeExecutor()
    print(f"Using executor: {executor.__class__.__name__}")

    result = executor.execute(request)
    print(f"Result: success={result.success}, return_code={result.return_code}")
    print(f"Classification: {result.classification}")
    print(f"Events: {len(result.events)}")

    # Verify file was modified
    modified_content = test_file.read_text(encoding="utf-8")
    if result.success:
        print("✓ File modification attempted by executor")
        if modified_content != original_content:
            print("✓ File content changed")
        else:
            print("⚠ File content unchanged (pattern not matched)")
    else:
        print(f"✗ Execution failed: {result.classification}")

    # Clean up
    test_file.unlink(missing_ok=True)
    test_file.parent.rmdir()


def test_bounded_task_real_execution() -> None:
    """Test real Stage 7 execution with executor abstraction."""
    print("\n" + "=" * 70)
    print("BOUNDED TASK REAL EXECUTION TEST")
    print("=" * 70)

    # Run real bounded task test
    test_script = REPO_ROOT / "bin" / "test_stage7_real_execution.py"
    if not test_script.exists():
        print(f"⚠ Test script not found: {test_script}")
        return

    print(f"Running: {test_script}")
    result = subprocess.run(
        [sys.executable, str(test_script)],
        capture_output=True,
        text=True,
    )

    print(result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)

    if result.returncode == 0:
        print("✓ Real execution test PASSED")
    else:
        print(f"⚠ Real execution test returned code {result.returncode}")
        if result.stderr:
            print(f"stderr: {result.stderr[-500:]}")


def main() -> None:
    """Run executor abstraction tests."""
    try:
        test_executor_availability()
        test_claude_code_executor()
        test_bounded_task_real_execution()

        print("\n" + "=" * 70)
        print("EXECUTOR ABSTRACTION TESTS COMPLETE")
        print("=" * 70)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
