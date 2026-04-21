"""RM-GOV-BASELINE-INSPECTOR-SEAM-1: inspect governance/roadmap/integrity/planner/CMDB surfaces."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _try_parse(path: Path) -> dict:
    if not path.exists():
        return {"present": False, "parseable": False}
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return {"present": True, "parseable": True}
    except Exception:
        return {"present": True, "parseable": False}


def _inspect_governance_files() -> dict:
    targets = [
        "canonical_roadmap.json",
        "phase_gate_status.json",
        "current_phase.json",
        "tactical_family_classification.json",
        "next_package_class.json",
        "rm_gov_closeout.json",
    ]
    gov_dir = REPO_ROOT / "governance"
    result = {}
    for name in targets:
        result[name] = _try_parse(gov_dir / name)
    cfg_path = REPO_ROOT / "config" / "promotion_manifest.json"
    result["config/promotion_manifest.json"] = _try_parse(cfg_path)
    return result


def _inspect_docs() -> dict:
    docs_dir = REPO_ROOT / "docs"
    if not docs_dir.exists():
        return {"count": 0, "names": []}
    names = sorted(
        str(p.relative_to(REPO_ROOT))
        for p in docs_dir.rglob("*")
        if p.suffix in (".md", ".json") and p.is_file()
    )
    return {"count": len(names), "names": names}


def _inspect_makefile() -> list[str]:
    makefile = REPO_ROOT / "Makefile"
    if not makefile.exists():
        return []
    found = []
    keywords = re.compile(
        r"(integrity|naming|normalization|governance|roadmap|loe|feature-block|package-plan)"
    )
    for i, line in enumerate(makefile.read_text(encoding="utf-8").splitlines(), 1):
        if re.match(r"^[a-zA-Z0-9_-]+:", line) and keywords.search(line):
            target = line.split(":")[0].strip()
            found.append(f"{target}:{i}")
    return found


def _inspect_bin() -> list[str]:
    bin_dir = REPO_ROOT / "bin"
    keywords = re.compile(r"(integrity|roadmap|naming|loe|planner|rm_gov|normalization)")
    found = []
    for p in sorted(bin_dir.iterdir()):
        if not p.is_file():
            continue
        if keywords.search(p.name):
            found.append(p.name)
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()[:20]
            if any(keywords.search(ln) for ln in lines):
                found.append(p.name)
        except Exception:
            pass
    return found


def _inspect_framework() -> list[str]:
    fw_dir = REPO_ROOT / "framework"
    keywords = re.compile(r"(integrity|roadmap|cmdb|naming|loe|planner|rm_gov)")
    return sorted(
        p.name for p in fw_dir.iterdir()
        if p.is_file() and keywords.search(p.name)
    )


def _inspect_tests() -> list[str]:
    tests_dir = REPO_ROOT / "tests"
    keywords = re.compile(r"(rm_gov|integrity|naming|roadmap|cmdb_authority)")
    return sorted(
        p.name for p in tests_dir.iterdir()
        if p.is_file() and keywords.search(p.name)
    )


def _inspect_rm_gov_entries() -> tuple:
    path = REPO_ROOT / "governance" / "canonical_roadmap.json"
    if not path.exists():
        return None, None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None, None, None

    rm001 = rm002 = rm003 = None

    # Also check docs/roadmap/data/roadmap_registry.yaml text-search
    registry_path = REPO_ROOT / "docs" / "roadmap" / "data" / "roadmap_registry.yaml"
    if registry_path.exists():
        text = registry_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "RM-GOV-001" in line:
                rm001 = {"source": "docs/roadmap/data/roadmap_registry.yaml", "line": line.strip()}
            if "RM-GOV-002" in line:
                rm002 = {"source": "docs/roadmap/data/roadmap_registry.yaml", "line": line.strip()}
            if "RM-GOV-003" in line:
                rm003 = {"source": "docs/roadmap/data/roadmap_registry.yaml", "line": line.strip()}

    # Check item YAML files
    for item_id, target in [("RM-GOV-001", "rm001"), ("RM-GOV-002", "rm002"), ("RM-GOV-003", "rm003")]:
        item_path = REPO_ROOT / "docs" / "roadmap" / "items" / f"{item_id}.yaml"
        if item_path.exists():
            if target == "rm001":
                rm001 = {"source": str(item_path.relative_to(REPO_ROOT)), "present": True}
            elif target == "rm002":
                rm002 = {"source": str(item_path.relative_to(REPO_ROOT)), "present": True}
            elif target == "rm003":
                rm003 = {"source": str(item_path.relative_to(REPO_ROOT)), "present": True}

    return rm001, rm002, rm003


def _collect_gaps(governance_files: dict) -> list[str]:
    gaps = []
    required = ["canonical_roadmap.json", "phase_gate_status.json", "current_phase.json"]
    for name in required:
        info = governance_files.get(name, {})
        if not info.get("present"):
            gaps.append(f"Missing expected governance file: {name}")
        elif not info.get("parseable"):
            gaps.append(f"Governance file not parseable as JSON: {name}")
    return gaps


def run() -> dict:
    gov_files = _inspect_governance_files()
    rm001, rm002, rm003 = _inspect_rm_gov_entries()

    result = {
        "inspection_id": "RM-GOV-BASELINE-INSPECTOR-SEAM-1",
        "inspected_at": _iso_now(),
        "governance_files": gov_files,
        "docs_summary": _inspect_docs(),
        "makefile_targets_found": _inspect_makefile(),
        "bin_scripts_found": _inspect_bin(),
        "framework_modules_found": _inspect_framework(),
        "test_files_found": _inspect_tests(),
        "rm_gov_001_raw_entry": rm001,
        "rm_gov_002_raw_entry": rm002,
        "rm_gov_003_raw_entry": rm003,
        "baseline_gaps": _collect_gaps(gov_files),
    }

    out_dir = REPO_ROOT / "artifacts" / "rm_gov_verification"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "baseline.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    r = run()
    print(json.dumps({
        "governance_files_count": len(r["governance_files"]),
        "makefile_targets_found": r["makefile_targets_found"],
        "framework_modules_found": r["framework_modules_found"],
        "test_files_found": r["test_files_found"],
        "rm_gov_001_raw_entry": r["rm_gov_001_raw_entry"],
        "rm_gov_002_raw_entry": r["rm_gov_002_raw_entry"],
        "rm_gov_003_raw_entry": r["rm_gov_003_raw_entry"],
        "baseline_gaps": r["baseline_gaps"],
    }, indent=2))
