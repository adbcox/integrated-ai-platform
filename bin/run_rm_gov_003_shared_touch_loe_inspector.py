"""RM-GOV-003-SHARED-TOUCH-LOE-INSPECTOR-SEAM-1: inspect planner_service.py and YAML metadata."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

_PLANNER_SERVICE = REPO_ROOT / "roadmap_governance" / "planner_service.py"
_ITEMS_DIR = REPO_ROOT / "docs" / "roadmap" / "items"
_PACKAGES_DIR = REPO_ROOT / "artifacts" / "governance" / "packages"

_LOE_KEYWORDS = ("shared_touch", "loe", "shared_touch_surfaces", "overlap_score")


def _inspect_planner_service() -> dict:
    text = _PLANNER_SERVICE.read_text(encoding="utf-8")
    found_keywords = [kw for kw in _LOE_KEYWORDS if kw in text]
    payload_match = re.search(r"payload\s*=\s*\{(.+?)\}", text, re.DOTALL)
    payload_keys: list[str] = []
    if payload_match:
        for line in payload_match.group(1).splitlines():
            m = re.search(r'"(\w+)"\s*:', line)
            if m:
                payload_keys.append(m.group(1))

    return {
        "path": str(_PLANNER_SERVICE.relative_to(REPO_ROOT)),
        "loe_keywords_found": found_keywords,
        "has_loe_output": len(found_keywords) > 0,
        "payload_keys_in_artifact": payload_keys,
        "shared_touch_in_payload": "shared_touch_surfaces" in payload_keys,
    }


def _inspect_yaml_shared_touch(item_id: str) -> dict:
    yaml_path = _ITEMS_DIR / f"{item_id}.yaml"
    if not yaml_path.exists():
        return {"item_id": item_id, "has_shared_touch_surfaces": False, "surfaces": []}

    text = yaml_path.read_text(encoding="utf-8")
    surfaces: list[str] = []
    in_shared = False
    for line in text.splitlines():
        if line.strip().startswith("shared_touch_surfaces:"):
            in_shared = True
            continue
        if in_shared:
            stripped = line.strip()
            if stripped.startswith("- "):
                surfaces.append(stripped[2:].strip().strip("\"'"))
            elif stripped and not stripped.startswith("#"):
                in_shared = False

    return {
        "item_id": item_id,
        "has_shared_touch_surfaces": len(surfaces) > 0,
        "surfaces": surfaces,
    }


def _inspect_package_artifacts() -> dict:
    if not _PACKAGES_DIR.exists():
        return {"packages_found": [], "any_has_shared_touch": False}

    packages = sorted(_PACKAGES_DIR.glob("PKG-*.json"))
    pkg_summaries = []
    any_has_shared_touch = False
    for pkg_path in packages:
        try:
            data = json.loads(pkg_path.read_text(encoding="utf-8"))
            has_shared_touch = "shared_touch_surfaces" in data or "shared_touch_count" in data
            if has_shared_touch:
                any_has_shared_touch = True
            pkg_summaries.append({
                "path": str(pkg_path.name),
                "package_id": data.get("package_id"),
                "has_shared_touch_surfaces": has_shared_touch,
                "keys": list(data.keys()),
            })
        except Exception as e:
            pkg_summaries.append({"path": str(pkg_path.name), "error": str(e)})

    return {
        "packages_found": pkg_summaries,
        "any_has_shared_touch": any_has_shared_touch,
        "total_packages": len(packages),
    }


def run_inspection() -> dict:
    planner_result = _inspect_planner_service()

    yaml_results = {
        item_id: _inspect_yaml_shared_touch(item_id)
        for item_id in ("RM-GOV-001", "RM-GOV-002", "RM-GOV-003")
    }
    any_yaml_has_surfaces = any(v["has_shared_touch_surfaces"] for v in yaml_results.values())

    pkg_result = _inspect_package_artifacts()

    gap_confirmed = (
        not planner_result["has_loe_output"]
        and not pkg_result["any_has_shared_touch"]
    )

    return {
        "inspection_id": "RM-GOV-003-SHARED-TOUCH-LOE-INSPECTOR-SEAM-1",
        "planner_service": planner_result,
        "yaml_shared_touch": yaml_results,
        "any_yaml_has_surfaces": any_yaml_has_surfaces,
        "package_artifacts": pkg_result,
        "gap_confirmed": gap_confirmed,
        "resolution_required": (
            "Add shared_touch_surfaces and shared_touch_count to planner_service.py payload"
            if gap_confirmed else "Gap already resolved"
        ),
    }


def emit_inspection(result: dict, artifact_dir: Path = REPO_ROOT / "artifacts" / "rm_gov_verification") -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "loe_inspection.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return str(out_path)


if __name__ == "__main__":
    result = run_inspection()
    path = emit_inspection(result)
    print(f"LOE inspection artifact: {path}")
    print(json.dumps(result, indent=2))
