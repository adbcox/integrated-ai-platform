#!/usr/bin/env python3
"""
Roadmap Dependency Planner

Reads live roadmap items and computes blocked/unblocked state and next-pull ordering.
"""

import json
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROADMAP_ITEMS_DIR = Path(__file__).parent.parent / "docs/roadmap/items"


def load_roadmap_items() -> Dict[str, dict]:
    """Load all roadmap items from YAML files."""
    items = {}
    if not ROADMAP_ITEMS_DIR.exists():
        return items

    for yaml_file in ROADMAP_ITEMS_DIR.glob("RM-*.yaml"):
        try:
            with open(yaml_file) as f:
                item = yaml.safe_load(f)
                item_id = item.get("id")
                if item_id:
                    items[item_id] = item
        except Exception as e:
            print(f"Warning: Failed to load {yaml_file}: {e}", file=sys.stderr)

    return items


def extract_blockers(item: dict) -> List[str]:
    """Extract the list of items that block this item."""
    if "dependencies" not in item:
        return []

    deps = item["dependencies"]

    # Warn if legacy blocked_by field exists
    if "blocked_by" in deps:
        print(f"Warning: Item {item.get('id')} uses legacy 'blocked_by' field; prefer 'depends_on'", file=sys.stderr)

    # Read canonical depends_on field
    if "depends_on" in deps:
        blockers = deps["depends_on"]
        return blockers if isinstance(blockers, list) else []

    return []


def compute_unblocked_status(
    item_id: str, items: Dict[str, dict], blocked_cache: Dict[str, bool]
) -> bool:
    """Compute whether an item is unblocked."""
    if item_id in blocked_cache:
        return not blocked_cache[item_id]

    item = items.get(item_id)
    if not item:
        return True

    status = item.get("status", "proposed")
    # Completed items never block anything
    if status == "completed":
        return True

    blockers = extract_blockers(item)
    for blocker_id in blockers:
        blocker = items.get(blocker_id)
        if not blocker:
            continue
        blocker_status = blocker.get("status", "proposed")
        if blocker_status != "completed":
            blocked_cache[item_id] = True
            return False

    blocked_cache[item_id] = False
    return True


def compute_pull_priority(
    item_id: str,
    items: Dict[str, dict],
    unblocked_items: Set[str],
    dependents: Dict[str, Set[str]],
) -> float:
    """Compute pull priority score for an item."""
    item = items.get(item_id)
    if not item:
        return 0.0

    # Priority mapping
    priority = item.get("priority", "P3")
    priority_scores = {"P1": 3.0, "P2": 2.0, "P3": 1.0}
    base_score = priority_scores.get(priority, 1.0)

    # Depth score (how many unblocked items depend on this)
    depth = len(dependents.get(item_id, set()))
    depth_score = 0.5 * depth

    # Readiness score (items already in validation/completed get boost)
    status = item.get("status", "proposed")
    readiness_scores = {"completed": 2.0, "in_validation": 1.5, "proposed": 0.0}
    readiness_score = readiness_scores.get(status, 0.0)

    return base_score + depth_score + readiness_score


def build_dependents_map(items: Dict[str, dict]) -> Dict[str, Set[str]]:
    """Build a map of which items depend on each item."""
    dependents: Dict[str, Set[str]] = {}
    for item_id, item in items.items():
        blockers = extract_blockers(item)
        for blocker_id in blockers:
            if blocker_id not in dependents:
                dependents[blocker_id] = set()
            dependents[blocker_id].add(item_id)
    return dependents


def generate_plan(items: Dict[str, dict]) -> dict:
    """Generate the dependency plan."""
    blocked_cache: Dict[str, bool] = {}
    dependents = build_dependents_map(items)

    unblocked_items: Set[str] = set()
    blocked_items: Set[str] = set()

    for item_id in items:
        if compute_unblocked_status(item_id, items, blocked_cache):
            unblocked_items.add(item_id)
        else:
            blocked_items.add(item_id)

    # Score and sort unblocked items
    scored_unblocked = []
    for item_id in unblocked_items:
        priority = compute_pull_priority(item_id, items, unblocked_items, dependents)
        scored_unblocked.append((item_id, priority))

    scored_unblocked.sort(key=lambda x: -x[1])

    # Build next_pull ordering
    next_pull = []
    for rank, (item_id, score) in enumerate(scored_unblocked, 1):
        item = items[item_id]
        next_pull.append(
            {
                "pull_rank": rank,
                "item_id": item_id,
                "title": item.get("title", ""),
                "pull_priority_score": round(score, 2),
                "reason": f"Unblocked; pull priority {round(score, 2)}",
            }
        )

    return {
        "total_items": len(items),
        "unblocked_items": len(unblocked_items),
        "blocked_items": len(blocked_items),
        "unblocked_list": sorted(list(unblocked_items)),
        "blocked_list": sorted(list(blocked_items)),
        "next_pull_ordering": next_pull,
    }


def main():
    items = load_roadmap_items()
    if not items:
        print("No roadmap items found", file=sys.stderr)
        sys.exit(1)

    plan = generate_plan(items)
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
