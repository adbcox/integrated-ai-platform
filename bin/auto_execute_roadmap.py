#!/usr/bin/env python3
"""Autonomous roadmap execution loop."""

import sys
import json
import subprocess
import argparse
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from bin.roadmap_parser import (
    parse_roadmap_directory,
    infer_dependencies,
    RoadmapItem,
    parse_roadmap_file,
)


class RoadmapExecutor:
    """Manages autonomous execution of roadmap items."""

    def __init__(self, repo_root: Path, status_file: Optional[Path] = None):
        self.repo_root = repo_root
        self.roadmap_dir = repo_root / "docs" / "roadmap"
        self.status_file = status_file or (self.roadmap_dir / "STATUS.yaml")
        self.artifacts_dir = repo_root / "artifacts" / "roadmap_execution"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Load execution state
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load execution state from STATUS.yaml."""
        if self.status_file.exists():
            try:
                with open(self.status_file) as f:
                    state = yaml.safe_load(f) or {}
                    return state
            except Exception as e:
                print(f"⚠️  Error loading state: {e}", file=sys.stderr)
                return {}
        return {"items": {}, "execution_log": []}

    def _save_state(self) -> None:
        """Save execution state to STATUS.yaml."""
        try:
            self.status_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.status_file, 'w') as f:
                yaml.dump(self.state, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"❌ Error saving state: {e}", file=sys.stderr)

    def _update_item_status(
        self,
        item_id: str,
        status: str,
        notes: str = "",
        commit_hash: Optional[str] = None,
    ) -> None:
        """Update status of a roadmap item."""
        if item_id not in self.state["items"]:
            self.state["items"][item_id] = {}

        self.state["items"][item_id].update({
            "status": status,
            "last_updated": datetime.utcnow().isoformat(),
            "notes": notes,
        })

        if commit_hash:
            self.state["items"][item_id]["commit_hash"] = commit_hash

        # Log to execution log
        self.state["execution_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "item_id": item_id,
            "status": status,
            "notes": notes,
        })

    def _dependencies_met(self, item: RoadmapItem) -> bool:
        """Check if all dependencies are completed."""
        for dep_id in item.dependencies:
            dep_status = self.state.get("items", {}).get(dep_id, {}).get("status")
            if dep_status != "completed":
                return False
        return True

    def find_next_executable_item(
        self,
        items: List[RoadmapItem],
    ) -> Optional[RoadmapItem]:
        """Find the next item to execute (highest priority, dependencies met)."""
        candidates = []

        for item in items:
            current_status = self.state.get("items", {}).get(item.id, {}).get("status", "planned")

            # Skip non-planned items
            if current_status != "planned":
                continue

            # Check dependencies
            if not self._dependencies_met(item):
                continue

            # Add to candidates
            candidates.append(item)

        # Sort by priority (lower number = higher priority), then by ID
        candidates.sort(key=lambda x: (x.priority, x.id))

        return candidates[0] if candidates else None

    def decompose_item(self, item: RoadmapItem, llm_model: Optional[str] = None) -> List[str]:
        """Decompose a roadmap item into subtasks using LLM."""
        if not llm_model:
            llm_model = "qwen2.5-coder:14b"

        prompt = f"""Analyze this roadmap item and decompose it into 3-7 concrete subtasks.

ID: {item.id}
Title: {item.title}

Objective: {item.objective}

Required Outcomes:
{chr(10).join(f'- {o}' for o in item.required_outcome)}

Required Artifacts:
{chr(10).join(f'- {a}' for a in item.required_artifacts)}

First Milestone: {item.first_milestone}

Respond ONLY with a JSON array of subtasks, each 1-2 sentences:
[
  "Subtask 1: concrete action here",
  "Subtask 2: concrete action here",
  ...
]

