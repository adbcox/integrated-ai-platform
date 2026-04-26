#!/usr/bin/env python3
"""Scan ALL RM-*.md files in repo and extract metadata for deduplication analysis."""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

_REPO = Path(__file__).parent.parent

# Fields we'll parse from each doc
_STATUS_MAP = {
    "accepted": "Accepted", "backlog": "Backlog", "todo": "Todo",
    "in progress": "In Progress", "in-progress": "In Progress",
    "done": "Done", "complete": "Done", "completed": "Done",
    "deferred": "Deferred", "cancelled": "Cancelled", "canceled": "Cancelled",
    "pending": "Backlog", "ready": "Ready",
}

_PRIORITY_MAP = {
    "p0": "urgent", "p1": "high", "p2": "medium", "p3": "low", "p4": "none",
    "critical": "urgent", "high": "high", "medium": "medium", "low": "low",
}

_STATUS_WORDS = {
    "accepted", "backlog", "todo", "in progress", "in-progress",
    "done", "complete", "completed", "deferred", "cancelled", "canceled",
    "pending", "ready",
}


def _find(pattern: str, text: str, group: int = 1, flags: int = re.IGNORECASE) -> str:
    m = re.search(pattern, text, flags)
    return m.group(group).strip() if m else ""


def extract_metadata(filepath: Path) -> dict:
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"error": str(e), "filepath": str(filepath)}

    stem = filepath.stem  # e.g. "RM-A11Y-001" or "RM-DEV-001_EXECUTION_PACK"

    # Determine file type
    is_exec_pack = "_EXECUTION_PACK" in stem
    clean_stem = stem.replace("_EXECUTION_PACK", "")

    id_match = re.match(r"(RM-[A-Z0-9]+-\d+)", clean_stem)
    item_id = id_match.group(1) if id_match else clean_stem

    cat_match = re.match(r"RM-([A-Z0-9]+)-", item_id)
    category = cat_match.group(1) if cat_match else "GENERAL"

    # Title: from bold **Title:** field or first # heading
    title = (_find(r'\*\*Title:\*\*\s*(.+)', content)
             or _find(r'^#\s+(.+)$', content, flags=re.MULTILINE)
             or item_id)
    title = re.sub(r'^#+\s*', '', title).strip()

    # Status
    raw_status = (_find(r'\*\*Status:\*\*\s*`?([^`\n]+)`?', content)
                  or _find(r'^[-*]\s+\*\*Status:\*\*\s*(.+)$', content, flags=re.MULTILINE))
    status = _STATUS_MAP.get(raw_status.lower().strip(), raw_status or "Backlog")

    # Priority
    raw_pri = (_find(r'\*\*Priority:\*\*\s*`?([^`\n]+)`?', content)
               or _find(r'\*\*Priority class:\*\*\s*`?([^`\n]+)`?', content))
    priority = _PRIORITY_MAP.get(raw_pri.lower().strip(), "medium")

    # Description: text between first heading and first ##
    desc_m = re.search(r'^#{1,2}[^#].+?\n\n(.*?)(?=\n##|\Z)', content,
                       re.MULTILINE | re.DOTALL)
    description = desc_m.group(1).strip()[:600] if desc_m else ""

    # Feature flags
    has_ac = bool(re.search(r'acceptance criteria|key requirements', content, re.IGNORECASE))
    has_deps = bool(re.search(r'\[RM-|\bDepends on\b|depends_on', content, re.IGNORECASE))
    has_loe = bool(re.search(r'\bLOE\b|\blevel of effort\b', content, re.IGNORECASE))

    return {
        "id": item_id,
        "title": title,
        "category": category,
        "status": status,
        "priority": priority,
        "description": description,
        "filepath": str(filepath.relative_to(_REPO)),
        "filesize": filepath.stat().st_size,
        "is_exec_pack": is_exec_pack,
        "has_acceptance_criteria": has_ac,
        "has_dependencies": has_deps,
        "has_loe": has_loe,
    }


