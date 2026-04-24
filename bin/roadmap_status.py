#!/usr/bin/env python3
"""Roadmap status dashboard (RM-GOV-001 governance metrics)."""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from bin.roadmap_parser import parse_roadmap_directory, infer_dependencies, RoadmapItem


class RoadmapDashboard:
    """Display roadmap governance metrics per RM-GOV-001."""

    STATUS_GROUPS = {
        "active": ["In progress", "Validating"],
        "completed": ["Completed"],
        "planned": ["Planned", "Decomposing", "Execution-ready"],
        "pending": ["Proposed", "Accepted"],
        "deferred": ["Deferred", "Frozen", "Rejected"],
    }

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.roadmap_dir = repo_root / "docs" / "roadmap"

    def calculate_metrics(self, items: List[RoadmapItem]) -> Dict[str, Any]:
        """Calculate governance metrics."""
        metrics = {
            "total": len(items),
            "by_status": {},
            "by_priority": {},
            "by_category": {},
            "strategic_value_distribution": [0] * 6,  # 0-5 scores
            "architecture_fit_distribution": [0] * 6,
            "execution_risk_distribution": [0] * 6,
            "readiness_distribution": {},
            "grouped_bundles": 0,
            "dependencies_unmet": 0,
            "critical_path_items": [],
        }

        # Group items by status
        for item in items:
            status = item.status
            metrics["by_status"][status] = metrics["by_status"].get(status, 0) + 1

            # Priority distribution
            priority = item.priority_class
            metrics["by_priority"][priority] = metrics["by_priority"].get(priority, 0) + 1

            # Category distribution
            cat = item.category
            metrics["by_category"][cat] = metrics["by_category"].get(cat, 0) + 1

            # Scoring distributions
            metrics["strategic_value_distribution"][item.strategic_value] += 1
            metrics["architecture_fit_distribution"][item.architecture_fit] += 1
            metrics["execution_risk_distribution"][item.execution_risk] += 1

            # Readiness
            readiness = item.readiness
            metrics["readiness_distribution"][readiness] = metrics["readiness_distribution"].get(readiness, 0) + 1

            # Grouped bundles
            if item.grouping_candidates:
                metrics["grouped_bundles"] += 1

            # Critical path (high strategic value, unmet dependencies)
            if item.strategic_value >= 4 and item.dependencies:
                unmet = [d for d in item.dependencies if any(i.id == d and i.status != "Completed" for i in items)]
                if unmet:
                    metrics["critical_path_items"].append((item.id, unmet))
                    metrics["dependencies_unmet"] += len(unmet)

        return metrics

    def print_header(self) -> None:
        """Print dashboard header."""
        print("\n" + "="*80)
        print("📊 ROADMAP GOVERNANCE DASHBOARD (RM-GOV-001)")
        print("="*80)

    def print_execution_status(self, metrics: Dict[str, Any]) -> None:
        """Print execution status breakdown."""
        print("\n📈 Execution Status")
        print("-"*80)

        active = sum(metrics["by_status"].get(s, 0) for s in self.STATUS_GROUPS["active"])
        completed = metrics["by_status"].get("Completed", 0)
        planned = sum(metrics["by_status"].get(s, 0) for s in self.STATUS_GROUPS["planned"])
        pending = sum(metrics["by_status"].get(s, 0) for s in self.STATUS_GROUPS["pending"])

        total = metrics["total"]
        active_pct = (active / total * 100) if total else 0
        completed_pct = (completed / total * 100) if total else 0

        print(f"   🔄 Active:    {active:3d} ({active_pct:5.1f}%)")
        print(f"   ✅ Completed: {completed:3d} ({completed_pct:5.1f}%)")
        print(f"   📋 Planned:   {planned:3d}")
        print(f"   ⏳ Pending:    {pending:3d}")

        # Show status breakdown
        if metrics["by_status"]:
            print(f"\n   Status breakdown:")
            for status in sorted(metrics["by_status"].keys()):
                count = metrics["by_status"][status]
                print(f"     • {status}: {count}")

    def print_priority_distribution(self, metrics: Dict[str, Any]) -> None:
        """Print priority class distribution."""
        print("\n🎯 Priority Distribution (per STANDARDS.md §5A)")
        print("-"*80)

        for pclass in ["P0", "P1", "P2", "P3", "P4"]:
            count = metrics["by_priority"].get(pclass, 0)
            bar = "█" * (count // 2) if count > 0 else ""
            print(f"   {pclass}: {count:3d} {bar}")

    def print_governance_scores(self, metrics: Dict[str, Any]) -> None:
        """Print governance scoring metrics."""
        print("\n🏆 Governance Scoring (1-5 scale, per STANDARDS.md §7)")
        print("-"*80)

        def score_dist(dist: List[int]) -> str:
            total = sum(dist)
            if total == 0:
                return "No items"
            # Calculate weighted average
            avg = sum(i * v for i, v in enumerate(dist)) / total if total else 0
            return f"Avg: {avg:.1f} | Distribution: {dist[1:]}"

        print(f"   Strategic value:    {score_dist(metrics['strategic_value_distribution'])}")
        print(f"   Architecture fit:   {score_dist(metrics['architecture_fit_distribution'])}")
        print(f"   Execution risk:     {score_dist(metrics['execution_risk_distribution'])}")

    def print_readiness(self, metrics: Dict[str, Any]) -> None:
        """Print readiness analysis."""
        print("\n📊 Readiness Status (per STANDARDS.md §7)")
        print("-"*80)

        readiness_icons = {"now": "⚡", "near": "→", "later": "⏳", "blocked": "🚫"}
        for readiness in ["now", "near", "later", "blocked"]:
            count = metrics["readiness_distribution"].get(readiness, 0)
            icon = readiness_icons.get(readiness, "?")
            print(f"   {icon} {readiness:8s}: {count:3d}")

    def print_category_breakdown(self, metrics: Dict[str, Any]) -> None:
        """Print breakdown by category."""
        print("\n📂 Items by Category (STANDARDS.md §2)")
        print("-"*80)

        for cat in sorted(metrics["by_category"].keys()):
            count = metrics["by_category"][cat]
            print(f"   {cat:12s}: {count:3d}")

    def print_critical_path(self, metrics: Dict[str, Any]) -> None:
        """Print critical path analysis."""
        if not metrics["critical_path_items"]:
            return

        print("\n⚠️  Critical Path Blockers (P3+ with unmet deps)")
        print("-"*80)

        for item_id, unmet_deps in metrics["critical_path_items"][:10]:
            print(f"   {item_id}: Blocked by {', '.join(unmet_deps)}")

        if len(metrics["critical_path_items"]) > 10:
            print(f"   ... and {len(metrics['critical_path_items']) - 10} more")

    def print_grouped_bundles(self, metrics: Dict[str, Any]) -> None:
        """Print grouped execution opportunities."""
        if metrics["grouped_bundles"] == 0:
            return

        print("\n📦 Grouped Execution Opportunities")
        print("-"*80)
        print(f"   {metrics['grouped_bundles']} items have grouping candidates")
        print(f"   (Can reduce shared-touch via coordinated execution)")

    def show_dashboard(self) -> None:
        """Display complete dashboard."""
        items = parse_roadmap_directory(self.roadmap_dir)
        infer_dependencies(items)
        metrics = self.calculate_metrics(items)

        self.print_header()
        self.print_execution_status(metrics)
        self.print_priority_distribution(metrics)
        self.print_governance_scores(metrics)
        self.print_readiness(metrics)
        self.print_category_breakdown(metrics)
        self.print_grouped_bundles(metrics)
        self.print_critical_path(metrics)

        print("\n" + "="*80)
        print(f"Last updated: {datetime.utcnow().isoformat()}")
        print("Reference: docs/roadmap/STANDARDS.md for governance rules")
        print("="*80 + "\n")

    def export_metrics(self, output_path: Path) -> None:
        """Export metrics to JSON."""
        items = parse_roadmap_directory(self.roadmap_dir)
        infer_dependencies(items)
        metrics = self.calculate_metrics(items)

        export_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_items": metrics["total"],
                "execution_status": metrics["by_status"],
                "priority_distribution": metrics["by_priority"],
                "category_distribution": metrics["by_category"],
                "readiness_distribution": metrics["readiness_distribution"],
                "grouped_bundles": metrics["grouped_bundles"],
                "unmet_dependencies": metrics["dependencies_unmet"],
            },
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"✅ Exported to {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Roadmap governance dashboard")
    parser.add_argument("--export", type=Path, help="Export metrics to JSON")

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    dashboard = RoadmapDashboard(repo_root)

    if args.export:
        dashboard.export_metrics(args.export)
    else:
        dashboard.show_dashboard()


if __name__ == "__main__":
    main()
