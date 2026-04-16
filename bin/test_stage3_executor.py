#!/usr/bin/env python3
"""Direct test of Stage 3 executor abstraction."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_stage3_with_executor() -> int:
    """Test stage3_manager with executor abstraction directly."""
    print("=" * 70)
    print("STAGE 3 EXECUTOR ABSTRACTION TEST")
    print("Direct test of executor abstraction in stage3_manager")
    print("=" * 70)

    # Create test file that needs modification
    test_file = REPO_ROOT / "artifacts" / "stage3_executor_test" / "test_module.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)

    original = '''def greet(name):
    return f"Hello {name}"
'''
    test_file.write_text(original, encoding="utf-8")
    print(f"\n[Setup] Created test file: {test_file.relative_to(REPO_ROOT)}")

    # Create message file
    message = 'def greet(name)::def greet(name):\n    """Greet a person."""'
    message_file = Path(tempfile.gettempdir()) / "stage3_test_message.msg"
    message_file.write_text(message, encoding="utf-8")
    print(f"[Setup] Created message file: {message_file}")

    # Call stage3_manager directly with the test file
    plan_id = "stage3-executor-001"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "bin" / "stage3_manager.py"),
        "--query",
        "greet docstring",
        "--target",
        str(test_file.relative_to(REPO_ROOT)),
        "--message",
        'def greet(name)::def greet(name):\n    """Greet a person."""',
        "--commit-msg",
        "Executor test: Add docstring",
        "--lines",
        "1-5",
        "--notes",
        "Test executor abstraction",
    ]

    print(f"\n[Execution] Running stage3_manager...")
    print(f"Command: {' '.join(cmd[-6:])}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    print(f"\nReturn code: {result.returncode}")
    if result.stdout:
        print(f"Output:\n{result.stdout[-500:]}")
    if result.stderr:
        print(f"Stderr:\n{result.stderr[-500:]}")

    # Check if executor log was created
    print(f"\n[Executor Detection]")
    executor_log = REPO_ROOT / "artifacts" / "stage3_manager" / f"{plan_id}.executor.json"

    if executor_log.exists():
        try:
            data = json.loads(executor_log.read_text(encoding="utf-8"))
            executor_name = data.get("executor", "unknown")
            print(f"✓ Executor log found: {executor_log.relative_to(REPO_ROOT)}")
            print(f"✓ Executor used: {executor_name}")

            if executor_name == "ClaudeCodeExecutor":
                print(f"\n✓✓✓ CRITICAL SUCCESS ✓✓✓")
                print(f"Claude Code executor was used - Aider is no longer mandatory!")
            elif executor_name == "AiderExecutor":
                print(f"\n⚠ Aider executor was used (fallback)")
            else:
                print(f"\n? Unknown executor: {executor_name}")
        except json.JSONDecodeError as e:
            print(f"✗ Could not parse executor log: {e}")
    else:
        print(f"✗ No executor log found at: {executor_log.relative_to(REPO_ROOT)}")
        print(f"  This may indicate stage3_manager didn't call run_worker")

    # Check if file was modified
    print(f"\n[File Modification]")
    modified = test_file.read_text(encoding="utf-8")
    if modified != original:
        print(f"✓ File was modified by executor")
        print(f"  Original length: {len(original)}")
        print(f"  Modified length: {len(modified)}")
    else:
        print(f"⚠ File was not modified")

    # Clean up
    message_file.unlink(missing_ok=True)
    test_file.unlink(missing_ok=True)

    print(f"\n{'=' * 70}")

    if executor_log.exists():
        try:
            data = json.loads(executor_log.read_text(encoding="utf-8"))
            if data.get("executor") == "ClaudeCodeExecutor":
                return 0
        except:
            pass

    return 1


if __name__ == "__main__":
    sys.exit(test_stage3_with_executor())
