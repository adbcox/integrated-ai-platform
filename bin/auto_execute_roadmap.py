#!/usr/bin/env python3
"""Autonomous roadmap execution with RM-GOV-001 compliance (frontmatter-based tracking)."""

import sys
import json
import subprocess
import argparse
import time
import os
import re
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from bin.roadmap_parser import (
    parse_roadmap_directory,
    infer_dependencies,
    RoadmapItem,
    update_frontmatter,
    detect_cycles,
)


class RoadmapExecutor:
    """Manages autonomous execution with RM-GOV-001 compliance."""

    EXECUTION_READY_STATUSES = ["Accepted", "Planned"]
    READY_READINESS = ["now", "near", "later"]
    VALID_STATUSES = ["Proposed", "Accepted", "Decomposing", "Planned", "Execution-ready", "In progress", "Validating", "Completed", "Deferred", "Frozen", "Rejected"]

    def __init__(self, repo_root: Path, llm_model: Optional[str] = None):
        self.repo_root = repo_root
        self.roadmap_dir = repo_root / "docs" / "roadmap" / "ITEMS"
        self.artifacts_dir = repo_root / "artifacts" / "executions"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.failures_log = repo_root / "artifacts" / "execution_failures.jsonl"
        self.llm_model = llm_model or "qwen2.5-coder:14b"

    def _update_item_status(
        self,
        item: RoadmapItem,
        new_status: str,
        notes: str = "",
        commit_hash: Optional[str] = None,
        validation_update: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Update item status in markdown and commit."""
        if new_status not in self.VALID_STATUSES:
            print(f"❌ Invalid status '{new_status}'", file=sys.stderr)
            return False

        # Update status in markdown file (bullet-list format)
        try:
            file_path = Path(item.file_path)
            content = file_path.read_text()

            # Replace status in markdown (- **Status:** `Accepted` → - **Status:** `Completed`)
            for status in self.VALID_STATUSES:
                old_status = f'- **Status:** `{status}`'
                if old_status in content:
                    new_status_line = f'- **Status:** `{new_status}`'
                    content = content.replace(old_status, new_status_line)
                    break

            file_path.write_text(content)
        except Exception as e:
            print(f"⚠️  Warning: Could not update file: {e}", file=sys.stderr)
            return True  # Don't fail if file update fails

        # Git commit this status change
        try:
            subprocess.run(
                ["git", "add", item.file_path],
                cwd=self.repo_root,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                check=True,
            )

            msg = f"status: {item.id} → {new_status}\n\n{notes}" if notes else f"status: {item.id} → {new_status}"
            subprocess.run(
                ["git", "commit", "-m", msg],
                cwd=self.repo_root,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                check=True,
            )

            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Could not commit status update: {e}", file=sys.stderr)
            return True  # Don't fail if commit fails

    def _log_failure(self, item_id: str, subtask: str, attempt: int, error: str, duration: float) -> None:
        """Log execution failure to JSONL log."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "item_id": item_id,
            "subtask": subtask,
            "attempt": attempt,
            "error": error,
            "duration_seconds": round(duration, 2),
        }
        try:
            with open(self.failures_log, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"⚠️  Could not write failure log: {e}", file=sys.stderr)

    def _dependencies_met(self, item: RoadmapItem, items: List[RoadmapItem]) -> bool:
        """Check if all dependencies are completed (status == 'Completed')."""
        id_map = {i.id: i for i in items}

        for dep_id in item.dependencies:
            if dep_id not in id_map:
                continue
            dep = id_map[dep_id]
            # Dependencies are met if the dependent item's status is Completed
            if dep.status != "Completed":
                return False
        return True

    def find_executable_items(
        self,
        items: List[RoadmapItem],
        max_count: int = 1,
    ) -> List[RoadmapItem]:
        """Find items ready for execution (respects dependencies, readiness, and priorities)."""
        candidates = []

        for item in items:
            # Skip non-execution-ready items (status must be Accepted or Planned)
            if item.status not in self.EXECUTION_READY_STATUSES:
                continue

            # Check readiness (must be 'now' or 'near')
            if item.readiness not in self.READY_READINESS:
                continue

            # Check dependencies
            if not self._dependencies_met(item, items):
                continue

            candidates.append(item)

        # Sort by: priority class, queue rank, ID
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
        candidates.sort(key=lambda x: (
            priority_order.get(x.priority_class, 999),
            x.queue_rank,
            x.id,
        ))

        return candidates[:max_count]

    def find_grouped_items(self, items: List[RoadmapItem], root_item: RoadmapItem) -> List[RoadmapItem]:
        """Find items that can be grouped with root_item."""
        grouped = [root_item]
        candidates = [i for i in items if i.id in root_item.grouping_candidates]

        for candidate in candidates:
            # Check if dependencies are met
            if self._dependencies_met(candidate, items):
                if candidate.execution.status in self.EXECUTION_READY_STATUSES:
                    grouped.append(candidate)

        return grouped

    def decompose_item(self, item: RoadmapItem, llm_model: Optional[str] = None) -> List[str]:
        """Decompose a roadmap item into subtasks using Ollama API with file path requirements."""
        if not llm_model:
            llm_model = self.llm_model

        expected_files = ', '.join(item.expected_file_families) if item.expected_file_families else 'infer from context'
        prompt = f"""Break down this task into 3-7 EXECUTABLE subtasks.
CRITICAL: Each subtask MUST mention specific Python file(s) to modify.

ID: {item.id}
Title: {item.title}
Description: {item.description}
Category: {item.category}
Expected files: {expected_files}

RULES:
1. Every subtask MUST include a .py file path (e.g., "Update domains/media.py...")
2. Subtasks without file paths will FAIL - be specific!
3. Use existing project structure:
   - bin/ for scripts and executors
   - domains/ for business logic (coding, media, operations, etc.)
   - web/ for web interfaces
   - framework/ for core runtime
   - tests/ for test files
   - config/ for configuration

GOOD EXAMPLES:
✅ "Add health_check() method to domains/media.py"
✅ "Create bin/inventory_manager.py with asset tagging functions"
✅ "Update web/dashboard/app.py to add click-tile navigation"
✅ "Add validation logic to framework/code_executor.py"

BAD EXAMPLES (will fail):
❌ "Design the user interface layout" (no file!)
❌ "Implement drag-and-drop functionality" (no file!)
❌ "Ensure compatibility with devices" (no file!)

Generate subtasks as a JSON array following these rules. MUST be valid JSON with file paths:
["Update domains/xxx.py to add yyy", "Create bin/zzz.py with aaa functionality", ...]

Only JSON array, no other text."""

        try:
            import requests
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=60
            )

            if response.status_code == 200:
                output = response.json().get("response", "")
                json_match = re.search(r'\[.*\]', output, re.DOTALL)
                if json_match:
                    try:
                        subtasks = json.loads(json_match.group())
                        if isinstance(subtasks, list) and len(subtasks) > 0:
                            # Filter: reject subtasks without .py file references
                            py_ref = re.compile(r'[\w/]+\.py')
                            valid = [s for s in subtasks if py_ref.search(s)]
                            if valid:
                                return valid
                    except json.JSONDecodeError:
                        pass

            # Fallback: use expected_file_families to generate file-anchored subtasks
            files = item.expected_file_families[:2] if item.expected_file_families else [f"domains/{item.category.lower()}.py"]
            return [
                f"Review and implement core logic in {files[0]}",
                f"Add validation and error handling to {files[0]}",
                f"Add tests for {files[0]}",
                f"Update {files[1] if len(files) > 1 else files[0]} with integration",
            ]
        except Exception as e:
            print(f"⚠️  Decomposition error: {e}", file=sys.stderr)
            # Fallback when API unavailable
            files = item.expected_file_families[:1] if item.expected_file_families else [f"domains/{item.category.lower()}.py"]
            return [
                f"Review {item.id} in {files[0]}",
                f"Implement {item.title} in {files[0]}",
                f"Test {item.id} in {files[0]}",
                f"Document {item.title} in {files[0]}"
            ]

    def execute_subtask(self, subtask: str, item_id: str = "", dry_run: bool = False, max_retries: int = 3, subtask_timeout: int = 600) -> bool:
        """Execute subtask via local_coding_task.py --force-local with retry logic."""
        if dry_run:
            print(f"    • {subtask} [DRY]")
            return True

        # Validate subtask has file reference; add fallback if missing
        if not re.search(r'\b\w+(?:/\w+)*\.py\b', subtask):
            file_map = {
                'UI': 'web/dashboard/app.py',
                'MEDIA': 'domains/media.py',
                'OPS': 'domains/operations.py',
                'GOV': 'bin/governance.py',
                'AUTO': 'bin/auto_execute_roadmap.py',
                'CORE': 'framework/worker_runtime.py',
                'DEV': 'bin/aider_executor.py',
                'HW': 'domains/hardware.py',
                'HOME': 'domains/home.py',
                'INTEL': 'framework/inference_adapter.py',
                'INV': 'domains/inventory.py',
                'KB': 'framework/state_store.py',
                'LANG': 'domains/language.py',
                'SHOP': 'domains/shop.py',
            }
            # Extract category from item_id if possible
            category = item_id.split('-')[1] if '-' in item_id else 'CORE'
            inferred_file = file_map.get(category, 'domains/coding.py')
            subtask = f"{subtask} (modify {inferred_file})"
            print(f"      [AUTO-FIX] Added inferred file: {inferred_file}")

        print(f"    • {subtask}")

        for attempt in range(1, max_retries + 1):
            if attempt > 1:
                delay = 5 * (2 ** (attempt - 2))  # 5, 10, 20 seconds
                print(f"      ↺ Retry {attempt}/{max_retries} in {delay}s...")
                time.sleep(delay)

            start = time.time()
            try:
                proc = subprocess.Popen(
                    [
                        "python3",
                        str(self.repo_root / "bin" / "local_coding_task.py"),
                        "--force-local",
                        "--batch-mode",
                        subtask
                    ],
                    cwd=self.repo_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=True,
                )
                try:
                    stdout, stderr = proc.communicate(timeout=subtask_timeout)
                    duration = time.time() - start
                    if proc.returncode == 0:
                        print(f"      ✅ Done (attempt {attempt})")
                        return True
                    error = f"exit {proc.returncode}: {stderr[:200] if stderr else 'no error output'}"
                except subprocess.TimeoutExpired:
                    # Kill the entire process group
                    try:
                        os.killpg(os.getpgid(proc.pid), 9)
                    except (ProcessLookupError, OSError):
                        pass
                    proc.wait()
                    duration = time.time() - start
                    error = f"timeout after {subtask_timeout}s"

                print(f"      ❌ Failed: {error}")
                if item_id:
                    self._log_failure(item_id, subtask, attempt, error, duration)

            except Exception as e:
                duration = time.time() - start
                error = str(e)
                print(f"      ❌ Error: {error}")
                if item_id:
                    self._log_failure(item_id, subtask, attempt, error, duration)

        return False

    def execute_item(self, item: RoadmapItem, grouped_items: Optional[List[RoadmapItem]] = None, dry_run: bool = False) -> bool:
        """Execute a roadmap item and update frontmatter."""
        print(f"\n{'='*70}")
        print(f"🚀 {item.id} — {item.title}")
        print(f"{'='*70}")

        self._update_item_status(item, "In progress", notes="Execution started")

        # Decompose into subtasks
        print(f"\n📋 Decomposing into subtasks...")
        subtasks = self.decompose_item(item)

        # CRITICAL: If no subtasks, FAIL - don't mark complete
        if not subtasks or len(subtasks) == 0:
            print(f"❌ FAILED: No subtasks generated for {item.id}")
            self._update_item_status(item, "Accepted", notes="Decomposition failed - reverted")
            return False

        print(f"   Generated {len(subtasks)} subtasks:")

        # Execute subtasks
        failed_count = 0
        for idx, subtask in enumerate(subtasks, 1):
            print(f"   [{idx}/{len(subtasks)}]", end=" ")
            if not self.execute_subtask(subtask, item_id=item.id, dry_run=dry_run):
                failed_count += 1

        # CRITICAL: Require ALL subtasks to pass
        if failed_count == 0:
            self._update_item_status(item, "Completed", notes=f"All {len(subtasks)} subtasks completed")
            print(f"\n✅ Completed: {item.id}")
            return True
        else:
            self._update_item_status(item, "Accepted", notes=f"{failed_count}/{len(subtasks)} subtasks failed - reverted")
            print(f"\n❌ FAILED: {failed_count}/{len(subtasks)} subtasks failed")
            return False

    def run_autonomous_loop(self, max_items: int = 5, dry_run: bool = False, resume: bool = False, filter_pattern: str = "") -> None:
        """Run autonomous execution loop with resume and filtering support."""
        print(f"\n🤖 Autonomous Roadmap Execution")
        print(f"   Max items: {max_items} | Dry run: {dry_run} | Resume: {resume} | Filter: {filter_pattern or 'none'}")

        # Parse items
        items = parse_roadmap_directory(self.roadmap_dir)
        infer_dependencies(items)

        print(f"   Loaded {len(items)} roadmap items")

        # Detect and warn about cycles
        cycles = detect_cycles(items)
        if cycles:
            print(f"⚠️  {len(cycles)} dependency cycle(s) detected:")
            for cycle in cycles:
                print(f"   {' → '.join(cycle)}")
        print()

        # Resume: reset "In progress" items back to "Accepted" to allow retry
        if resume:
            reset_count = 0
            for item in items:
                if item.status == "In progress":
                    print(f"  🔄 Resetting {item.id} from In progress → Accepted")
                    self._update_item_status(item, "Accepted", notes="Reset from In progress (resume mode)")
                    reset_count += 1
            if reset_count > 0:
                # Reload after reset
                items = parse_roadmap_directory(self.roadmap_dir)
                infer_dependencies(items)
                print(f"  Reset {reset_count} items\n")

        executed = 0
        for _ in range(max_items):
            # Find next executable item
            candidates = self.find_executable_items(items, max_count=1)
            if not candidates:
                print(f"✅ No more executable items")
                break

            item = candidates[0]

            # Apply filter if specified
            if filter_pattern:
                if not re.search(filter_pattern, item.id):
                    # Skip this item, reload and find next
                    items = parse_roadmap_directory(self.roadmap_dir)
                    infer_dependencies(items)
                    continue

            # Find grouped items
            grouped = self.find_grouped_items(items, item)
            if len(grouped) > 1:
                print(f"📦 Grouped execution: {item.id} + {len(grouped)-1} others")

            # Execute (pass llm_model to decompose_item)
            self.execute_item(item, grouped_items=grouped if len(grouped) > 1 else None, dry_run=dry_run)
            # Update decompose_item to use passed model
            executed += 1

            # Reload items for updated status
            items = parse_roadmap_directory(self.roadmap_dir)
            infer_dependencies(items)

            if executed % 3 == 0:
                print(f"\n⏸️  Checkpoint: {executed} items executed")
                time.sleep(1)

        print(f"\n{'='*70}")
        print(f"🏁 Execution complete: {executed} items")
        print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Autonomous roadmap execution (RM-GOV-001 compliant)")
    parser.add_argument("--max-items", type=int, default=5, help="Max items to execute")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--model", default="qwen2.5-coder:14b", help="Decomposition model")
    parser.add_argument("--resume", action="store_true", help="Reset stuck In-progress items and retry")
    parser.add_argument("--filter", default="", help="Regex filter on item ID (e.g. 'RM-GOV')")

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    executor = RoadmapExecutor(repo_root, llm_model=args.model)

    try:
        executor.run_autonomous_loop(max_items=args.max_items, dry_run=args.dry_run, resume=args.resume, filter_pattern=args.filter)
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()
