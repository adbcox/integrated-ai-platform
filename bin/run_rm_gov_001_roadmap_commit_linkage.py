"""RM-GOV-001-ROADMAP-COMMIT-LINKAGE-SEAM-1: populate last_execution_commit in RM-GOV YAML items."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

INSPECTION_ARTIFACT = (
    REPO_ROOT / "artifacts" / "rm_gov_verification" / "commit_linkage_inspection.json"
)

ITEM_IDS = ("RM-GOV-001", "RM-GOV-002", "RM-GOV-003")


def _load_inspection() -> dict:
    return json.loads(INSPECTION_ARTIFACT.read_text(encoding="utf-8"))


def _yaml_path(item_id: str) -> Path:
    return REPO_ROOT / "docs" / "roadmap" / "items" / f"{item_id}.yaml"


def _set_last_execution_commit(yaml_path: Path, sha: str) -> bool:
    """Replace `last_execution_commit: null` with the given SHA. Returns True if changed."""
    text = yaml_path.read_text(encoding="utf-8")
    pattern = re.compile(r"(^  last_execution_commit:\s*)null\s*$", re.MULTILINE)
    if not pattern.search(text):
        # Already set or field absent
        return False
    new_text = pattern.sub(rf'\g<1>"{sha}"', text)
    yaml_path.write_text(new_text, encoding="utf-8")
    return True


def _read_last_execution_commit(yaml_path: Path) -> object:
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("last_execution_commit:"):
            value = stripped[len("last_execution_commit:"):].strip()
            if value in ("null", "~", ""):
                return None
            return value.strip("\"'")
    return None


def run_linkage() -> dict:
    inspection = _load_inspection()
    results: dict[str, dict] = {}

    for item_id in ITEM_IDS:
        item_data = inspection["items"].get(item_id, {})
        sha = item_data.get("recommended_sha")
        yaml_path = _yaml_path(item_id)

        if sha is None:
            results[item_id] = {
                "item_id": item_id,
                "sha_used": None,
                "changed": False,
                "error": "no recommended_sha in inspection artifact",
            }
            continue

        changed = _set_last_execution_commit(yaml_path, sha)
        current = _read_last_execution_commit(yaml_path)
        results[item_id] = {
            "item_id": item_id,
            "sha_used": sha,
            "changed": changed,
            "last_execution_commit_after": current,
            "populated": current is not None,
        }

    all_populated = all(r.get("populated", False) for r in results.values())

    return {
        "linkage_id": "RM-GOV-001-ROADMAP-COMMIT-LINKAGE-SEAM-1",
        "items": results,
        "all_populated": all_populated,
        "total_items": len(ITEM_IDS),
    }


def verify_tracking_subclaim_flips() -> dict:
    """Re-run the RM-GOV-001 verifier and confirm roadmap_to_development_tracking is evidenced."""
    import importlib.util

    verifier_path = REPO_ROOT / "bin" / "run_rm_gov_001_verifier.py"
    spec = importlib.util.spec_from_file_location("run_rm_gov_001_verifier", verifier_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    result = mod.run()
    tracking = result.get("subclaims", {}).get("roadmap_to_development_tracking", {})
    return {
        "evidenced": tracking.get("evidenced", False),
        "evidence_detail": tracking.get("evidence_detail", ""),
        "full_verdict": result.get("provisional_verdict"),
    }


def emit_linkage(result: dict, artifact_dir: Path = REPO_ROOT / "artifacts" / "rm_gov_verification") -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "commit_linkage_result.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return str(out_path)


if __name__ == "__main__":
    result = run_linkage()
    path = emit_linkage(result)
    print(f"Linkage artifact: {path}")
    print(json.dumps(result, indent=2))

    print("\n--- Verifying roadmap_to_development_tracking flip ---")
    flip = verify_tracking_subclaim_flips()
    print(json.dumps(flip, indent=2))
