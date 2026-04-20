"""RGC metrics capture and query service.

capture_metrics is the public entry point.  It reads live counts from the DB,
writes MetricSnapshot rows for the global scope and each category scope, and
returns a summary.

get_scope_metrics returns the most-recent snapshot for a (scope_type, scope_ref)
pair, or None if none exists.

Metric keys produced:
  item_count            — total roadmap items in scope
  items_by_status       — dict {status: count}
  items_by_category     — dict {category: count}  (global scope only)
  link_coverage_pct     — % of items in scope that have at least one roadmap_link
  open_finding_count    — open IntegrityFinding rows with object_type=roadmap_item
                          whose object_ref is in the scope item set
  package_count         — number of feature_block_package rows (global only)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from roadmap_governance.models import (
    FeatureBlockPackage,
    IntegrityFinding,
    MetricSnapshot,
    RoadmapItem,
    RoadmapLink,
)


@dataclass
class MetricsCaptureResult:
    snapshots_written: int = 0
    scopes_captured: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.scopes_captured is None:
            self.scopes_captured = []


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _link_coverage(db: Session, item_ids: set[str]) -> float:
    if not item_ids:
        return 0.0
    linked = {
        r.roadmap_id
        for r in db.query(RoadmapLink.roadmap_id)
        .filter(RoadmapLink.roadmap_id.in_(list(item_ids)))
        .all()
    }
    return round(len(linked) / len(item_ids) * 100, 2)


def _open_finding_count(db: Session, item_ids: set[str]) -> int:
    if not item_ids:
        return 0
    return (
        db.query(IntegrityFinding)
        .filter(
            IntegrityFinding.object_type == "roadmap_item",
            IntegrityFinding.object_ref.in_(list(item_ids)),
            IntegrityFinding.status == "open",
        )
        .count()
    )


def _write_snapshot(db: Session, scope_type: str, scope_ref: str, metrics: dict, *, dry_run: bool) -> None:
    if dry_run:
        return
    snap = MetricSnapshot(
        snapshot_id=str(uuid.uuid4()),
        scope_type=scope_type,
        scope_ref=scope_ref,
        metrics=metrics,
        captured_at=_now(),
    )
    db.add(snap)


def capture_metrics(
    db: Session,
    *,
    dry_run: bool = False,
) -> MetricsCaptureResult:
    """Capture a full metrics snapshot for global scope and each category."""
    result = MetricsCaptureResult()

    all_items: list[RoadmapItem] = db.query(RoadmapItem).all()
    all_ids = {item.id for item in all_items}

    status_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for item in all_items:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1
        category_counts[item.category] = category_counts.get(item.category, 0) + 1

    pkg_count = db.query(FeatureBlockPackage).count()

    global_metrics = {
        "item_count": len(all_items),
        "items_by_status": status_counts,
        "items_by_category": category_counts,
        "link_coverage_pct": _link_coverage(db, all_ids),
        "open_finding_count": _open_finding_count(db, all_ids),
        "package_count": pkg_count,
    }
    _write_snapshot(db, "global", "global", global_metrics, dry_run=dry_run)
    result.snapshots_written += 1
    result.scopes_captured.append("global:global")

    categories = list(category_counts.keys())
    for cat in sorted(categories):
        cat_items = {item.id for item in all_items if item.category == cat}
        cat_status: dict[str, int] = {}
        for item in all_items:
            if item.category == cat:
                cat_status[item.status] = cat_status.get(item.status, 0) + 1
        cat_metrics = {
            "item_count": len(cat_items),
            "items_by_status": cat_status,
            "link_coverage_pct": _link_coverage(db, cat_items),
            "open_finding_count": _open_finding_count(db, cat_items),
        }
        _write_snapshot(db, "category", cat, cat_metrics, dry_run=dry_run)
        result.snapshots_written += 1
        result.scopes_captured.append(f"category:{cat}")

    if not dry_run:
        db.commit()

    return result


def get_scope_metrics(
    db: Session,
    scope_type: str,
    scope_ref: str,
) -> Optional[MetricSnapshot]:
    """Return the most-recent MetricSnapshot for the given scope, or None."""
    return (
        db.query(MetricSnapshot)
        .filter(
            MetricSnapshot.scope_type == scope_type,
            MetricSnapshot.scope_ref == scope_ref,
        )
        .order_by(MetricSnapshot.captured_at.desc())
        .first()
    )