def main() -> int:
    all_files = sorted(_REPO.rglob("RM-*.md"))
    # Exclude hidden dirs
    all_files = [f for f in all_files if "/." not in str(f)]

    print(f"Found {len(all_files)} RM-*.md files total")

    items: list[dict] = []
    by_id: dict[str, list[dict]] = defaultdict(list)
    errors = 0

    for fp in all_files:
        meta = extract_metadata(fp)
        if "error" in meta:
            print(f"  ERROR {fp}: {meta['error']}", file=sys.stderr)
            errors += 1
            continue
        items.append(meta)
        by_id[meta["id"]].append(meta)

    # Classify
    exec_packs = [i for i in items if i["is_exec_pack"]]
    issue_items = [i for i in items if not i["is_exec_pack"]]
    duplicates = {id_: entries for id_, entries in by_id.items() if len(entries) > 1}

    # Category breakdown (issues only)
    by_cat: dict[str, int] = defaultdict(int)
    for it in issue_items:
        by_cat[it["category"]] += 1

    print(f"\n{'─'*50}")
    print(f"  Issue ITEMS:       {len(issue_items)}")
    print(f"  Execution packs:   {len(exec_packs)}")
    print(f"  Unique IDs:        {len(by_id)}")
    print(f"  Duplicate IDs:     {len(duplicates)}")
    print(f"  Parse errors:      {errors}")
    print(f"{'─'*50}")

    print(f"\nCategory breakdown ({len(by_cat)} categories):")
    for cat, cnt in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"  {cat:<12} {cnt:>4}")

    if duplicates:
        print(f"\nDuplicate IDs ({len(duplicates)}):")
        for id_, entries in sorted(duplicates.items()):
            print(f"  {id_}:")
            for e in entries:
                tag = "[EXEC]" if e["is_exec_pack"] else "[ITEM]"
                print(f"    {tag} {e['filepath']}")

    report = {
        "total_files": len(all_files),
        "issue_items": len(issue_items),
        "exec_packs": len(exec_packs),
        "unique_ids": len(by_id),
        "duplicate_ids": len(duplicates),
        "parse_errors": errors,
        "by_category": dict(sorted(by_cat.items())),
        "duplicates": {
            id_: [e["filepath"] for e in entries]
            for id_, entries in duplicates.items()
        },
        "items": items,
    }

    out = _REPO / "roadmap_scan_report.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"\n✓ Report saved → roadmap_scan_report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())


def scan_roadmap_docs_api() -> dict:
    """API-friendly scan — same logic as main() but returns a dict instead of printing."""
    all_files = sorted(_REPO.rglob("RM-*.md"))
    all_files = [f for f in all_files if "/." not in str(f)]

    items: list[dict] = []
    by_id: dict[str, list[dict]] = defaultdict(list)
    errors: list[str] = []

    for fp in all_files:
        meta = extract_metadata(fp)
        if "error" in meta:
            errors.append(f"{fp}: {meta['error']}")
            continue
        items.append(meta)
        by_id[meta["id"]].append(meta)

    issue_items = [i for i in items if not i["is_exec_pack"]]
    exec_packs  = [i for i in items if i["is_exec_pack"]]
    duplicates  = {id_: [e["filepath"] for e in entries]
                   for id_, entries in by_id.items() if len(entries) > 1}

    by_cat: dict[str, int] = defaultdict(int)
    for it in issue_items:
        by_cat[it["category"]] += 1

    return {
        "total_files":   len(all_files),
        "issue_items":   len(issue_items),
        "exec_packs":    len(exec_packs),
        "unique_ids":    len(by_id),
        "duplicate_ids": len(duplicates),
        "parse_errors":  errors,
        "by_category":   dict(sorted(by_cat.items())),
        "duplicates":    duplicates,
        "items":         items,
    }
