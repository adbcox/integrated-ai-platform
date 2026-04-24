#!/usr/bin/env python3
"""Autonomous roadmap execution with RM-GOV-001 compliance (frontmatter-based tracking)."""

import sys
import json
import subprocess
import argparse
import time
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
)


class RoadmapExecutor:
    """Manages autonomous execution with RM-GOV-001 compliance."""

    EXECUTION_READY_STATUSES = ["Accepted", "Planned"]
    READY_READINESS = ["now", "near"]
    VALID_STATUSES = ["Proposed", "Accepted", "Decomposing", "Planned", "Execution-ready", "In progress", "Validating", "Completed", "Deferred", "Frozen", "Rejected"]

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.roadmap_dir = repo_root / "docs" / "roadmap" / "ITEMS"
        self.artifacts_dir = repo_root / "artifacts" / "executions"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

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
                capture_output=True,
                check=True,
            )

            msg = f"status: {item.id} → {new_status}\n\n{notes}" if notes else f"status: {item.id} → {new_status}"
            subprocess.run(
                ["git", "commit", "-m", msg],
                cwd=self.repo_root,
                capture_output=True,
                check=True,
            )

            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Could not commit status update: {e}", file=sys.stderr)
            return True  # Don't fail if commit fails

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
        """Decompose a roadmap item into subtasks using Ollama API."""
        if not llm_model:
            llm_model = "qwen2.5-coder:14b"

        prompt = f"""Analyze this roadmap item and decompose it into 3-7 concrete subtasks.

ID: {item.id}
Title: {item.title}
Description: {item.description}

Respond ONLY with a JSON array of concrete, actionable subtasks:
["Subtask 1", "Subtask 2", ...]

Only JSON, no other text."""

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
                import re
                json_match = re.search(r'\[.*\]', output, re.DOTALL)
                if json_match:
                    try:
                        subtasks = json.loads(json_match.group())
                        if isinstance(subtasks, list) and len(subtasks) > 0:
                            return subtasks
                    except json.JSONDecodeError:
                        pass

            # Fallback: heuristic decomposition
            return [
                f"Review requirements for {item.id}",
                f"Implement core functionality for {item.title}",
                f"Add tests and validation for {item.id}",
                f"Update documentation for {item.title}"
            ]
        except Exception as e:
            print(f"⚠️  Decomposition error: {e}", file=sys.stderr)
            # Fallback plan when API unavailable
            return [
                f"Review {item.id} requirements",
                f"Implement {item.title}",
                f"Test {item.id}",
                f"Document {item.title}"
            ]

    def execute_subtask(self, subtask: str, dry_run: bool = False) -> bool:
        """Execute a single subtask via quick_task.sh."""
        if dry_run:
            print(f"    • {subtask} [DRY]")
            return True

        print(f"    • {subtask}")
        try:
            cmd = f"{self.repo_root}/bin/quick_task.sh --dual-model '{subtask}'"
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=self.repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                print(f"      ✅ Done")
                return True
            else:
                print(f"      ❌ Failed (exit {result.returncode})")
                return False
        except subprocess.TimeoutExpired:
            print(f"      ⏱️  Timeout")
            return False
        except Exception as e:
            print(f"      ❌ Error: {e}")
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
            if not self.execute_subtask(subtask, dry_run=dry_run):
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

    def run_autonomous_loop(self, max_items: int = 5, dry_run: bool = False) -> None:
        """Run autonomous execution loop."""
        print(f"\n🤖 Autonomous Roadmap Execution")
        print(f"   Max items: {max_items} | Dry run: {dry_run}")

        # Parse items
        items = parse_roadmap_directory(self.roadmap_dir)
        infer_dependencies(items)

        print(f"   Loaded {len(items)} roadmap items")
        print()

        executed = 0
        for _ in range(max_items):
            # Find next executable item
            candidates = self.find_executable_items(items, max_count=1)
            if not candidates:
                print(f"✅ No more executable items")
                break

            item = candidates[0]

            # Find grouped items
            grouped = self.find_grouped_items(items, item)
            if len(grouped) > 1:
                print(f"📦 Grouped execution: {item.id} + {len(grouped)-1} others")

            # Execute
            self.execute_item(item, grouped_items=grouped if len(grouped) > 1 else None, dry_run=dry_run)
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

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    executor = RoadmapExecutor(repo_root)

    try:
        executor.run_autonomous_loop(max_items=args.max_items, dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()
