#!/usr/bin/env python3
"""Parse roadmap markdown files with YAML frontmatter (RM-GOV-001 compliance)."""

import sys
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml


@dataclass
class ExecutionStatus:
    """Tracks execution status per RM-GOV-001."""
    status: str  # Proposed, Accepted, Decomposing, Planned, Execution-ready, In progress, Validating, Completed, Deferred, Frozen, Rejected
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    subtasks_completed: int = 0
    subtasks_total: int = 0
    last_updated: Optional[str] = None
    blocker: Optional[str] = None
    assigned_executor: Optional[str] = None
    model_used: Optional[str] = None
    commits: List[str] = field(default_factory=list)
    validation_status: Dict[str, str] = field(default_factory=dict)


@dataclass
class RoadmapItem:
    """Represents a roadmap item with execution tracking."""
    id: str
    title: str
    category: str
    item_type: str  # Program, System, Feature, Enhancement
    description: str

    # Governance fields (per STANDARDS.md section 13)
    status: str  # From standard status set
    priority: str  # Critical, High, Medium, Low
    priority_class: str  # P0-P4
    queue_rank: int = 999
    target_horizon: str = "later"  # now, next, soon, later, parking-lot
    loe: str = "M"  # XS, S, M, L, XL, XXL

    # Scoring fields
    strategic_value: int = 3  # 1-5
    architecture_fit: int = 3
    execution_risk: int = 3
    dependency_burden: int = 3
    readiness: str = "blocked"  # now, near, later, blocked

    # Impact transparency (per STANDARDS.md section 10)
    affected_systems: List[str] = field(default_factory=list)
    affected_subsystems: List[str] = field(default_factory=list)
    expected_file_families: List[str] = field(default_factory=list)
    cmdb_links: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    # Grouping (per STANDARDS.md section 12)
    grouping_candidates: List[str] = field(default_factory=list)

    # Execution tracking (RM-GOV-001 compliance)
    execution: ExecutionStatus = field(default_factory=lambda: ExecutionStatus(status="Accepted"))

    # File handling
    file_path: Optional[str] = None
    markdown_content: str = ""  # Full markdown after frontmatter
    frontmatter: Dict[str, Any] = field(default_factory=dict)


def extract_bullet_list_metadata(content: str) -> Dict[str, Any]:
    """Extract metadata from bullet-list format (- **Field:** `value`)."""
    metadata = {}

    patterns = {
        'id': r'- \*\*ID:\*\*\s*`([^`]+)`',
        'title': r'- \*\*Title:\*\*\s*(.+?)(?:\n|$)',
        'category': r'- \*\*Category:\*\*\s*`([^`]+)`',
        'item_type': r'- \*\*Type:\*\*\s*`([^`]+)`',
        'status': r'- \*\*Status:\*\*\s*`([^`]+)`',
        'maturity': r'- \*\*Maturity:\*\*\s*`([^`]+)`',
        'priority': r'- \*\*Priority:\*\*\s*`([^`]+)`',
        'priority_class': r'- \*\*Priority class:\*\*\s*`([^`]+)`',
        'queue_rank': r'- \*\*Queue rank:\*\*\s*`?(\d+)`?',
        'target_horizon': r'- \*\*Target horizon:\*\*\s*`([^`]+)`',
        'loe': r'- \*\*LOE:\*\*\s*`([^`]+)`',
        'strategic_value': r'- \*\*Strategic value:\*\*\s*`?(\d+)`?',
        'architecture_fit': r'- \*\*Architecture fit:\*\*\s*`?(\d+)`?',
        'execution_risk': r'- \*\*Execution risk:\*\*\s*`?(\d+)`?',
        'dependency_burden': r'- \*\*Dependency burden:\*\*\s*`?(\d+)`?',
        'readiness': r'- \*\*Readiness:\*\*\s*`([^`]+)`',
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            value = match.group(1).strip()
            metadata[field] = value

    return metadata


def parse_markdown_sections(content: str, item_id: str) -> Dict[str, str]:
    """Extract Description, Key requirements, Affected systems sections."""
    sections = {}

    desc_match = re.search(r'^## Description\s*\n+(.+?)(?=\n^##|$)', content, re.MULTILINE | re.DOTALL)
    if desc_match:
        sections['description'] = desc_match.group(1).strip()[:500]

    req_match = re.search(r'^## Key requirements\s*\n+(.+?)(?=\n^##|$)', content, re.MULTILINE | re.DOTALL)
    if req_match:
        sections['requirements'] = req_match.group(1).strip()

    affected_match = re.search(r'^## Affected systems\s*\n+(.+?)(?=\n^##|$)', content, re.MULTILINE | re.DOTALL)
    if affected_match:
        affected_text = affected_match.group(1).strip()
        systems = re.findall(r'- (.+?)(?:\n|$)', affected_text)
        sections['affected_systems'] = systems

    # Extract dependencies from content (exclude self-reference)
    dep_ids = set()
    for match in re.finditer(r'(RM-[A-Z]+-\d+)', content):
        dep_id = match.group(1)
        if dep_id != item_id:  # Exclude self-reference
            dep_ids.add(dep_id)
    if dep_ids:
        sections['dependencies'] = sorted(list(dep_ids))

    return sections


def parse_roadmap_file(file_path: Path) -> Optional[RoadmapItem]:
    """Parse a roadmap markdown file (bullet-list format) into a RoadmapItem."""
    try:
        content = file_path.read_text()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}", file=sys.stderr)
        return None

    # Extract ID from filename
    item_id = re.search(r'(RM-[A-Z]+-\d+)', file_path.name)
    if not item_id:
        return None
    item_id = item_id.group(1)

    # Extract bullet-list metadata
    bullet_meta = extract_bullet_list_metadata(content)

    # Extract markdown sections
    sections = parse_markdown_sections(content, item_id)

    # Parse execution status (from bullet list if present, else defaults)
    execution = ExecutionStatus(
        status=bullet_meta.get('status', 'Accepted'),
    )

    # Build RoadmapItem
    item = RoadmapItem(
        id=item_id,
        title=bullet_meta.get('title', item_id),
        category=bullet_meta.get('category', 'CORE'),
        item_type=bullet_meta.get('item_type', 'Feature'),
        description=sections.get('description', ''),

        # Status fields from bullet list
        status=bullet_meta.get('status', 'Accepted'),
        priority=bullet_meta.get('priority', 'Medium'),
        priority_class=bullet_meta.get('priority_class', 'P2'),
        queue_rank=int(bullet_meta.get('queue_rank', 999)),
        target_horizon=bullet_meta.get('target_horizon', 'later'),
        loe=bullet_meta.get('loe', 'M'),

        # Scoring from bullet list
        strategic_value=int(bullet_meta.get('strategic_value', 3)),
        architecture_fit=int(bullet_meta.get('architecture_fit', 3)),
        execution_risk=int(bullet_meta.get('execution_risk', 3)),
        dependency_burden=int(bullet_meta.get('dependency_burden', 3)),
        readiness=bullet_meta.get('readiness', 'blocked'),

        # Impact from sections
        affected_systems=sections.get('affected_systems', []),
        affected_subsystems=[],
        expected_file_families=[],
        cmdb_links=[],
        dependencies=sections.get('dependencies', []),
        grouping_candidates=[],

        # Execution tracking
        execution=execution,

        # Content
        file_path=str(file_path),
        markdown_content=content,
        frontmatter=bullet_meta,
    )

    return item


