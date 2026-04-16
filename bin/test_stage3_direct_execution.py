#!/usr/bin/env python3
"""Direct test of Stage 3 executor abstraction with proper message format."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]

def find_latest_executor_log() -> Optional[Path]:
    """Find the most recently created executor log."""
    stage3_dir = REPO_ROOT / "artifacts" / "stage3_manager"
    if not stage3_dir.exists():
        return None
    
    executor_logs = list(stage3_dir.glob("*.executor.json"))
    if not executor_logs:
        return None
    
    # Sort by modification time, get the most recent
    executor_logs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return executor_logs[0]

def main() -> int:
    """Test stage3_manager executor abstraction directly."""
    
    print("=" * 70)
    print("STAGE 3 DIRECT EXECUTOR ABSTRACTION TEST")
    print("Testing bounded task message format with actual file modification")
    print("=" * 70)
    
    # Create test target file
    test_dir = REPO_ROOT / "artifacts" / "stage3_direct_test"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = test_dir / "functions.py"
    original_content = '''def calculate_sum(a, b):
    return a + b

def calculate_product(a, b):
    return a * b
'''
    test_file.write_text(original_content, encoding="utf-8")
    print(f"\n[Setup] Created test file: {test_file.relative_to(REPO_ROOT)}")
    print(f"Original content ({len(original_content)} bytes)")
    
    # Create properly formatted bounded task message
    # Format required: target:: replace exact text 'old' with 'new'
    target_relpath = str(test_file.relative_to(REPO_ROOT))
    old_literal = "def calculate_sum(a, b):\n    return a + b"
    new_literal = '''def calculate_sum(a, b):
    """Add two numbers and return the sum."""
    return a + b'''
    
    # Message must have: target:: and match "replace exact text '...' with '...'"
    message = f"{target_relpath}:: replace exact text '{old_literal}' with '{new_literal}'"
    
    # Call stage3_manager with the test file and bounded task message
    cmd = [
        sys.executable,
        str(REPO_ROOT / "bin" / "stage3_manager.py"),
        "--query", "calculate sum docstring addition",
        "--target", target_relpath,
        "--message", message,
        "--commit-msg", "Test: Add docstring to calculate_sum",
        "--lines", "1-3",
        "--notes", "Direct Stage 3 executor test",
    ]
    
    print(f"\n[Execution] Calling stage3_manager with bounded task message...")
    print(f"Message format: target:: replace exact text 'old' with 'new'")
    print(f"Target: {target_relpath}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"\nReturn code: {result.returncode}")
    if result.stdout:
        lines = result.stdout.split('\n')
        # Show last few meaningful lines
        for line in lines[-10:]:
            if line.strip():
                print(f"  {line}")
    if result.stderr:
        print(f"Stderr:\n{result.stderr[-400:]}")
    
    # Give it a moment for file I/O
    time.sleep(0.5)
    
    # Check executor log (find most recent)
    print(f"\n[Executor Detection]")
    executor_log = find_latest_executor_log()
    
    executor_name = None
    if executor_log:
        try:
            data = json.loads(executor_log.read_text(encoding="utf-8"))
            executor_name = data.get("executor", "unknown")
            print(f"✓ Executor log found: {executor_log.relative_to(REPO_ROOT)}")
            print(f"✓ Executor used: {executor_name}")
        except json.JSONDecodeError as e:
            print(f"✗ Could not parse executor log: {e}")
    else:
        print(f"✗ No executor log found in artifacts/stage3_manager/")
    
    # Check if file was actually modified
    print(f"\n[File Modification]")
    modified_content = test_file.read_text(encoding="utf-8")
    
    if new_literal in modified_content:
        print(f"✓ File was modified successfully!")
        print(f"  Original length: {len(original_content)} bytes")
        print(f"  Modified length: {len(modified_content)} bytes")
        print(f"✓ New pattern found in file")
        file_modified = True
    else:
        print(f"✗ File was not modified")
        print(f"  Expected pattern not found")
        file_modified = False
    
    print(f"\n{'=' * 70}")
    print("[Summary]")
    print(f"  Return code: {result.returncode}")
    print(f"  Executor detected: {executor_name or 'NO'}")
    print(f"  File modified: {'YES' if file_modified else 'NO'}")
    
    if executor_name == "ClaudeCodeExecutor" and file_modified:
        print(f"\n✓✓✓ CRITICAL SUCCESS ✓✓✓")
        print(f"Claude Code executor works - real file modifications proven!")
        return 0
    elif executor_name and file_modified:
        print(f"\n⚠ Executor works but not Claude Code: {executor_name}")
        return 1
    else:
        print(f"\n✗ Execution failed or executor not detected")
        return 1

if __name__ == "__main__":
    sys.exit(main())
