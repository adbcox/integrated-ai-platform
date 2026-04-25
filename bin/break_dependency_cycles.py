#!/usr/bin/env python3
"""Automatically break circular dependencies in roadmap by removing weakest links."""

import sys
import re
from pathlib import Path
from typing import List, Set, Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from bin.roadmap_parser import parse_roadmap_directory, infer_dependencies, detect_cycles, RoadmapItem


def find_weakest_link_in_cycle(cycle: List[str], items_by_id: Dict[str, RoadmapItem]) -> Tuple[str, str]:
    """
    Find the weakest dependency link in a cycle to break it.
    Strategy: Remove dependency from item with MOST other dependencies (least critical).
    Returns: (item_to_modify, dependency_to_remove)
    """
    dep_counts = {}

    for item_id in cycle[:-1]:  # Exclude duplicate at end
        item = items_by_id.get(item_id)
        if item:
            dep_counts[item_id] = len(item.dependencies)

    if not dep_counts:
        return (cycle[0], cycle[1])

    # Item with most other deps is best candidate to lose one (least critical)
    item_to_modify = max(dep_counts, key=dep_counts.get)
    idx = cycle.index(item_to_modify)
    next_in_cycle = cycle[(idx + 1) % len(cycle[:-1])]  # Next in cycle

    return (item_to_modify, next_in_cycle)


def remove_dependency_from_file(file_path: Path, dep_id: str) -> bool:
    """Remove a dependency reference from a markdown file."""
    try:
        content = file_path.read_text()
        original = content

        # Strategy: Remove the dependency ID with backticks (e.g. `RM-TESTING-020`)
        # This handles both explicit Dependencies sections and inferred references

        # First, try removing the dependency from the Dependencies section
        new_content = re.sub(
            rf'- `{re.escape(dep_id)}`[^\n]*\n',  # Match `RM-ID` with optional description
            '',
            content
        )

        # Also remove it from inline references in descriptions (just the ID and backticks)
        if new_content == content:
            new_content = re.sub(
                rf'`{re.escape(dep_id)}`',
                '',
                content
            )

        if new_content != original:
            file_path.write_text(new_content)
            return True
        return False
    except Exception as e:
        print(f"⚠️  Error modifying {file_path}: {e}", file=sys.stderr)
        return False


def break_cycles(cycles: List[List[str]], items_by_id: Dict[str, RoadmapItem], roadmap_dir: Path, max_to_break: int = 50) -> List[Tuple[str, str]]:
    """Break circular dependencies intelligently."""
    broken = []

    for i, cycle in enumerate(cycles[:max_to_break]):
        item_to_modify, dep_to_remove = find_weakest_link_in_cycle(cycle, items_by_id)

        file_path = roadmap_dir / f"{item_to_modify}.md"
        if file_path.exists():
            if remove_dependency_from_file(file_path, dep_to_remove):
                broken.append((item_to_modify, dep_to_remove))
                print(f"  [{i+1}] Removed {dep_to_remove} from {item_to_modify} — breaks cycle: {' → '.join(cycle)}")
            else:
                print(f"  [{i+1}] ⚠️  Could not remove {dep_to_remove} from {item_to_modify}")
        else:
            print(f"  [{i+1}] ⚠️  File not found: {file_path}")

    return broken


def main():
    repo_root = Path(__file__).parent.parent
    roadmap_dir = repo_root / "docs" / "roadmap" / "ITEMS"

    print("🔍 Analyzing roadmap cycles...")

    # Parse roadmap
    items = parse_roadmap_directory(roadmap_dir)
    infer_dependencies(items)
    items_by_id = {item.id: item for item in items}

    # Detect cycles
    cycles = detect_cycles(items)
    print(f"Found {len(cycles)} circular dependency cycles\n")

    if not cycles:
        print("✅ No cycles detected!")
        return 0

    # Break cycles
    print("🔨 Breaking cycles by removing weakest dependency links...")
    broken = break_cycles(cycles, items_by_id, roadmap_dir)

    print(f"\n✅ Broke {len(broken)}/{len(cycles)} cycles")
    print(f"\nNext step: Review changes and commit")
    print(f"  git diff docs/roadmap/ITEMS/")
    print(f"  git add docs/roadmap/ITEMS/")
    print(f"  git commit -m 'fix: Break circular dependencies (automated)'")

    return 0


if __name__ == "__main__":
    sys.exit(main())
