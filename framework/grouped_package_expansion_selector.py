"""LACE1-P13-GROUPED-PACKAGE-EXPANSION-SEAM-1: re-apply RM-GOV-003 scoring to select next expansion package."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from roadmap_governance.planner_service import _collect_shared_touch_surfaces

assert callable(_collect_shared_touch_surfaces), "INTERFACE MISMATCH: _collect_shared_touch_surfaces not callable"

_CANDIDATE_PACKAGES = (
    {
        "package_id": "MT-RETRIEVAL-ENRICHMENT",
        "description": "Enrich stage_rag4 retrieval with additional entity signals and domain bonuses",
        "item_ids": ["RM-GOV-001", "RM-GOV-003"],
        "base_score": 0.72,
    },
    {
        "package_id": "MT-DECOMP-HANDOFF-WIRING",
        "description": "Wire TaskDecompositionSubstrate output into PlannerExecutorHandoff end-to-end",
        "item_ids": ["RM-GOV-002", "RM-GOV-003"],
        "base_score": 0.65,
    },
    {
        "package_id": "MT-TRACE-REPLAY-WIRING",
        "description": "Wire ExecutionTraceEnricher output through ReplayGate into a retry loop",
        "item_ids": ["RM-GOV-001", "RM-GOV-002"],
        "base_score": 0.60,
    },
)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass(frozen=True)
class PackageCandidate:
    package_id: str
    description: str
    item_ids: List[str]
    base_score: float
    shared_touch_surfaces: List[str]
    shared_touch_count: int
    final_score: float


@dataclass
class GroupedPackageSelectionRecord:
    selection_id: str
    selected_package_id: str
    scoring_method: str
    candidates: List[PackageCandidate]
    selected_at: str
    artifact_path: Optional[str] = None


class GroupedPackageExpansionSelector:
    """Select the highest-priority expansion package using RM-GOV-003 shared-touch scoring."""

    def select(self) -> GroupedPackageSelectionRecord:
        candidates: List[PackageCandidate] = []
        for c in _CANDIDATE_PACKAGES:
            surfaces = _collect_shared_touch_surfaces(list(c["item_ids"]))
            shared_touch_count = len(surfaces)
            final_score = round(c["base_score"] + 0.05 * shared_touch_count, 4)
            candidates.append(PackageCandidate(
                package_id=c["package_id"],
                description=c["description"],
                item_ids=list(c["item_ids"]),
                base_score=c["base_score"],
                shared_touch_surfaces=surfaces,
                shared_touch_count=shared_touch_count,
                final_score=final_score,
            ))

        ranked = sorted(candidates, key=lambda x: (x.shared_touch_count, x.final_score), reverse=True)
        selected = ranked[0]

        return GroupedPackageSelectionRecord(
            selection_id=f"GPSEL-LACE1-{_ts()}",
            selected_package_id=selected.package_id,
            scoring_method="rm_gov_003_shared_touch_count",
            candidates=ranked,
            selected_at=_iso_now(),
        )

    def emit(self, record: GroupedPackageSelectionRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "grouped_package_selection.json"
        payload = {
            "selection_id": record.selection_id,
            "selected_package_id": record.selected_package_id,
            "scoring_method": record.scoring_method,
            "selected_at": record.selected_at,
            "candidates": [asdict(c) for c in record.candidates],
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = [
    "PackageCandidate",
    "GroupedPackageSelectionRecord",
    "GroupedPackageExpansionSelector",
]
