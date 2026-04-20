"""RGC feature-block package planner service.

run_planner_refresh is the public entry point.  It groups all active roadmap
items by category, scores each group, upserts one FeatureBlockPackage per
category, rebuilds its FeatureBlockMember set, writes an artifact JSON file,
and returns a summary.

Scoring model (see docs/governance/scoring-model.md for full description):

  1. Priority weight per item: P0=4, P1=3, P2=2, P3=1, other=1
  2. Raw score  = sum(priority_weights) for items in the package
  3. Max score  = len(items) * 4
  4. Normalised = raw / max  (0.0–1.0; 0.0 when no items)
  5. Link bonus = +0.10 if any item in the package has a CMDB link
  6. Finding penalty = -0.05 × open_finding_count for items in the package
  7. Final score = clamp(normalised + link_bonus - finding_penalty, 0.0, 1.0)

Package IDs: PKG-{CATEGORY} (uppercase, stable across reruns).

Safe to rerun: upserts are idempotent; member set is fully rebuilt each run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from roadmap_governance.models import (
    FeatureBlockMember,
    FeatureBlockPackage,
    IntegrityFinding,
    RoadmapItem,
    RoadmapLink,
)

_PRIORITY_WEIGHTS: dict[str, int] = {"P0": 4, "P1": 3, "P2": 2, "P3": 1}
_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "governance" / "packages"


@dataclass
class PlannerRefreshResult:
    packages_created: int = 0
    packages_updated: int = 0
    packages_unchanged: int = 0
    members_added: int = 0
    artifact_paths: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.artifact_paths is None:
            self.artifact_paths = []


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _pkg_id(category: str) -> str:
    return "PKG-" + category.upper().replace(" ", "-")


def _score(
    items: list[RoadmapItem],
    linked_ids: set[str],
    open_finding_count: int,
) -> float:
    if not items:
        return 0.0
    raw = sum(_PRIORITY_WEIGHTS.get(item.priority, 1) for item in items)
    max_score = len(items) * 4
    normalised = raw / max_score
    link_bonus = 0.10 if any(item.id in linked_ids for item in items) else 0.0
    finding_penalty = 0.05 * open_finding_count
    return max(0.0, min(1.0, normalised + link_bonus - finding_penalty))


def _rationale(items: list[RoadmapItem], score: float, linked_ids: set[str], open_finding_count: int) -> str:
    linked = sum(1 for item in items if item.id in linked_ids)
    return (
        f"{len(items)} item(s); "
        f"{linked} with CMDB links; "
        f"{open_finding_count} open finding(s); "
        f"score={score:.3f}"
    )


def run_planner_refresh(
    db: Session,
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> PlannerRefreshResult:
    """Group roadmap items by category, score, and upsert feature-block packages."""
    result = PlannerRefreshResult()
    art_dir = artifact_dir or _DEFAULT_ARTIFACT_DIR

    all_items: list[RoadmapItem] = db.query(RoadmapItem).order_by(RoadmapItem.id).all()

    all_ids = {item.id for item in all_items}
    linked_ids: set[str] = {
        r.roadmap_id
        for r in db.query(RoadmapLink.roadmap_id)
        .filter(RoadmapLink.roadmap_id.in_(list(all_ids)))
        .all()
    } if all_ids else set()

    # Group by category
    by_category: dict[str, list[RoadmapItem]] = {}
    for item in all_items:
        by_category.setdefault(item.category, []).append(item)

    now = _now()

    for category, items in sorted(by_category.items()):
        item_ids = {item.id for item in items}
        open_finding_count = (
            db.query(IntegrityFinding)
            .filter(
                IntegrityFinding.object_type == "roadmap_item",
                IntegrityFinding.object_ref.in_(list(item_ids)),
                IntegrityFinding.status == "open",
            )
            .count()
        )

        pkg_id = _pkg_id(category)
        score = _score(items, linked_ids, open_finding_count)
        title = f"{category.title()} Feature Block"
        rationale = _rationale(items, score, linked_ids, open_finding_count)

        artifact_path: Optional[str] = None
        if not dry_run:
            art_dir.mkdir(parents=True, exist_ok=True)
            artifact_file = art_dir / f"{pkg_id}.json"
            payload = {
                "package_id": pkg_id,
                "title": title,
                "scope": category,
                "score": round(score, 6),
                "rationale": rationale,
                "members": [
                    {"roadmap_id": item.id, "title": item.title, "priority": item.priority, "status": item.status}
                    for item in items
                ],
                "refreshed_at": now.isoformat(),
            }
            artifact_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            artifact_path = str(artifact_file)
            result.artifact_paths.append(artifact_path)

        if not dry_run:
            existing: Optional[FeatureBlockPackage] = db.get(FeatureBlockPackage, pkg_id)
            if existing is None:
                pkg = FeatureBlockPackage(
                    package_id=pkg_id,
                    title=title,
                    scope=category,
                    status="draft",
                    score=score,
                    rationale=rationale,
                    artifact_path=artifact_path,
                    created_at=now,
                    updated_at=now,
                )
                db.add(pkg)
                result.packages_created += 1
            else:
                changed = (
                    existing.score != score
                    or existing.rationale != rationale
                    or existing.title != title
                    or existing.artifact_path != artifact_path
                )
                if changed:
                    existing.score = score
                    existing.rationale = rationale
                    existing.title = title
                    existing.artifact_path = artifact_path
                    existing.updated_at = now
                    result.packages_updated += 1
                else:
                    result.packages_unchanged += 1

            # Rebuild member set: delete existing, insert current
            db.query(FeatureBlockMember).filter(FeatureBlockMember.package_id == pkg_id).delete()
            for item in items:
                db.add(FeatureBlockMember(
                    package_id=pkg_id,
                    roadmap_id=item.id,
                    member_role="primary",
                    added_at=now,
                ))
                result.members_added += 1
        else:
            # dry_run: just count
            existing = db.get(FeatureBlockPackage, pkg_id)
            if existing is None:
                result.packages_created += 1
            else:
                result.packages_updated += 1
            result.members_added += len(items)

    if not dry_run:
        db.commit()

    return result
