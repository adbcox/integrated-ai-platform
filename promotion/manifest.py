"""Helpers for reading the promotion manifest and resolving lane metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "config" / "promotion_manifest.json"


@dataclass(frozen=True)
class PromotionConfig:
    """Typed view over the promotion manifest."""

    data: Dict[str, Any]

    def lane(self, name: str) -> Dict[str, Any]:
        return resolve_lane_config(self.data, name)

    @property
    def version(self) -> int:
        return int(self.data.get("version", 0))

    @property
    def subsystem_levels(self) -> Dict[str, Any]:
        return dict(self.data.get("subsystem_levels", {}))


def load_manifest(path: str | Path | None = None) -> PromotionConfig:
    """Load and parse the promotion manifest."""
    manifest_path = Path(path or MANIFEST_PATH)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return PromotionConfig(data=data)


def resolve_lane_config(manifest: Dict[str, Any], lane_name: str) -> Dict[str, Any]:
    lanes = manifest.get("lanes", {})
    if lane_name not in lanes:
        raise KeyError(f"lane '{lane_name}' not defined in promotion manifest")
    lane = dict(lanes[lane_name])
    lane["name"] = lane_name
    return lane


def resolve_versions_for_lane(manifest: Dict[str, Any], lane_name: str) -> Dict[str, Any]:
    lane = resolve_lane_config(manifest, lane_name)
    stage_versions = manifest.get("stage_versions", {})
    manager_versions = manifest.get("manager_versions", {})
    rag_versions = manifest.get("rag_versions", {})

    stage_version_name = lane.get("stage_version")
    manager_version_name = lane.get("manager_version")
    rag_version_name = lane.get("rag_version")

    stage_details = stage_versions.get(stage_version_name, {})
    manager_details = manager_versions.get(manager_version_name, {})
    rag_details = rag_versions.get(rag_version_name, {})

    return {
        "lane": lane,
        "stage_version_name": stage_version_name,
        "stage": stage_details.get("stage"),
        "stage_details": stage_details,
        "manager_version_name": manager_version_name,
        "manager_details": manager_details,
        "rag_version_name": rag_version_name,
        "rag_details": rag_details,
    }
