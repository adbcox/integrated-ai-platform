#!/usr/bin/env python3
"""
Validate roadmap consistency across all layers.

Checks for contradictions between:
- Item files (Layer 1, canonical)
- Dependency graph (Layer 2, derived)
- next_pull.json (Layer 2, derived)
- ROADMAP_MASTER.md (Layer 3, derived)
- ROADMAP_INDEX.md (Layer 3, derived)

Reports all found contradictions and exit code 1 if any found.
"""

import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set
import yaml

@dataclass
class RoadmapItemStatus:
    """Status of a single roadmap item"""
    item_id: str
    status: str = None
    archive_status: str = None
    source: str = None  # where this status was read from

@dataclass
class ConsistencyReport:
    """Report of consistency check results"""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    archived_items: Set[str] = field(default_factory=set)
    active_items: Set[str] = field(default_factory=set)

    def add_error(self, msg: str):
        self.errors.append(msg)

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def has_issues(self) -> bool:
        return bool(self.errors)

def load_item_files(items_dir: Path) -> Dict[str, RoadmapItemStatus]:
    """Load all item files and extract status"""
    items = {}

    for item_file in sorted(items_dir.glob("RM-*.yaml")):
        item_id = item_file.stem
        content = item_file.read_text()

        # Extract status and archive_status using regex
        status_match = re.search(r'status:\s*["\']?([^"\'\n]+)["\']?', content)
        archive_match = re.search(r'archive_status:\s*["\']?([^"\'\n]+)["\']?', content)

        status = status_match.group(1).strip() if status_match else "unknown"
        archive_status = archive_match.group(1).strip() if archive_match else "unknown"

        items[item_id] = RoadmapItemStatus(
            item_id=item_id,
            status=status,
            archive_status=archive_status,
            source="item_file"
        )

    return items

def load_dependency_graph(graph_file: Path) -> tuple[Set[str], Set[str], Set[str]]:
    """Load dependency graph and extract archived/eligible/blocked items."""
    data = yaml.safe_load(graph_file.read_text()) or {}
    blocking = data.get("blocking_analysis") or {}
    archived = set(blocking.get("archived_items") or [])
    eligible = set(blocking.get("eligible_items") or [])
    blocked = set(blocking.get("blocked_items") or [])
    return archived, eligible, blocked

def load_next_pull(next_pull_file: Path) -> tuple[Set[str], Set[str]]:
    """Load next_pull.json and extract archived/eligible items"""
    data = json.loads(next_pull_file.read_text())

    archived = set(data.get('archived_items', []))

    # next_pull_candidates contains eligible items
    eligible = set()
    for item in data.get('next_pull_candidates', []):
        if isinstance(item, dict) and 'id' in item:
            eligible.add(item['id'])
        elif isinstance(item, str):
            eligible.add(item)

    return archived, eligible

def check_summary_docs(roadmap_master: Path, roadmap_index: Path) -> tuple[Set[str], Set[str]]:
    """Check that archived items don't appear in active sections of summary docs"""
    issues = []

    # Check ROADMAP_MASTER.md "Next active initiatives" section
    master_content = roadmap_master.read_text()
    next_active_section = re.search(
        r'(?:Next active initiatives|Active initiatives)(.*?)(?:\n\n|\n##|\Z)',
        master_content,
        re.DOTALL | re.IGNORECASE
    )

    if next_active_section:
        section_text = next_active_section.group(1)
        # Find all RM-* items in this section
        items_in_active = re.findall(r'`?RM-[A-Z]+-\d+`?', section_text)

        # These items appear in "active" section
        return set(items_in_active), issues

    return set(), issues

