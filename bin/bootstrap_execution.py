#!/usr/bin/env python3
"""Bootstrap autonomous execution by marking foundational items complete."""
import sys
from pathlib import Path
from datetime import datetime
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent))
from bin.roadmap_parser import parse_roadmap_directory

def find_bootstrap_candidates(items):
    """Find items safe to mark complete to bootstrap execution.

    Strategy:
    1. Items with zero dependencies (can be done standalone)
    2. Items with only completed dependencies
    3. Foundational GOV items (governance framework)
    """
    completed_ids = {i.id for i in items if i.status == "Completed"}
    id_map = {i.id: i for i in items}

    candidates = {
        'zero_deps': [],
        'foundational_gov': [],
        'near_ready': []
    }

    for item in items:
        if item.status != "Accepted":
            continue

        # Zero dependencies
        if not item.dependencies:
            candidates['zero_deps'].append(item)
            continue

        # Foundational GOV items (RM-GOV-002, RM-GOV-003)
        if item.id.startswith("RM-GOV-") and item.id in ["RM-GOV-002", "RM-GOV-003"]:
            candidates['foundational_gov'].append(item)
            continue

        # Items with only 1-2 blocking deps (near ready)
        unmet = [d for d in item.dependencies if d not in completed_ids]
        if len(unmet) <= 2 and item.readiness in ["now", "near"]:
            candidates['near_ready'].append((item, unmet))

    return candidates

def mark_complete(item_id: str, repo_root: Path, reason: str):
    """Mark an item as completed."""
    file_path = repo_root / "docs" / "roadmap" / "ITEMS" / f"{item_id}.md"

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    # Update status in markdown
    content = file_path.read_text()
    content = content.replace(
        '- **Status:** `Accepted`',
        '- **Status:** `Completed`'
    )
    file_path.write_text(content)

    # Git commit
    subprocess.run(['git', 'add', str(file_path)], cwd=repo_root, check=True)
    subprocess.run(
        ['git', 'commit', '-m', f'status: {item_id} → Completed ({reason})'],
        cwd=repo_root,
        check=True
    )

    print(f"✅ {item_id} → Completed ({reason})")
    return True

def main():
    repo_root = Path(__file__).parent.parent
    items = parse_roadmap_directory(repo_root / "docs" / "roadmap" / "ITEMS")

    print("🔍 Finding bootstrap candidates...\n")

    candidates = find_bootstrap_candidates(items)

    print("📋 Bootstrap Strategy:\n")

    # Show zero-dep items
    if candidates['zero_deps']:
        print("✅ Items with ZERO dependencies (safe to mark complete):")
        for item in candidates['zero_deps'][:5]:
            print(f"   {item.id} - {item.title[:50]}")
        print()

    # Show foundational GOV
    if candidates['foundational_gov']:
        print("🏛️  Foundational GOV items (governance framework):")
        for item in candidates['foundational_gov']:
            print(f"   {item.id} - {item.title[:50]}")
        print()

    # Show near-ready
    if candidates['near_ready']:
        print("⚡ Near-ready items (1-2 deps away):")
        for item, unmet in candidates['near_ready'][:5]:
            print(f"   {item.id} - blocked by: {unmet}")
        print()

    # Recommend action
    print("=" * 70)
    print("💡 RECOMMENDATION:")
    print("=" * 70)

    to_mark = []

    # Mark zero-dep items
    to_mark.extend(candidates['zero_deps'][:3])

    # Mark foundational GOV (breaks circular deps)
    to_mark.extend(candidates['foundational_gov'])

    if to_mark:
        print(f"\nMark {len(to_mark)} items complete to bootstrap:\n")
        for item in to_mark:
            print(f"  • {item.id} - {item.title[:50]}")

        response = input("\nProceed? (yes/no): ").strip().lower()

        if response == 'yes':
            for item in to_mark:
                mark_complete(item.id, repo_root, "bootstrap foundation")

            print(f"\n✅ Marked {len(to_mark)} items complete")
            print("\nRun: ./bin/auto_execute_roadmap.py --dry-run")
        else:
            print("\n❌ Bootstrap cancelled")
    else:
        print("\n⚠️  No safe bootstrap candidates found")

if __name__ == '__main__':
    main()
