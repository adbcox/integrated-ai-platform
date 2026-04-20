"""Parse docs/roadmap/ROADMAP_INDEX.md and enrich from per-item YAML files.

Primary source: ROADMAP_INDEX.md (markdown bullet list).
Enrichment source: docs/roadmap/items/<ID>.yaml when present.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

# RM-<DOMAIN>-<NNN> where DOMAIN is one or more hyphen-separated uppercase
# alpha-numeric words and NNN is at least 3 digits.
_NAMING_RE = re.compile(
    r"^RM-([A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*)-(\d{3,})$"
)

# Matches markdown item bullet:  - `RM-GOV-001` — Some title
_MD_ITEM_RE = re.compile(
    r"^\s*-\s+`([^`]+)`\s+[—–\-]{1,3}\s*(.+)$"
)

_NAMING_VERSION = "v1"
_DEFAULT_STATUS = "proposed"
_DEFAULT_PRIORITY = "P2"
_DEFAULT_TYPE = "unknown"


@dataclass
class ParsedItem:
    id: str
    title: str
    source_path: str
    source_hash: str
    category: str
    item_type: str
    priority: str
    status: str
    description: Optional[str]
    from_yaml: bool = False
    raw_line: Optional[str] = None


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _domain_from_id(item_id: str) -> str:
    """Extract domain segment from a well-formed ID, e.g. 'GOV' from 'RM-GOV-001'."""
    m = _NAMING_RE.match(item_id)
    if m:
        return m.group(1)
    # Fall back to the segment after 'RM-' before the last '-NNN'
    parts = item_id.split("-")
    if len(parts) >= 3:
        return "-".join(parts[1:-1])
    return "UNKNOWN"


def _load_item_yaml(yaml_path: Path) -> dict:
    if not yaml_path.exists():
        return {}
    try:
        return yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _item_yaml_path(repo_root: Path, item_id: str) -> Path:
    return repo_root / "docs" / "roadmap" / "items" / f"{item_id}.yaml"


def _parsed_item_from_yaml(yaml_path: Path, repo_root: Path) -> Optional[ParsedItem]:
    """Build a ParsedItem from a standalone item YAML file."""
    raw = yaml_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    item_id = data.get("id", "")
    if not item_id:
        return None
    description_raw = data.get("description", None)
    description = description_raw.strip() if isinstance(description_raw, str) else None
    return ParsedItem(
        id=item_id,
        title=data.get("title", item_id),
        source_path=str(yaml_path.relative_to(repo_root)),
        source_hash=_sha256(raw),
        category=data.get("category", _domain_from_id(item_id)),
        item_type=data.get("type", _DEFAULT_TYPE),
        priority=data.get("priority", _DEFAULT_PRIORITY),
        status=data.get("status", _DEFAULT_STATUS),
        description=description,
        from_yaml=True,
    )


def parse_index_md(
    index_path: Path,
    repo_root: Path,
) -> list[ParsedItem]:
    """Parse ROADMAP_INDEX.md and return one ParsedItem per discovered item.

    Items that have a corresponding docs/roadmap/items/<ID>.yaml are enriched
    from that YAML.  Items found only in the markdown use defaults derived from
    their ID.
    """
    if not index_path.exists():
        return []

    md_text = index_path.read_text(encoding="utf-8")
    results: list[ParsedItem] = []
    md_source = str(index_path.relative_to(repo_root))

    for raw_line in md_text.splitlines():
        m = _MD_ITEM_RE.match(raw_line)
        if not m:
            continue
        item_id = m.group(1).strip()
        md_title = m.group(2).strip()

        yaml_path = _item_yaml_path(repo_root, item_id)
        yaml_data = _load_item_yaml(yaml_path)

        if yaml_data:
            raw_yaml = yaml_path.read_text(encoding="utf-8")
            description_raw = yaml_data.get("description", None)
            description = (
                description_raw.strip() if isinstance(description_raw, str) else None
            )
            item = ParsedItem(
                id=item_id,
                title=yaml_data.get("title", md_title),
                source_path=str(yaml_path.relative_to(repo_root)),
                source_hash=_sha256(raw_yaml),
                category=yaml_data.get("category", _domain_from_id(item_id)),
                item_type=yaml_data.get("type", _DEFAULT_TYPE),
                priority=yaml_data.get("priority", _DEFAULT_PRIORITY),
                status=yaml_data.get("status", _DEFAULT_STATUS),
                description=description,
                from_yaml=True,
                raw_line=raw_line,
            )
        else:
            item = ParsedItem(
                id=item_id,
                title=md_title,
                source_path=md_source,
                source_hash=_sha256(raw_line),
                category=_domain_from_id(item_id),
                item_type=_DEFAULT_TYPE,
                priority=_DEFAULT_PRIORITY,
                status=_DEFAULT_STATUS,
                description=None,
                from_yaml=False,
                raw_line=raw_line,
            )
        results.append(item)

    return results


def scan_item_yamls(repo_root: Path) -> list[ParsedItem]:
    """Scan docs/roadmap/items/*.yaml and return ParsedItems for every file."""
    items_dir = repo_root / "docs" / "roadmap" / "items"
    if not items_dir.is_dir():
        return []
    results: list[ParsedItem] = []
    for yaml_path in sorted(items_dir.glob("*.yaml")):
        item = _parsed_item_from_yaml(yaml_path, repo_root)
        if item is not None:
            results.append(item)
    return results


def validate_naming(item_id: str) -> bool:
    """Return True if item_id conforms to RM-<DOMAIN>-<NNN> convention."""
    return bool(_NAMING_RE.match(item_id))


NAMING_VERSION = _NAMING_VERSION
