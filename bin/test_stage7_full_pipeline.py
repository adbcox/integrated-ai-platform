#!/usr/bin/env python3
"""Test full end-to-end Stage 7 → Stage 3 pipeline with real file modifications."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def find_latest_executor_log() -> Path | None:
    """Find the most recently created executor log."""
    stage3_dir = REPO_ROOT / "artifacts" / "stage3_manager"
    if not stage3_dir.exists():
        return None
    
    executor_logs = list(stage3_dir.glob("*.executor.json"))
    if not executor_logs:
        return None
    
    executor_logs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return executor_logs[0]

def find_stage7_plan(plan_id: str) -> Path | None:
    """Find Stage 7 plan history file."""
    plan_path = REPO_ROOT / "artifacts" / "manager6" / "plans" / f"{plan_id}.json"
    return plan_path if plan_path.exists() else None

def main() -> int:
    print("=" * 70)
    print("FULL STAGE 7 PIPELINE INTEGRATION TEST")
    print("Testing Stage 7 → Stage 6 → Stage 5 → Stage 4 → Stage 3 flow")
    print("=" * 70)
    
    # Create test file with a clear modification need
    test_dir = REPO_ROOT / "artifacts" / "stage7_full_test"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = test_dir / "utilities.py"
    original_content = '''def process_data(items):
    return items
'''
    test_file.write_text(original_content, encoding="utf-8")
    print(f"\n[Setup] Created test file: {test_file.relative_to(REPO_ROOT)}")
    print(f"Original content ({len(original_content)} bytes)")
    
    # Test with a simple, clear query
    plan_id = f"stage7-full-test-{int(time.time())}"
    query = "process_data function with better documentation"
    
    cmd = [
        sys.executable,
        str(REPO_ROOT / "bin" / "stage7_manager.py"),
        "--query", *query.split(),
        "--plan-id", plan_id,
        "--commit-msg", "Test: Improve process_data documentation",
        "--manifest", str(REPO_ROOT / "config" / "promotion_manifest.json"),
        "--max-subplans", "1",
        "--subplan-size", "1",
    ]
    
    print(f"\n[Execution] Running Stage 7 with query: {query}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"Return code: {result.returncode}")
    if result.returncode != 0:
        print(f"Stderr: {result.stderr[-300:] if result.stderr else 'None'}")
    
    # Wait for async processing
    time.sleep(1)
    
    # Check Stage 7 plan
    print(f"\n[Stage 7] Checking plan creation...")
    stage7_plan = find_stage7_plan(plan_id)
    if stage7_plan:
        print(f"✓ Stage 7 plan found: {stage7_plan.relative_to(REPO_ROOT)}")
        try:
            plan_data = json.loads(stage7_plan.read_text(encoding="utf-8"))
            subplan_count = len(plan_data.get("plan_payload", {}).get("subplans", []))
            print(f"  Subplans created: {subplan_count}")
        except:
            print(f"  (Could not parse plan)")
    else:
        print(f"✗ Stage 7 plan not found")
    
    # Check if Stage 3 was reached (by looking for executor logs)
    print(f"\n[Stage 3] Checking executor invocation...")
    latest_executor_log = find_latest_executor_log()
    
    executor_name = None
    if latest_executor_log:
        try:
            data = json.loads(latest_executor_log.read_text(encoding="utf-8"))
            executor_name = data.get("executor")
            print(f"✓ Executor log found: {latest_executor_log.relative_to(REPO_ROOT)}")
            print(f"  Executor used: {executor_name}")
        except:
            pass
    
    # Check file modification
    print(f"\n[File Modification]")
    modified_content = test_file.read_text(encoding="utf-8")
    file_changed = modified_content != original_content
    
    if file_changed:
        print(f"✓ File was modified")
        print(f"  Original: {len(original_content)} bytes")
        print(f"  Modified: {len(modified_content)} bytes")
    else:
        print(f"⚠ File was not modified (may still be processing)")
    
    # Report results
    print(f"\n{'=' * 70}")
    print("[Summary]")
    print(f"  Plan created: {'YES' if stage7_plan else 'NO'}")
    print(f"  Executor used: {executor_name or 'NOT DETECTED'}")
    print(f"  File modified: {'YES' if file_changed else 'NO'}")
    
    if executor_name == "ClaudeCodeExecutor" and file_changed:
        print(f"\n✓✓✓ PIPELINE SUCCESS ✓✓✓")
        print(f"Full Stage 7 pipeline flows to Stage 3 with real modifications!")
        return 0
    elif executor_name and file_changed:
        print(f"\n⚠ Pipeline works but using {executor_name}")
        return 1
    elif executor_name:
        print(f"\n⚠ Executor detected but file not modified")
        return 1
    else:
        print(f"\n⚠ Pipeline may still be processing or incomplete")
        return 1

if __name__ == "__main__":
    sys.exit(main())
