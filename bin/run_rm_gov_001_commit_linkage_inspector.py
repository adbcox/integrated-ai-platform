"""RM-GOV-001-COMMIT-LINKAGE-INSPECTOR-SEAM-1: inspect YAML fields and identify linkable commits."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ITEM_IDS = ("RM-GOV-001", "RM-GOV-002", "RM-GOV-003")

_KEYWORD_COMMITS = {
    "RM-GOV-001": [
        "ROADMAP-ITEM-INGEST-1",
        "ROADMAP-CANONICAL-BOOTSTRAP",
    ],
    "RM-GOV-002": [
        "GOV-PHASE0-RECONCILE",
        "RECON-W1",
        "CAP-P2-CLOSE",
    ],
    "RM-GOV-003": [
        "RECON-W1",
        "CAP-P3-CLOSE",
        "CAP-P4-CLOSE",
    ],
}

_FILE_PROBES = {
    "RM-GOV-001": [
        "docs/roadmap/items/RM-GOV-001.yaml",
        "docs/roadmap/data/roadmap_registry.yaml",
    ],
    "RM-GOV-002": [
        "governance/current_phase.json",
        "governance/canonical_roadmap.json",
    ],
    "RM-GOV-003": [
        "governance/authority_adr_0001_source_of_truth.md",
        "governance/authority_adr_0002_tactical_family_classification.md",
    ],
}


def _git_log_oneline(n: int = 80) -> list[dict]:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "log", f"--max-count={n}", "--pretty=format:%H %s"],
        capture_output=True, text=True,
    )
    entries = []
    for line in result.stdout.splitlines():
        if " " in line:
            sha, msg = line.split(" ", 1)
            entries.append({"sha": sha, "message": msg})
    return entries


def _git_log_for_file(path: str) -> list[dict]:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "log", "--follow", "--pretty=format:%H %s", "--", path],
        capture_output=True, text=True,
    )
    entries = []
    for line in result.stdout.splitlines():
        if " " in line:
            sha, msg = line.split(" ", 1)
            entries.append({"sha": sha, "message": msg})
    return entries


def _read_yaml_field(yaml_path: Path, field_path: str) -> object:
    """Read a dot-delimited field from YAML using simple line scan (no PyYAML dependency)."""
    key = field_path.split(".")[-1]
    if not yaml_path.exists():
        return None
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{key}:"):
            value = stripped[len(f"{key}:"):].strip()
            if value in ("null", "~", ""):
                return None
            if value.startswith('"') or value.startswith("'"):
                return value.strip("\"'")
            return value
    return None


def _find_keyword_commits(all_commits: list[dict], keywords: list[str]) -> list[dict]:
    found = []
    for commit in all_commits:
        for kw in keywords:
            if kw in commit["message"]:
                found.append(commit)
                break
    return found


def inspect_item(item_id: str, all_commits: list[dict]) -> dict:
    yaml_path = REPO_ROOT / "docs" / "roadmap" / "items" / f"{item_id}.yaml"
    current_commit = _read_yaml_field(yaml_path, "execution.last_execution_commit")

    lines = yaml_path.read_text(encoding="utf-8").splitlines() if yaml_path.exists() else []
    in_refs = False
    refs = []
    for line in lines:
        if line.strip().startswith("execution_package_refs:"):
            in_refs = True
            continue
        if in_refs:
            stripped = line.strip()
            if stripped.startswith("- "):
                refs.append(stripped[2:].strip().strip("\"'"))
            elif stripped and not stripped.startswith("#"):
                in_refs = False

    keyword_commits = _find_keyword_commits(all_commits, _KEYWORD_COMMITS.get(item_id, []))

    file_commits: dict[str, list[dict]] = {}
    for probe_file in _FILE_PROBES.get(item_id, []):
        file_commits[probe_file] = _git_log_for_file(probe_file)[:3]

    # Prefer keyword match; fall back to oldest file-history commit for the primary probe file
    best_sha = None
    best_msg = None
    if keyword_commits:
        best_sha = keyword_commits[0]["sha"]
        best_msg = keyword_commits[0]["message"]
    else:
        probes = _FILE_PROBES.get(item_id, [])
        for probe_file in probes:
            history = file_commits.get(probe_file, [])
            if history:
                # oldest (last in list) is most canonical creation commit
                oldest = history[-1]
                best_sha = oldest["sha"]
                best_msg = oldest["message"]
                break

    return {
        "item_id": item_id,
        "yaml_path": str(yaml_path.relative_to(REPO_ROOT)),
        "current_last_execution_commit": current_commit,
        "current_execution_package_refs": refs,
        "linkable_commits": keyword_commits[:3],
        "file_history_probes": file_commits,
        "recommended_sha": best_sha,
        "recommended_message": best_msg,
        "needs_population": current_commit is None,
    }


def run_inspection() -> dict:
    all_commits = _git_log_oneline(100)
    items: dict[str, dict] = {}
    for item_id in ITEM_IDS:
        items[item_id] = inspect_item(item_id, all_commits)

    items_needing_population = [k for k, v in items.items() if v["needs_population"]]
    all_have_recommendations = all(
        v["recommended_sha"] is not None for v in items.values()
    )

    return {
        "inspection_id": "RM-GOV-001-COMMIT-LINKAGE-INSPECTOR-SEAM-1",
        "items": items,
        "items_needing_population": items_needing_population,
        "all_have_recommendations": all_have_recommendations,
        "total_items": len(ITEM_IDS),
    }


def emit_inspection(result: dict, artifact_dir: Path = REPO_ROOT / "artifacts" / "rm_gov_verification") -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "commit_linkage_inspection.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return str(out_path)


if __name__ == "__main__":
    result = run_inspection()
    path = emit_inspection(result)
    print(f"Inspection artifact: {path}")
    print(json.dumps(result, indent=2))