def parse_roadmap_directory(roadmap_dir: Path) -> List[RoadmapItem]:
    """Parse all roadmap files from items directory."""
    items = []
    items_dir = roadmap_dir

    if not items_dir.exists():
        print(f"⚠️  Items directory not found: {items_dir}", file=sys.stderr)
        return items

    for md_file in sorted(items_dir.glob('RM-*.md')):
        item = parse_roadmap_file(md_file)
        if item:
            items.append(item)

    return items


def infer_dependencies(items: List[RoadmapItem]) -> None:
    """Infer dependencies based on referenced IDs."""
    id_map = {item.id: item for item in items}

    for item in items:
        deps = set(item.dependencies or [])

        # Extract referenced IDs from description
        for match in re.finditer(r'(RM-[A-Z]+-\d+)', item.description):
            ref_id = match.group(1)
            if ref_id in id_map and ref_id != item.id:
                deps.add(ref_id)

        item.dependencies = sorted(list(deps))


def update_frontmatter(file_path: Path, updates: Dict[str, Any]) -> bool:
    """Update frontmatter in-place while preserving markdown content."""
    try:
        content = file_path.read_text()
        frontmatter, markdown = extract_frontmatter_and_content(content)

        if frontmatter is None:
            # No frontmatter, create it
            frontmatter = {}

        # Deep merge updates
        for key, value in updates.items():
            if key in frontmatter and isinstance(frontmatter[key], dict) and isinstance(value, dict):
                frontmatter[key].update(value)
            else:
                frontmatter[key] = value

        # Serialize frontmatter
        yaml_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

        # Reconstruct file
        new_content = f"---\n{yaml_str}---\n\n{markdown}"
        file_path.write_text(new_content)

        return True
    except Exception as e:
        print(f"❌ Error updating frontmatter: {e}", file=sys.stderr)
        return False


def print_item_summary(item: RoadmapItem) -> None:
    """Print a formatted summary of a roadmap item."""
    print(f"\n📋 {item.id} — {item.title}")
    print(f"   Type: {item.item_type} | Category: {item.category}")
    print(f"   Status: {item.status} | Priority: {item.priority} ({item.priority_class})")
    print(f"   Execution: {item.execution.status}")
    if item.dependencies:
        print(f"   Dependencies: {', '.join(item.dependencies)}")
    if item.affected_systems:
        print(f"   Affected systems: {', '.join(item.affected_systems)}")


def detect_cycles(items: List[RoadmapItem]) -> List[List[str]]:
    """Detect circular dependencies using DFS. Returns list of cycles."""
    id_to_item = {item.id: item for item in items}
    visited = set()
    path = []
    path_set = set()
    cycles = []

    def dfs(node_id: str) -> None:
        if node_id in path_set:
            # Found a cycle — extract the cycle portion
            cycle_start = path.index(node_id)
            cycles.append(path[cycle_start:] + [node_id])
            return
        if node_id in visited:
            return
        visited.add(node_id)
        path.append(node_id)
        path_set.add(node_id)
        item = id_to_item.get(node_id)
        if item:
            for dep_id in item.dependencies:
                if dep_id in id_to_item:
                    dfs(dep_id)
        path.pop()
        path_set.discard(node_id)

    for item in items:
        if item.id not in visited:
            dfs(item.id)

    return cycles


if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent
    roadmap_dir = repo_root / "docs" / "roadmap" / "ITEMS"

    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        items = parse_roadmap_directory(roadmap_dir)
        infer_dependencies(items)

        print(f"✅ Parsed {len(items)} roadmap items\n")
        for item in items:
            print_item_summary(item)
    else:
        if len(sys.argv) < 2:
            print("Usage: roadmap_parser.py [--all|filename.md]")
            sys.exit(1)

        target = Path(sys.argv[1])
        if not target.is_absolute():
            target = roadmap_dir / target

        item = parse_roadmap_file(target)
        if item:
            print_item_summary(item)
            print(f"\nDescription: {item.description}")
            if item.affected_systems:
                print(f"Affected systems: {', '.join(item.affected_systems)}")