def validate_consistency(repo_root: Path) -> ConsistencyReport:
    """Main validation function"""
    report = ConsistencyReport()

    # Load all data
    items_dir = repo_root / "docs/roadmap/items"
    graph_file = repo_root / "governance/roadmap_dependency_graph.v1.yaml"
    next_pull_file = repo_root / "artifacts/planning/next_pull.json"
    roadmap_master = repo_root / "docs/roadmap/ROADMAP_MASTER.md"
    roadmap_index = repo_root / "docs/roadmap/ROADMAP_INDEX.md"

    item_statuses = load_item_files(items_dir)

    # Categorize items from Layer 1 (canonical)
    for item_id, status_obj in item_statuses.items():
        if status_obj.archive_status == "archived":
            report.archived_items.add(item_id)
        else:
            report.active_items.add(item_id)

    # Check Layer 2: Dependency graph
    if graph_file.exists():
        graph_archived, graph_eligible, graph_blocked = load_dependency_graph(graph_file)

        # Check for archived items appearing in eligible_items
        archived_in_eligible = graph_eligible & report.archived_items
        if archived_in_eligible:
            for item_id in sorted(archived_in_eligible):
                report.add_error(
                    f"LAYER2 ERROR: {item_id} is archived (Layer 1) but appears in "
                    f"eligible_items (dependency graph)"
                )

        # Check for archived items appearing in blocked_items
        archived_in_blocked = graph_blocked & report.archived_items
        if archived_in_blocked:
            for item_id in sorted(archived_in_blocked):
                report.add_warning(
                    f"LAYER2 WARNING: {item_id} is archived (Layer 1) but appears in "
                    f"blocked_items (dependency graph)"
                )

    # Check Layer 2: next_pull.json
    if next_pull_file.exists():
        pull_archived, pull_eligible = load_next_pull(next_pull_file)
        next_pull_data = json.loads(next_pull_file.read_text())
        blocked_placeholder = set(next_pull_data.get("blocked_placeholder_items", []))

        # Check for archived items appearing in eligible
        archived_in_pull = pull_eligible & report.archived_items
        if archived_in_pull:
            for item_id in sorted(archived_in_pull):
                report.add_error(
                    f"LAYER2 ERROR: {item_id} is archived (Layer 1) but appears in "
                    f"next_pull_candidates (next_pull.json)"
                )

        # Check for terminal-status items appearing in eligible candidates
        for item_id in sorted(pull_eligible):
            status_obj = item_statuses.get(item_id)
            if not status_obj:
                report.add_error(
                    f"LAYER2 ERROR: {item_id} appears in next_pull_candidates but has no canonical item file"
                )
                continue

            item_status = (status_obj.status or "").strip().lower()
            item_archive = (status_obj.archive_status or "").strip().lower()
            if item_status in {"complete", "completed"}:
                report.add_error(
                    f"LAYER2 ERROR: {item_id} has terminal status '{status_obj.status}' but appears in next_pull_candidates"
                )
            if item_archive in {"archived", "ready_for_archive"}:
                report.add_error(
                    f"LAYER2 ERROR: {item_id} has archive_status '{status_obj.archive_status}' but appears in next_pull_candidates"
                )

        # Ensure placeholder-conflicted items are not leaked into pull queue
        placeholder_leak = blocked_placeholder & pull_eligible
        if placeholder_leak:
            for item_id in sorted(placeholder_leak):
                report.add_error(
                    f"LAYER2 ERROR: {item_id} is blocked_placeholder but appears in next_pull_candidates"
                )

    # Check Layer 3: Summary docs
    if roadmap_master.exists():
        items_in_active, _ = check_summary_docs(roadmap_master, roadmap_index)
        archived_in_summary = items_in_active & report.archived_items
        if archived_in_summary:
            for item_id in sorted(archived_in_summary):
                report.add_error(
                    f"LAYER3 ERROR: {item_id} is archived (Layer 1) but appears in "
                    f"active sections (ROADMAP_MASTER.md or ROADMAP_INDEX.md)"
                )

    return report

def main():
    repo_root = Path(__file__).parent.parent

    print("=" * 70)
    print("Roadmap Consistency Validation")
    print("=" * 70)

    report = validate_consistency(repo_root)

    if report.errors:
        print("\n❌ ERRORS FOUND:")
        for error in sorted(report.errors):
            print(f"  - {error}")

    if report.warnings:
        print("\n⚠️  WARNINGS:")
        for warning in sorted(report.warnings):
            print(f"  - {warning}")

    if not report.errors and not report.warnings:
        print("\n✅ Consistency check PASSED")

    print("\nStatus Summary:")
    print(f"  Archived items: {len(report.archived_items)}")
    print(f"  Active items: {len(report.active_items)}")
    print("\nArchived items:")
    for item_id in sorted(report.archived_items):
        print(f"  - {item_id}")

    if report.active_items:
        print("\nActive items:")
        for item_id in sorted(report.active_items):
            print(f"  - {item_id}")

    print("=" * 70)

    return 1 if report.has_issues() else 0

if __name__ == "__main__":
    sys.exit(main())
