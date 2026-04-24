#!/usr/bin/env python3
"""Parse roadmap markdown files into structured RoadmapItem objects."""

import sys
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class RoadmapItem:
    """Represents a parsed roadmap execution pack."""
    id: str
    title: str
    objective: str
    why_matters: str
    required_outcome: List[str]
    required_artifacts: List[str]
    best_practices: List[str]
    failure_modes: List[str]
    first_milestone: str

    # Execution tracking
    status: str = "planned"  # planned, in_progress, blocked, completed
    dependencies: List[str] = field(default_factory=list)
    priority: int = 5  # 1=highest, 10=lowest
    affected_files: List[str] = field(default_factory=list)
    complexity: str = "medium"  # simple, medium, complex
    subtasks: List[str] = field(default_factory=list)

    # Metadata
    file_path: Optional[str] = None
    parsed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: Optional[str] = None


def extract_id_from_filename(filename: str) -> str:
    """Extract roadmap ID from filename (e.g., RM-CORE-004)."""
    match = re.search(r'(RM-[A-Z]+-\d+)', filename)
    if match:
        return match.group(1)
    return Path(filename).stem


def extract_bullet_list(content: str) -> List[str]:
    """Extract bullet points from markdown section."""
    lines = content.split('\n')
    items = []
    for line in lines:
        line = line.strip()
        if line.startswith('- '):
            items.append(line[2:].strip())
    return items


def parse_roadmap_file(file_path: Path) -> Optional[RoadmapItem]:
    """Parse a roadmap markdown file into a RoadmapItem."""
    try:
        content = file_path.read_text()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}", file=sys.stderr)
        return None

    # Extract ID from filename
    item_id = extract_id_from_filename(file_path.name)

    # Extract sections using regex
    sections = {}
    current_section = None
    current_content = []

    for line in content.split('\n'):
        # Match section headers (## Title, ## Objective, etc.)
        header_match = re.match(r'^##\s+(.+)$', line)
        if header_match:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = header_match.group(1).lower()
            current_content = []
        elif current_section:
            current_content.append(line)

    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()

    # Extract title (first non-# line or from filename)
    title_match = re.search(r'\*\*(.+?)\*\*', sections.get('title', ''))
    title = title_match.group(1) if title_match else item_id

    # Build item
    item = RoadmapItem(
        id=item_id,
        title=title,
        objective=sections.get('objective', '').strip(),
        why_matters=sections.get('why this matters', '').strip(),
        required_outcome=extract_bullet_list(sections.get('required outcome', '')),
        required_artifacts=extract_bullet_list(sections.get('required artifacts', '')),
        best_practices=extract_bullet_list(sections.get('best practices', '')),
        failure_modes=extract_bullet_list(sections.get('common failure modes', '')),
        first_milestone=sections.get('recommended first milestone', '').strip(),
        file_path=str(file_path),
    )

    return item


def parse_roadmap_directory(roadmap_dir: Path) -> List[RoadmapItem]:
    """Parse all roadmap files from a directory."""
    items = []

    # Find all markdown files matching pattern
    for md_file in sorted(roadmap_dir.glob('RM-*.md')):
        item = parse_roadmap_file(md_file)
        if item:
            items.append(item)

    return items


def infer_dependencies(items: List[RoadmapItem]) -> None:
    """Infer dependencies based on ID patterns and content analysis."""
    id_map = {item.id: item for item in items}

    for item in items:
        deps = set()

        # Extract referenced IDs from content
        for field_name in ['objective', 'why_matters', 'first_milestone']:
            content = getattr(item, field_name, '')
            for match in re.finditer(r'(RM-[A-Z]+-\d+)', content):
                ref_id = match.group(1)
                if ref_id in id_map and ref_id != item.id:
                    deps.add(ref_id)

        item.dependencies = sorted(list(deps))


def print_item_summary(item: RoadmapItem) -> None:
    """Print a formatted summary of a roadmap item."""
    print(f"\n📋 {item.id} — {item.title}")
    print(f"   Status: {item.status}")
    print(f"   Objective: {item.objective[:80]}...")
    if item.dependencies:
        print(f"   Dependencies: {', '.join(item.dependencies)}")
    if item.required_outcome:
        print(f"   Outcomes: {len(item.required_outcome)} items")


if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent
    roadmap_dir = repo_root / "docs" / "roadmap"

    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Parse all items
        items = parse_roadmap_directory(roadmap_dir)
        infer_dependencies(items)

        print(f"✅ Parsed {len(items)} roadmap items\n")
        for item in items:
            print_item_summary(item)
    else:
        # Parse a specific file
        if len(sys.argv) < 2:
            print("Usage: roadmap_parser.py [--all|filename.md]")
            sys.exit(1)

        target = Path(sys.argv[1])
        if not target.is_absolute():
            target = roadmap_dir / target

        item = parse_roadmap_file(target)
        if item:
            print_item_summary(item)
            print(f"\n   Objective: {item.objective}")
            if item.required_outcome:
                print(f"\n   Required Outcomes:")
                for outcome in item.required_outcome:
                    print(f"     - {outcome}")
