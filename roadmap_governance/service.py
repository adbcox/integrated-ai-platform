"""RGC sync service: parse → validate → upsert → persist findings."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from roadmap_governance.models import IntegrityFinding, RoadmapItem
from roadmap_governance.parser import (
    NAMING_VERSION,
    ParsedItem,
    parse_index_md,
    scan_item_yamls,
    validate_naming,
)


@dataclass
class SyncResult:
    items_created: int = 0
    items_updated: int = 0
    items_unchanged: int = 0
    findings_created: int = 0


_INDEX_PATH_RELATIVE = Path("docs") / "roadmap" / "ROADMAP_INDEX.md"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _finding_exists(db: Session, finding_type: str, object_ref: str) -> bool:
    """Return True if an open finding of this type already exists for this ref."""
    return (
        db.query(IntegrityFinding)
        .filter_by(finding_type=finding_type, object_ref=object_ref, status="open")
        .first()
        is not None
    )


def _record_finding(
    db: Session,
    *,
    finding_type: str,
    severity: str,
    object_type: str,
    object_ref: str,
    summary: str,
    details: Optional[dict] = None,
    dry_run: bool = False,
) -> bool:
    """Persist an integrity finding if one is not already open. Returns True if created."""
    if _finding_exists(db, finding_type, object_ref):
        return False
    if dry_run:
        return True
    finding = IntegrityFinding(
        finding_id=str(uuid.uuid4()),
        finding_type=finding_type,
        severity=severity,
        object_type=object_type,
        object_ref=object_ref,
        summary=summary,
        details=details or {},
        detected_at=_now(),
        status="open",
        resolution_note=None,
    )
    db.add(finding)
    return True


def _upsert_item(
    db: Session,
    parsed: ParsedItem,
    *,
    dry_run: bool = False,
) -> str:
    """Upsert a roadmap item. Returns 'created', 'updated', or 'unchanged'."""
    existing: Optional[RoadmapItem] = db.get(RoadmapItem, parsed.id)
    now = _now()

    if existing is None:
        if not dry_run:
            item = RoadmapItem(
                id=parsed.id,
                title=parsed.title,
                category=parsed.category,
                item_type=parsed.item_type,
                priority=parsed.priority,
                status=parsed.status,
                description=parsed.description,
                source_path=parsed.source_path,
                source_hash=parsed.source_hash,
                naming_version=NAMING_VERSION,
                created_at=now,
                updated_at=now,
            )
            db.add(item)
        return "created"

    changed = (
        existing.title != parsed.title
        or existing.category != parsed.category
        or existing.item_type != parsed.item_type
        or existing.priority != parsed.priority
        or existing.status != parsed.status
        or existing.description != parsed.description
        or existing.source_path != parsed.source_path
        or existing.source_hash != parsed.source_hash
    )
    if changed:
        if not dry_run:
            existing.title = parsed.title
            existing.category = parsed.category
            existing.item_type = parsed.item_type
            existing.priority = parsed.priority
            existing.status = parsed.status
            existing.description = parsed.description
            existing.source_path = parsed.source_path
            existing.source_hash = parsed.source_hash
            existing.updated_at = now
        return "updated"
    return "unchanged"


def sync_roadmap(
    db: Session,
    repo_root: Path,
    *,
    dry_run: bool = False,
) -> SyncResult:
    """Full sync: read ROADMAP_INDEX.md + YAML files, upsert items, persist findings.

    Safe to rerun: duplicate findings are not re-created, upserts are idempotent.
    """
    result = SyncResult()
    index_path = repo_root / _INDEX_PATH_RELATIVE

    # --- 1. Parse primary source (ROADMAP_INDEX.md) ---
    md_items = parse_index_md(index_path, repo_root)

    # --- 2. Scan YAML items to catch items not listed in the index ---
    yaml_items = scan_item_yamls(repo_root)
    yaml_ids_by_id = {item.id: item for item in yaml_items}
    md_ids = {item.id for item in md_items}

    # Build the authoritative item map: prefer YAML-enriched items from md_items,
    # then add any YAML-only items as secondary.
    all_items: list[ParsedItem] = list(md_items)
    for yaml_item in yaml_items:
        if yaml_item.id not in md_ids:
            all_items.append(yaml_item)

    # --- 3. Detect duplicates across the combined set ---
    seen_ids: dict[str, int] = {}
    for parsed in all_items:
        seen_ids[parsed.id] = seen_ids.get(parsed.id, 0) + 1

    # --- 4. Validate, upsert, and persist findings ---
    processed_ids: set[str] = set()

    for parsed in all_items:
        # Skip second+ occurrence of a duplicate ID (record finding once)
        if parsed.id in processed_ids:
            created = _record_finding(
                db,
                finding_type="duplicate_id",
                severity="warning",
                object_type="roadmap_item",
                object_ref=parsed.id,
                summary=f"Roadmap item ID '{parsed.id}' appears more than once in source.",
                details={"count": seen_ids[parsed.id]},
                dry_run=dry_run,
            )
            if created:
                result.findings_created += 1
            continue
        processed_ids.add(parsed.id)

        # Duplicate finding for first occurrence when count > 1
        if seen_ids[parsed.id] > 1:
            created = _record_finding(
                db,
                finding_type="duplicate_id",
                severity="warning",
                object_type="roadmap_item",
                object_ref=parsed.id,
                summary=f"Roadmap item ID '{parsed.id}' appears more than once in source.",
                details={"count": seen_ids[parsed.id]},
                dry_run=dry_run,
            )
            if created:
                result.findings_created += 1

        # Naming validation
        if not validate_naming(parsed.id):
            created = _record_finding(
                db,
                finding_type="naming_violation",
                severity="error",
                object_type="roadmap_item",
                object_ref=parsed.id,
                summary=(
                    f"Roadmap item ID '{parsed.id}' does not conform to"
                    " RM-<DOMAIN>-<NNN> naming convention."
                ),
                details={"id": parsed.id, "naming_version": NAMING_VERSION},
                dry_run=dry_run,
            )
            if created:
                result.findings_created += 1

        # Upsert
        outcome = _upsert_item(db, parsed, dry_run=dry_run)
        if outcome == "created":
            result.items_created += 1
        elif outcome == "updated":
            result.items_updated += 1
        else:
            result.items_unchanged += 1

    if not dry_run:
        db.commit()

    return result
