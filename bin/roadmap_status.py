#!/usr/bin/env python3
"""Dashboard for roadmap execution progress."""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from bin.roadmap_parser import parse_roadmap_directory, infer_dependencies


class RoadmapStatusDashboard:
    """Display roadmap execution progress."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.roadmap_dir = repo_root / "docs" / "roadmap"
        self.status_file = self.roadmap_dir / "STATUS.yaml"

    def load_status(self) -> Dict[str, Any]:
        """Load execution status."""
        if self.status_file.exists():
            try:
                with open(self.status_file) as f:
                    return yaml.safe_load(f) or {"items": {}, "execution_log": []}
            except Exception as e:
                print(f"⚠️  Error loading status: {e}", file=sys.stderr)
                return {"items": {}, "execution_log": []}
        return {"items": {}, "execution_log": []}

    def calculate_metrics(self, items: List[Any], status: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate progress metrics."""
        total = len(items)
        completed = sum(1 for item in items if status.get("items", {}).get(item.id, {}).get("status") == "completed")
        in_progress = sum(1 for item in items if status.get("items", {}).get(item.id, {}).get("status") == "in_progress")
        blocked = sum(1 for item in items if status.get("items", {}).get(item.id, {}).get("status") == "blocked")
        planned = total - completed - in_progress - blocked

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "blocked": blocked,
            "planned": planned,
            "completion_percent": (completed / total * 100) if total > 0 else 0,
        }

    def print_header(self) -> None:
        """Print dashboard header."""
        print("\n" + "=" * 80)
        print("📊 ROADMAP EXECUTION DASHBOARD")
        print("=" * 80)

    def print_metrics(self, metrics: Dict[str, Any]) -> None:
        """Print progress metrics."""
        print(f"\n📈 Overall Progress")
        print(f"   Total Items: {metrics['total']}")
        print(f"   ✅ Completed:  {metrics['completed']:3d} ({metrics['completion_percent']:5.1f}%)")
        print(f"   🔄 In Progress: {metrics['in_progress']:3d}")
        print(f"   ⏸️  Blocked:    {metrics['blocked']:3d}")
        print(f"   📋 Planned:    {metrics['planned']:3d}")

    def print_status_by_item(
        self,
        items: List[Any],
        status: Dict[str, Any],
    ) -> None:
        """Print detailed status for each item."""
        print(f"\n📋 Item Status")
        print("-" * 80)

        # Group by status
        by_status = {"completed": [], "in_progress": [], "blocked": [], "planned": []}
        for item in items:
            item_status = status.get("items", {}).get(item.id, {}).get("status", "planned")
            by_status[item_status].append(item)

        # Print by status with emojis
        status_icons = {
            "completed": "✅",
            "in_progress": "🔄",
            "blocked": "⏸️",
            "planned": "📋",
        }

        for stat_key in ["in_progress", "completed", "blocked", "planned"]:
            items_list = by_status[stat_key]
            if items_list:
                icon = status_icons[stat_key]
                print(f"\n{icon} {stat_key.upper()} ({len(items_list)})")
                for item in items_list[:10]:  # Show first 10 per status
                    item_meta = status.get("items", {}).get(item.id, {})
                    deps_str = f" [deps: {', '.join(item.dependencies)}]" if item.dependencies else ""
                    notes = item_meta.get("notes", "")
                    notes_str = f" — {notes}" if notes else ""
                    print(f"   • {item.id}: {item.title[:50]}{deps_str}{notes_str}")

                if len(items_list) > 10:
                    print(f"   ... and {len(items_list) - 10} more")

    def print_recent_activity(self, status: Dict[str, Any]) -> None:
        """Print recent execution activity."""
        log = status.get("execution_log", [])
        if not log:
            return

        print(f"\n📝 Recent Activity (last 10 entries)")
        print("-" * 80)

        for entry in log[-10:]:
            timestamp = entry.get("timestamp", "")
            item_id = entry.get("item_id", "")
            stat = entry.get("status", "")
            notes = entry.get("notes", "")

            # Extract time from ISO timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = timestamp[:19]

            status_icon = "✅" if stat == "completed" else "🔄" if stat == "in_progress" else "⏸️" if stat == "blocked" else "📋"

            details = f"{notes}" if notes else ""
            print(f"   {time_str} | {status_icon} {item_id:15s} → {stat:12s} {details}")

    def print_blocked_items_with_reasons(
        self,
        items: List[Any],
        status: Dict[str, Any],
    ) -> None:
        """Print blocked items and their blocking reasons."""
        blocked = [
            item for item in items
            if status.get("items", {}).get(item.id, {}).get("status") == "blocked"
        ]

        if not blocked:
            return

        print(f"\n🚫 Blocked Items ({len(blocked)})")
        print("-" * 80)

        for item in blocked:
            item_meta = status.get("items", {}).get(item.id, {})
            reason = item_meta.get("notes", "Unknown reason")
            print(f"   • {item.id}: {reason}")
            if item.dependencies:
                print(f"      Dependencies: {', '.join(item.dependencies)}")

    def show_dashboard(self) -> None:
        """Display the full dashboard."""
        # Load data
        items = parse_roadmap_directory(self.roadmap_dir)
        infer_dependencies(items)
        status = self.load_status()

        # Calculate metrics
        metrics = self.calculate_metrics(items, status)

        # Print dashboard
        self.print_header()
        self.print_metrics(metrics)
        self.print_status_by_item(items, status)
        self.print_blocked_items_with_reasons(items, status)
        self.print_recent_activity(status)

        print("\n" + "=" * 80)
        print(f"Last updated: {datetime.utcnow().isoformat()}")
        print("=" * 80 + "\n")

    def export_json(self, output_path: Path) -> None:
        """Export dashboard data as JSON."""
        items = parse_roadmap_directory(self.roadmap_dir)
        infer_dependencies(items)
        status = self.load_status()
        metrics = self.calculate_metrics(items, status)

        # Build export structure
        export_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total": metrics["total"],
                "completed": metrics["completed"],
                "in_progress": metrics["in_progress"],
                "blocked": metrics["blocked"],
                "planned": metrics["planned"],
                "completion_percent": metrics["completion_percent"],
            },
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "status": status.get("items", {}).get(item.id, {}).get("status", "planned"),
                    "dependencies": item.dependencies,
                    "priority": item.priority,
                }
                for item in items
            ],
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"✅ Exported dashboard data to {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Roadmap execution status dashboard")
    parser.add_argument(
        "--export",
        type=Path,
        help="Export data to JSON file",
    )

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    dashboard = RoadmapStatusDashboard(repo_root)

    if args.export:
        dashboard.export_json(args.export)
    else:
        dashboard.show_dashboard()


if __name__ == "__main__":
    main()
