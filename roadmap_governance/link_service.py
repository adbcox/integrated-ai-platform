"""RGC roadmap-to-CMDB linking service.

run_link_refresh is the public entry point.  It loads all persisted roadmap items
and CMDB entities, evaluates matches conservatively, persists safe links, and records
integrity findings for unresolved or ambiguous cases.

Matching strategy (conservative, two levels):

  Level 1 — exact canonical name (link_type="exact_canonical", confidence=1.0):
    The CMDB entity's full canonical_name appears verbatim as a token in the
    roadmap item's combined text (title + description).  Only this level produces
    persisted links.  Multiple exact matches on the same item each produce their own
    independent link.

  Level 2 — last-segment fallback (no link created, findings only):
    If no exact match is found, the last segment of any CMDB canonical_name (e.g.
    "api" from "prod.rgc.api") is searched in the item text.  If multiple entities
    share the same last segment that appears in the text, an ambiguous_cmdb_link
    finding is emitted.  Single-segment matches are still treated as unresolved
    because they are not safely attributable to one entity without more context.

Finding types emitted:
  unresolved_cmdb_link — item has no exact canonical-name match in its text.
  ambiguous_cmdb_link  — item text contains a segment token shared by ≥2 entities.

Safe to rerun: both upserts and findings are idempotent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from roadmap_governance.models import CmdbEntity, RoadmapItem, RoadmapLink
from roadmap_governance.schemas import RoadmapImpactResponse, RoadmapLinkItem
from roadmap_governance.service import record_finding

_AUTO_LINK_THRESHOLD: float = 0.9  # only exact (1.0) matches exceed this


@dataclass
class LinkRefreshResult:
    items_processed: int = 0
    links_created: int = 0
    links_updated: int = 0
    links_unchanged: int = 0
    findings_created: int = 0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _item_text(item: RoadmapItem) -> str:
    return ((item.title or "") + " " + (item.description or "")).lower()


def _extract_canonical_tokens(text: str) -> set[str]:
    """Return all substrings that look like canonical names (2+ dot-separated segments)."""
    return set(re.findall(r"[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)+", text))


def _extract_word_tokens(text: str, exclude: set[str]) -> set[str]:
    """Return individual word-level tokens, excluding those already identified as canonical names."""
    raw = set(re.findall(r"[a-z0-9][a-z0-9-]*", text))
    return raw - exclude


def _match_item(
    item: RoadmapItem,
    entities: list[CmdbEntity],
) -> tuple[list[CmdbEntity], list[list[CmdbEntity]]]:
    """Evaluate one roadmap item against all CMDB entities.

    Returns:
      exact_matches  — entities whose canonical_name appears verbatim in item text.
      ambiguous_groups — groups of 2+ entities sharing a last-segment token in item
                         text (only populated when exact_matches is empty).
    """
    text = _item_text(item)
    canonical_tokens = _extract_canonical_tokens(text)
    entity_by_name = {e.canonical_name: e for e in entities}

    exact = [entity_by_name[tok] for tok in canonical_tokens if tok in entity_by_name]

    if exact:
        return exact, []

    # Segment fallback — last segment of each canonical name vs word tokens in text
    word_tokens = _extract_word_tokens(text, canonical_tokens)
    segment_groups: dict[str, list[CmdbEntity]] = {}
    for e in entities:
        last_seg = e.canonical_name.rsplit(".", 1)[-1]
        if last_seg in word_tokens:
            segment_groups.setdefault(last_seg, []).append(e)

    ambiguous = [grp for grp in segment_groups.values() if len(grp) > 1]
    return [], ambiguous


def _upsert_link(
    db: Session,
    roadmap_id: str,
    entity_id: str,
    link_type: str,
    confidence: float,
    evidence_ref: Optional[str],
    *,
    dry_run: bool,
) -> str:
    """Upsert by composite PK. Returns 'created', 'updated', or 'unchanged'."""
    existing: Optional[RoadmapLink] = (
        db.query(RoadmapLink)
        .filter(
            RoadmapLink.roadmap_id == roadmap_id,
            RoadmapLink.entity_id == entity_id,
            RoadmapLink.link_type == link_type,
        )
        .first()
    )
    now = _now()

    if existing is None:
        if not dry_run:
            db.add(
                RoadmapLink(
                    roadmap_id=roadmap_id,
                    entity_id=entity_id,
                    link_type=link_type,
                    confidence=confidence,
                    evidence_ref=evidence_ref,
                    created_at=now,
                    updated_at=now,
                )
            )
        return "created"

    changed = existing.confidence != confidence or existing.evidence_ref != evidence_ref
    if changed:
        if not dry_run:
            existing.confidence = confidence
            existing.evidence_ref = evidence_ref
            existing.updated_at = now
        return "updated"
    return "unchanged"


def run_link_refresh(
    db: Session,
    *,
    dry_run: bool = False,
) -> LinkRefreshResult:
    """Evaluate all roadmap items against all CMDB entities and persist safe links.

    Idempotent: safe to rerun; existing active findings are not re-created.
    """
    result = LinkRefreshResult()

    def _emit(finding_type: str, severity: str, object_ref: str, summary: str, details: dict) -> None:
        ok = record_finding(
            db,
            finding_type=finding_type,
            severity=severity,
            object_type="roadmap_item",
            object_ref=object_ref,
            summary=summary,
            details=details,
            dry_run=dry_run,
        )
        if ok:
            result.findings_created += 1

    items: list[RoadmapItem] = db.query(RoadmapItem).order_by(RoadmapItem.id).all()
    entities: list[CmdbEntity] = db.query(CmdbEntity).all()
    result.items_processed = len(items)

    for item in items:
        exact_matches, ambiguous_groups = _match_item(item, entities)

        for entity in exact_matches:
            evidence = f"canonical_name:{entity.canonical_name}"
            outcome = _upsert_link(
                db,
                item.id,
                entity.entity_id,
                "exact_canonical",
                1.0,
                evidence,
                dry_run=dry_run,
            )
            if outcome == "created":
                result.links_created += 1
            elif outcome == "updated":
                result.links_updated += 1
            else:
                result.links_unchanged += 1

        if ambiguous_groups:
            for group in ambiguous_groups:
                candidates = sorted(e.canonical_name for e in group)
                _emit(
                    "ambiguous_cmdb_link",
                    "warning",
                    item.id,
                    f"Roadmap item '{item.id}' matches multiple CMDB entities by segment token: {candidates}.",
                    {"roadmap_id": item.id, "candidates": candidates},
                )

        if not exact_matches and not ambiguous_groups:
            _emit(
                "unresolved_cmdb_link",
                "info",
                item.id,
                f"Roadmap item '{item.id}' has no resolvable CMDB entity link.",
                {"roadmap_id": item.id, "title": item.title},
            )

    if not dry_run:
        db.commit()

    return result


def get_impact_view(db: Session, roadmap_id: str) -> Optional[RoadmapImpactResponse]:
    """Return the impact view for a roadmap item, or None if the item does not exist."""
    item = db.get(RoadmapItem, roadmap_id)
    if item is None:
        return None

    links: list[RoadmapLink] = (
        db.query(RoadmapLink)
        .filter(RoadmapLink.roadmap_id == roadmap_id)
        .all()
    )

    link_items: list[RoadmapLinkItem] = []
    for link in links:
        entity: Optional[CmdbEntity] = db.get(CmdbEntity, link.entity_id)
        if entity is None:
            continue
        link_items.append(
            RoadmapLinkItem(
                entity_id=link.entity_id,
                link_type=link.link_type,
                confidence=link.confidence,
                evidence_ref=link.evidence_ref,
                canonical_name=entity.canonical_name,
                display_name=entity.display_name,
                entity_type=entity.entity_type,
                created_at=link.created_at,
                updated_at=link.updated_at,
            )
        )

    return RoadmapImpactResponse(roadmap_id=item.id, title=item.title, links=link_items)
