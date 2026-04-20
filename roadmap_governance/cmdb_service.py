"""RGC CMDB import service: validate, upsert, and persist findings for CMDB entities.

import_cmdb_entities is the public entry point.  It accepts a list of raw entity
dicts (already parsed from a seed file), normalizes fields, validates each entity,
upserts idempotently by canonical_name, and persists integrity findings.

Safe to rerun: upserts are idempotent by canonical_name; active findings are not
re-created (idempotence via finding_exists in service.py).
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from sqlalchemy.orm import Session

from roadmap_governance.models import CmdbEntity
from roadmap_governance.service import record_finding

VALID_ENTITY_TYPES: frozenset[str] = frozenset(
    {"machine", "service", "repo", "script", "dashboard", "dataset", "device"}
)

# canonical_name: two or more dot-separated segments, each [a-z0-9][a-z0-9-]*
# Supports <environment>.<domain>.<service_or_host> and two-segment variants.
_CANONICAL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)+$")


def validate_canonical_name(name: str) -> bool:
    return bool(_CANONICAL_NAME_RE.match(name))


@dataclass
class ParsedEntity:
    entity_type: str
    canonical_name: str
    display_name: str
    platform: Optional[str]
    environment: Optional[str]
    criticality: Optional[str]
    owner: Optional[str]
    lifecycle_state: Optional[str]
    source_system: Optional[str]
    external_ref: Optional[str]
    entity_metadata: dict


@dataclass
class CmdbImportResult:
    entities_created: int = 0
    entities_updated: int = 0
    entities_unchanged: int = 0
    findings_created: int = 0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _opt(raw: dict, key: str) -> Optional[str]:
    v = raw.get(key)
    return str(v).strip() if v is not None else None


def _normalize(raw: dict) -> ParsedEntity:
    canonical_name = str(raw.get("canonical_name", "") or "").strip().lower()
    display_name = str(raw.get("display_name", canonical_name) or canonical_name).strip()
    entity_type = str(raw.get("entity_type", "") or "").strip().lower()
    meta = raw.get("metadata", {})
    if not isinstance(meta, dict):
        meta = {}
    return ParsedEntity(
        entity_type=entity_type,
        canonical_name=canonical_name,
        display_name=display_name,
        platform=_opt(raw, "platform"),
        environment=_opt(raw, "environment"),
        criticality=_opt(raw, "criticality"),
        owner=_opt(raw, "owner"),
        lifecycle_state=_opt(raw, "lifecycle_state"),
        source_system=_opt(raw, "source_system") or "seed_file",
        external_ref=_opt(raw, "external_ref"),
        entity_metadata=meta,
    )


def _upsert_entity(db: Session, parsed: ParsedEntity, *, dry_run: bool) -> str:
    """Upsert by canonical_name. Returns 'created', 'updated', or 'unchanged'."""
    existing: Optional[CmdbEntity] = (
        db.query(CmdbEntity)
        .filter(CmdbEntity.canonical_name == parsed.canonical_name)
        .first()
    )
    now = _now()

    if existing is None:
        if not dry_run:
            db.add(CmdbEntity(
                entity_id=str(uuid.uuid4()),
                entity_type=parsed.entity_type,
                canonical_name=parsed.canonical_name,
                display_name=parsed.display_name,
                platform=parsed.platform,
                environment=parsed.environment,
                criticality=parsed.criticality,
                owner=parsed.owner,
                lifecycle_state=parsed.lifecycle_state,
                source_system=parsed.source_system,
                external_ref=parsed.external_ref,
                entity_metadata=parsed.entity_metadata,
                created_at=now,
                updated_at=now,
            ))
        return "created"

    changed = (
        existing.entity_type != parsed.entity_type
        or existing.display_name != parsed.display_name
        or existing.platform != parsed.platform
        or existing.environment != parsed.environment
        or existing.criticality != parsed.criticality
        or existing.owner != parsed.owner
        or existing.lifecycle_state != parsed.lifecycle_state
        or existing.source_system != parsed.source_system
        or existing.external_ref != parsed.external_ref
        or existing.entity_metadata != parsed.entity_metadata
    )
    if changed:
        if not dry_run:
            existing.entity_type = parsed.entity_type
            existing.display_name = parsed.display_name
            existing.platform = parsed.platform
            existing.environment = parsed.environment
            existing.criticality = parsed.criticality
            existing.owner = parsed.owner
            existing.lifecycle_state = parsed.lifecycle_state
            existing.source_system = parsed.source_system
            existing.external_ref = parsed.external_ref
            existing.entity_metadata = parsed.entity_metadata
            existing.updated_at = now
        return "updated"
    return "unchanged"


def import_cmdb_entities(
    db: Session,
    entities_data: list[dict],
    *,
    dry_run: bool = False,
) -> CmdbImportResult:
    """Validate and upsert entities, persisting integrity findings where needed.

    Idempotent: re-importing the same data produces no new findings or duplicates.
    Duplicate canonical_name detection is scoped to the current import batch.
    """
    result = CmdbImportResult()

    def _emit(finding_type: str, severity: str, object_ref: str, summary: str, details: dict) -> None:
        ok = record_finding(
            db,
            finding_type=finding_type,
            severity=severity,
            object_type="cmdb_entity",
            object_ref=object_ref,
            summary=summary,
            details=details,
            dry_run=dry_run,
        )
        if ok:
            result.findings_created += 1

    parsed_entities = [_normalize(raw) for raw in entities_data]

    # Count occurrences of each canonical_name in this batch for duplicate detection.
    seen_names: dict[str, int] = {}
    for p in parsed_entities:
        if p.canonical_name:
            seen_names[p.canonical_name] = seen_names.get(p.canonical_name, 0) + 1

    processed_names: set[str] = set()

    for parsed in parsed_entities:
        if not parsed.canonical_name or not validate_canonical_name(parsed.canonical_name):
            ref = parsed.canonical_name or "<empty>"
            _emit(
                "invalid_canonical_name",
                "error",
                ref,
                f"CMDB entity canonical_name '{ref}' does not conform to the naming convention "
                "(<seg>.<seg>[.<seg>...], lowercase alphanumeric + hyphens).",
                {"canonical_name": ref},
            )
            if not parsed.canonical_name:
                continue

        if parsed.entity_type not in VALID_ENTITY_TYPES:
            _emit(
                "invalid_entity_type",
                "warning",
                parsed.canonical_name,
                f"CMDB entity '{parsed.canonical_name}' has unsupported entity_type '{parsed.entity_type}'.",
                {"entity_type": parsed.entity_type, "valid": sorted(VALID_ENTITY_TYPES)},
            )

        if seen_names.get(parsed.canonical_name, 0) > 1:
            if parsed.canonical_name in processed_names:
                # Subsequent duplicate occurrence: emit finding (idempotent) and skip upsert.
                _emit(
                    "duplicate_canonical_name",
                    "warning",
                    parsed.canonical_name,
                    f"CMDB canonical_name '{parsed.canonical_name}' appears more than once in the import batch.",
                    {"canonical_name": parsed.canonical_name, "count": seen_names[parsed.canonical_name]},
                )
                continue
            # First occurrence of a duplicate: emit finding and still upsert.
            _emit(
                "duplicate_canonical_name",
                "warning",
                parsed.canonical_name,
                f"CMDB canonical_name '{parsed.canonical_name}' appears more than once in the import batch.",
                {"canonical_name": parsed.canonical_name, "count": seen_names[parsed.canonical_name]},
            )

        processed_names.add(parsed.canonical_name)
        outcome = _upsert_entity(db, parsed, dry_run=dry_run)
        if outcome == "created":
            result.entities_created += 1
        elif outcome == "updated":
            result.entities_updated += 1
        else:
            result.entities_unchanged += 1

    if not dry_run:
        db.commit()

    return result


def load_seed_file(path: Path) -> list[dict]:
    """Load a YAML or JSON seed file and return the entities list."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return raw.get("entities", [])
