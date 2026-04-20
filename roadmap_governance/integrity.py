"""RGC integrity review service: per-item token checks + cross-item near-duplicate detection.

run_integrity_review is the public entry point; it is safe to rerun (idempotent via
finding_exists) and writes timestamped artifacts under artifacts/governance/integrity/.
"""

from __future__ import annotations

import difflib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from roadmap_governance.models import RoadmapItem
from roadmap_governance.service import record_finding

# Tokens loaded from docs/roadmap/data/enums.yaml at import time.
# Kept as frozensets for O(1) membership testing.
VALID_PRIORITIES: frozenset[str] = frozenset({"P0", "P1", "P2", "P3", "P4"})
VALID_ITEM_TYPES: frozenset[str] = frozenset(
    {
        "platform_foundation",
        "capability",
        "workflow",
        "integration",
        "interface",
        "infrastructure",
        "research",
        "governance",
        "automation",
        "hardware",
        "domain_app",
        # "unknown" is a system placeholder for markdown-only items; exempt from check.
    }
)
VALID_CATEGORIES: frozenset[str] = frozenset(
    {
        "GOV",
        "CORE",
        "DEV",
        "UI",
        "AUTO",
        "OPS",
        "INV",
        "MEDIA",
        "HOME",
        "LANG",
        "HW",
        "SHOP",
        "AUTO-MECH",
        "DOCAPP",
        "INTEL",
    }
)

NEAR_DUPLICATE_THRESHOLD: float = 0.85

# Naming regex (mirrors parser.py — single source of truth lives there, replicated here
# to avoid a circular import through service → parser).
_NAMING_RE = re.compile(
    r"^RM-([A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*)-(\d{3,})$"
)

_ARTIFACT_DIR_DEFAULT = Path("artifacts") / "governance" / "integrity"


@dataclass
class IntegrityReviewResult:
    items_checked: int = 0
    findings_created: int = 0
    findings_skipped: int = 0
    artifact_path: Optional[str] = None
    check_counts: dict = field(default_factory=dict)


def _normalize_title(title: str) -> str:
    """Lowercase, strip punctuation/whitespace for fuzzy comparison."""
    title = title.lower()
    title = unicodedata.normalize("NFKD", title)
    title = re.sub(r"[^\w\s]", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def _pair_ref(id_a: str, id_b: str) -> str:
    """Stable pair key regardless of iteration order."""
    lo, hi = sorted([id_a, id_b])
    return f"{lo}|{hi}"


def run_integrity_review(
    db: Session,
    repo_root: Path,
    *,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> IntegrityReviewResult:
    """Run all integrity checks against current DB state and persist findings.

    Safe to rerun: active findings are not re-created (idempotence via finding_exists).
    Resolved findings are re-raised if the underlying issue persists.
    """
    result = IntegrityReviewResult()
    check_counts: dict[str, int] = {}

    items: list[RoadmapItem] = db.query(RoadmapItem).order_by(RoadmapItem.id).all()
    result.items_checked = len(items)

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
        check_counts[finding_type] = check_counts.get(finding_type, 0) + 1
        if ok:
            result.findings_created += 1
        else:
            result.findings_skipped += 1

    # ── Per-item checks ──────────────────────────────────────────────────────
    for item in items:
        if not _NAMING_RE.match(item.id):
            _emit(
                "naming_violation",
                "error",
                item.id,
                f"Item '{item.id}' does not conform to RM-<DOMAIN>-<NNN> naming convention.",
                {"id": item.id},
            )

        if item.priority not in VALID_PRIORITIES:
            _emit(
                "invalid_priority",
                "warning",
                item.id,
                f"Item '{item.id}' has unrecognised priority '{item.priority}'.",
                {"priority": item.priority, "valid": sorted(VALID_PRIORITIES)},
            )

        if item.item_type != "unknown" and item.item_type not in VALID_ITEM_TYPES:
            _emit(
                "invalid_item_type",
                "warning",
                item.id,
                f"Item '{item.id}' has unrecognised item_type '{item.item_type}'.",
                {"item_type": item.item_type, "valid": sorted(VALID_ITEM_TYPES)},
            )

        if item.category not in VALID_CATEGORIES:
            _emit(
                "invalid_category",
                "warning",
                item.id,
                f"Item '{item.id}' has unrecognised category '{item.category}'.",
                {"category": item.category, "valid": sorted(VALID_CATEGORIES)},
            )

    # ── Cross-item: near-duplicate titles ────────────────────────────────────
    normalized = [(item.id, _normalize_title(item.title)) for item in items]
    for i in range(len(normalized)):
        for j in range(i + 1, len(normalized)):
            id_a, norm_a = normalized[i]
            id_b, norm_b = normalized[j]
            ratio = _similarity(norm_a, norm_b)
            if ratio >= NEAR_DUPLICATE_THRESHOLD:
                pair = _pair_ref(id_a, id_b)
                _emit(
                    "near_duplicate_title",
                    "warning",
                    pair,
                    f"Items '{id_a}' and '{id_b}' have near-duplicate titles (similarity {ratio:.2f}).",
                    {"id_a": id_a, "id_b": id_b, "similarity": round(ratio, 4)},
                )

    if not dry_run:
        db.commit()

    result.check_counts = check_counts
    result.artifact_path = _write_artifact(result, repo_root, artifact_dir, dry_run=dry_run)
    return result


def _write_artifact(
    result: IntegrityReviewResult,
    repo_root: Path,
    artifact_dir: Optional[Path],
    *,
    dry_run: bool,
) -> Optional[str]:
    if dry_run:
        return None
    base = (repo_root / artifact_dir) if artifact_dir else (repo_root / _ARTIFACT_DIR_DEFAULT)
    base.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "generated_at": ts,
        "items_checked": result.items_checked,
        "findings_created": result.findings_created,
        "findings_skipped": result.findings_skipped,
        "check_counts": result.check_counts,
    }
    timestamped = base / f"integrity_review_{ts}.json"
    latest = base / "latest.json"

    timestamped.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(timestamped)
