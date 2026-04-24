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


def extract_frontmatter_and_content(content: str) -> tuple[Optional[Dict[str, Any]], str]:
    """Extract YAML frontmatter and remaining markdown."""
    if not content.startswith("---"):
        return None, content

    try:
        # Find closing --- (must be on its own line)
        lines = content.split('\n')
        end_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        if end_idx is None:
            return None, content

        frontmatter_str = '\n'.join(lines[1:end_idx])
        markdown = '\n'.join(lines[end_idx+1:])

        # Parse YAML
        try:
            frontmatter = yaml.safe_load(frontmatter_str) if frontmatter_str.strip() else {}
            return frontmatter or {}, markdown.lstrip('\n')
        except yaml.YAMLError as e:
            print(f"⚠️  YAML parse error: {e}", file=sys.stderr)
            return {}, markdown.lstrip('\n')
    except Exception as e:
        print(f"⚠️  Frontmatter extraction error: {e}", file=sys.stderr)
        return None, content


def parse_markdown_metadata(content: str, item_id: str) -> Dict[str, Any]:
    """Extract metadata from markdown sections."""
    meta = {}

    # Extract title from first # header or bold section
    title_match = re.search(r'\*\*(.+?)\*\*|^#\s+(.+?)$', content, re.MULTILINE)
    if title_match:
        meta['title'] = title_match.group(1) or title_match.group(2)
    else:
        meta['title'] = item_id

    # Extract description (from first non-header section)
    desc_match = re.search(r'^## (?:Objective|Description)\s*\n+(.+?)(?:^##|$)', content, re.MULTILINE | re.DOTALL)
    if desc_match:
        meta['description'] = desc_match.group(1).strip()[:200]

    return meta


def parse_roadmap_file(file_path: Path) -> Optional[RoadmapItem]:
    """Parse a roadmap markdown file into a RoadmapItem."""
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

    # Extract frontmatter and markdown
    frontmatter, markdown = extract_frontmatter_and_content(content)

    # Extract metadata from markdown if not in frontmatter
    markdown_meta = parse_markdown_metadata(markdown, item_id)

    # Build item with frontmatter as primary source
    fm = frontmatter or {}

    # Parse execution status from frontmatter
    exec_data = fm.get('execution', {})
    execution = ExecutionStatus(
        status=exec_data.get('status', 'Accepted'),
        started_at=exec_data.get('started_at'),
        completed_at=exec_data.get('completed_at'),
        blocker=exec_data.get('blocker'),
        assigned_executor=exec_data.get('assigned_executor'),
        model_used=exec_data.get('model_used'),
        commits=exec_data.get('commits', []),
        validation_status=exec_data.get('validation_status', {}),
    )

    item = RoadmapItem(
        id=item_id,
        title=fm.get('title') or markdown_meta.get('title', item_id),
        category=fm.get('category', 'CORE'),
        item_type=fm.get('type', 'Feature'),
        description=fm.get('description') or markdown_meta.get('description', ''),

        # Status fields
        status=fm.get('status', 'Accepted'),
        priority=fm.get('priority', 'Medium'),
        priority_class=fm.get('priority_class', 'P2'),
        queue_rank=int(fm.get('queue_rank', 999)),
        target_horizon=fm.get('target_horizon', 'later'),
        loe=fm.get('loe', 'M'),

        # Scoring
        strategic_value=int(fm.get('strategic_value', 3)),
        architecture_fit=int(fm.get('architecture_fit', 3)),
        execution_risk=int(fm.get('execution_risk', 3)),
        dependency_burden=int(fm.get('dependency_burden', 3)),
        readiness=fm.get('readiness', 'blocked'),

        # Impact
        affected_systems=fm.get('affected_systems', []),
        affected_subsystems=fm.get('affected_subsystems', []),
        expected_file_families=fm.get('expected_file_families', []),
        cmdb_links=fm.get('cmdb_links', []),
        dependencies=fm.get('dependencies', []),
        grouping_candidates=fm.get('grouping_candidates', []),

        # Execution tracking
        execution=execution,

        # Content
        file_path=str(file_path),
        markdown_content=markdown,
        frontmatter=fm,
    )

    return item


def parse_roadmap_directory(roadmap_dir: Path) -> List[RoadmapItem]:
    """Parse all roadmap files from a directory."""
    items = []

    for md_file in sorted(roadmap_dir.glob('RM-*.md')):
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


if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent
    roadmap_dir = repo_root / "docs" / "roadmap"

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