Only JSON, no other text."""

        try:
            cmd = [
                "aider",
                "--no-auto-commits",
                f"--model={llm_model}",
                "--read=/dev/stdin",
            ]

            proc = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.repo_root,
            )

            output = proc.stdout + (proc.stderr or "")

            # Extract JSON from output
            import re
            json_match = re.search(r'\[.*\]', output, re.DOTALL)
            if json_match:
                try:
                    subtasks = json.loads(json_match.group())
                    return subtasks if isinstance(subtasks, list) else []
                except json.JSONDecodeError:
                    pass

            # Fallback: return first milestone as a single task
            return [item.first_milestone]

        except Exception as e:
            print(f"⚠️  Error decomposing item: {e}", file=sys.stderr)
            return [item.first_milestone]

    def execute_subtask(self, subtask: str, item_id: str, dry_run: bool = False) -> bool:
        """Execute a single subtask via quick_task.sh."""
        print(f"\n  🎯 Subtask: {subtask}")

        if dry_run:
            print(f"  [DRY RUN] Would execute: ./bin/quick_task.sh --dual-model '{subtask}'")
            return True

        try:
            # Run quick_task.sh with dual-model enabled
            result = subprocess.run(
                [
                    str(self.repo_root / "bin" / "quick_task.sh"),
                    "--dual-model",
                    subtask,
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                print(f"  ✅ Completed")
                return True
            else:
                print(f"  ❌ Failed (exit code {result.returncode})")
                if result.stderr:
                    print(f"     {result.stderr[:200]}")
                return False

        except subprocess.TimeoutExpired:
            print(f"  ⏱️  Timeout")
            return False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False

    def execute_item(self, item: RoadmapItem, dry_run: bool = False) -> bool:
        """Execute a roadmap item and its subtasks."""
        print(f"\n{'='*70}")
        print(f"🚀 Executing: {item.id} — {item.title}")
        print(f"{'='*70}")

        self._update_item_status(item.id, "in_progress")
        self._save_state()

        # Decompose into subtasks
        print(f"\n📋 Decomposing into subtasks...")
        subtasks = self.decompose_item(item)
        print(f"   Generated {len(subtasks)} subtasks")

        # Execute each subtask
        failed_count = 0
        for idx, subtask in enumerate(subtasks, 1):
            print(f"\n   [{idx}/{len(subtasks)}]", end="")
            if not self.execute_subtask(subtask, item.id, dry_run=dry_run):
                failed_count += 1

        # Update status
        if failed_count == 0:
            self._update_item_status(item.id, "completed", notes=f"Executed {len(subtasks)} subtasks")
            print(f"\n✅ Completed: {item.id}")
        else:
            self._update_item_status(
                item.id,
                "blocked",
                notes=f"{failed_count}/{len(subtasks)} subtasks failed"
            )
            print(f"\n⚠️  Blocked: {item.id} ({failed_count} failures)")

        self._save_state()
        return failed_count == 0

    def run_autonomous_loop(self, max_items: int = 5, dry_run: bool = False) -> None:
        """Run the autonomous execution loop."""
        print(f"🤖 Starting autonomous roadmap execution loop")
        print(f"   Max items: {max_items}")
        print(f"   Dry run: {dry_run}")
        print()

        # Parse all items
        items = parse_roadmap_directory(self.roadmap_dir)
        infer_dependencies(items)

        print(f"📦 Loaded {len(items)} roadmap items")

        # Execute loop
        executed_count = 0
        for _ in range(max_items):
            item = self.find_next_executable_item(items)
            if not item:
                print(f"\n✅ No more executable items (all completed or blocked)")
                break

            self.execute_item(item, dry_run=dry_run)
            executed_count += 1

            # Check for unmet dependencies after execution
            if executed_count % 3 == 0:
                print(f"\n⏸️  Checkpoint: {executed_count} items executed")
                time.sleep(1)

        print(f"\n{'='*70}")
        print(f"🏁 Loop complete: {executed_count} items executed")
        print(f"{'='*70}")


def main():
    parser = argparse.ArgumentParser(description="Autonomous roadmap execution loop")
    parser.add_argument(
        "--max-items",
        type=int,
        default=5,
        help="Maximum items to execute (default: 5)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running tasks",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5-coder:14b",
        help="Model for decomposition (default: qwen2.5-coder:14b)",
    )

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    executor = RoadmapExecutor(repo_root)

    try:
        executor.run_autonomous_loop(max_items=args.max_items, dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\n⏹️  Execution interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
