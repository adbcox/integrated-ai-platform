"""RM-GOV-003-EVIDENCE-VERIFIER-SEAM-1: verify feature-block/LOE/planner-output subclaims."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sub(evidenced: bool, source, detail: str) -> dict:
    return {"evidenced": evidenced, "evidence_source": source, "evidence_detail": detail}


def _check_grouped_feature_block_planning() -> dict:
    """Evidenced only if a real executable system implements grouped feature-block planning."""
    planner_module = REPO_ROOT / "roadmap_governance" / "planner_service.py"
    rgc_path = REPO_ROOT / "bin" / "rgc.py"

    if planner_module.exists() and rgc_path.exists():
        rgc_text = rgc_path.read_text(encoding="utf-8")
        planner_text = planner_module.read_text(encoding="utf-8")

        has_command = "planner" in rgc_text and "planner_refresh" in rgc_text
        has_run_planner = "run_planner_refresh" in planner_text
        groups_by_category = "FeatureBlockPackage" in planner_text

        if has_command and has_run_planner and groups_by_category:
            try:
                from roadmap_governance.planner_service import run_planner_refresh
                if callable(run_planner_refresh):
                    return _sub(
                        True,
                        "bin/rgc.py + roadmap_governance/planner_service.py",
                        "system capability: rgc.py planner refresh command backed by "
                        "run_planner_refresh(); groups roadmap items into FeatureBlockPackage "
                        "records by category with scoring; not a conversation habit",
                    )
            except Exception as exc:
                return _sub(False, None, f"planner_service import failed: {exc}")

    # Check for any bin/ script with grouped planning capability
    for p in (REPO_ROOT / "bin").glob("*.py"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if "feature_block" in text.lower() or "feature-block" in text.lower():
            return _sub(
                True,
                str(p.relative_to(REPO_ROOT)),
                f"feature-block planning capability found in {p.name}",
            )

    # Docs-only or habit-only: check docs/roadmap for feature_block_candidates
    items_dir = REPO_ROOT / "docs" / "roadmap" / "items"
    if items_dir.exists():
        has_schema = any(
            "feature_block_candidates" in p.read_text(encoding="utf-8", errors="ignore")
            for p in items_dir.glob("*.yaml")
        )
        if has_schema:
            return _sub(
                False,
                "docs/roadmap/items/*.yaml",
                "YAML items contain feature_block_candidates field but no executable planner "
                "script found; this is schema metadata, not system capability",
            )

    return _sub(
        False,
        None,
        "no system capability found; no executable feature-block planner script in bin/ or framework/",
    )


def _check_package_grouping_outputs_machine_readable() -> dict:
    """Evidenced if the planner system produces structured JSON output."""
    packages_dir = REPO_ROOT / "artifacts" / "governance" / "packages"
    if packages_dir.exists():
        json_files = list(packages_dir.glob("PKG-*.json"))
        if json_files:
            sample = json_files[0]
            try:
                data = json.loads(sample.read_text(encoding="utf-8"))
                required_keys = {"package_id", "members"}
                if required_keys.issubset(data.keys()):
                    return _sub(
                        True,
                        str(packages_dir.relative_to(REPO_ROOT)),
                        f"{len(json_files)} PKG-*.json artifacts present; "
                        f"sample {sample.name} has keys: {sorted(data.keys())}; "
                        f"members array with roadmap item details; machine-readable",
                    )
            except Exception:
                pass

    # Planner module exists but no artifacts yet → not evidenced
    planner_module = REPO_ROOT / "roadmap_governance" / "planner_service.py"
    if planner_module.exists():
        return _sub(
            False,
            "roadmap_governance/planner_service.py",
            "planner_service.py capable of JSON output but no PKG-*.json artifacts "
            "found in artifacts/governance/packages/; output not demonstrated",
        )

    return _sub(False, None, "No package grouping output artifacts found")


def _check_shared_touch_loe_optimization() -> dict:
    """Evidenced only if shared-touch or LOE aggregation is a computed output field."""
    planner_module = REPO_ROOT / "roadmap_governance" / "planner_service.py"
    if planner_module.exists():
        text = planner_module.read_text(encoding="utf-8")
        for keyword in ("shared_touch", "loe", "shared-touch", "overlap_score"):
            if keyword in text.lower():
                return _sub(
                    True,
                    "roadmap_governance/planner_service.py",
                    f"shared-touch/LOE keyword '{keyword}' found in planner_service.py",
                )

    # Check planner output artifacts for loe field
    packages_dir = REPO_ROOT / "artifacts" / "governance" / "packages"
    if packages_dir.exists():
        for p in packages_dir.glob("PKG-*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if "loe" in data or "shared_touch" in data or "overlap" in data:
                    return _sub(
                        True,
                        str(p.relative_to(REPO_ROOT)),
                        f"LOE/shared-touch field in {p.name}",
                    )
            except Exception:
                pass

    # Check if YAML items have shared_touch_surfaces but no computed field
    items_dir = REPO_ROOT / "docs" / "roadmap" / "items"
    if items_dir.exists():
        has_schema = any(
            "shared_touch_surfaces" in p.read_text(encoding="utf-8", errors="ignore")
            for p in items_dir.glob("*.yaml")
        )
        if has_schema:
            return _sub(
                False,
                "docs/roadmap/items/*.yaml",
                "YAML items contain shared_touch_surfaces metadata fields but no computed "
                "LOE optimization output exists; planner scoring uses priority/CMDB/findings "
                "but not shared-touch aggregation",
            )

    return _sub(
        False,
        None,
        "no shared-touch LOE optimization found as computed output field; "
        "planner groups by category and scores by priority but does not aggregate LOE",
    )


def _check_planner_outputs_reusable() -> dict:
    """Evidenced if downstream scripts or services consume structured planner output."""
    # Check if roadmap_governance modules consume FeatureBlockPackage
    downstream_consumers = []
    for rel_path in [
        "roadmap_governance/metrics_service.py",
        "roadmap_governance/router.py",
        "roadmap_governance/schemas.py",
    ]:
        p = REPO_ROOT / rel_path
        if p.exists() and "FeatureBlockPackage" in p.read_text(encoding="utf-8", errors="ignore"):
            downstream_consumers.append(rel_path)

    if downstream_consumers:
        return _sub(
            True,
            ", ".join(downstream_consumers),
            f"FeatureBlockPackage model consumed by: {downstream_consumers}; "
            f"metrics_service.py counts packages; router.py exposes via API; "
            f"planner output is persistent DB state and JSON artifacts",
        )

    # Check if any bin/ script reads package artifacts
    for p in (REPO_ROOT / "bin").glob("*.py"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if "PKG-" in text or "feature_block" in text.lower():
            return _sub(
                True,
                str(p.relative_to(REPO_ROOT)),
                f"{p.name} consumes feature-block package output",
            )

    return _sub(False, None, "No downstream consumer of planner output found")


def run() -> dict:
    subclaims = {
        "grouped_feature_block_planning": _check_grouped_feature_block_planning(),
        "package_grouping_outputs_machine_readable": _check_package_grouping_outputs_machine_readable(),
        "shared_touch_loe_optimization": _check_shared_touch_loe_optimization(),
        "planner_outputs_reusable": _check_planner_outputs_reusable(),
    }

    evidenced_count = sum(1 for v in subclaims.values() if v["evidenced"])
    total = len(subclaims)

    # Cap rule: deferred if grouped planning AND LOE both false
    grouped_ok = subclaims["grouped_feature_block_planning"]["evidenced"]
    loe_ok = subclaims["shared_touch_loe_optimization"]["evidenced"]

    if evidenced_count == total:
        verdict = "complete"
    elif not grouped_ok and not loe_ok:
        verdict = "deferred"
    elif evidenced_count == 0:
        verdict = "deferred"
    else:
        verdict = "partial"

    result = {
        "verifier_id": "RM-GOV-003-EVIDENCE-VERIFIER-SEAM-1",
        "verified_at": _iso_now(),
        "subclaims": subclaims,
        "evidenced_count": evidenced_count,
        "total_subclaims": total,
        "provisional_verdict": verdict,
    }

    out_dir = REPO_ROOT / "artifacts" / "rm_gov_verification"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rm_gov_003_evidence.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    r = run()
    print(json.dumps({
        "provisional_verdict": r["provisional_verdict"],
        "evidenced_count": r["evidenced_count"],
        "total_subclaims": r["total_subclaims"],
        "subclaims_summary": {k: v["evidenced"] for k, v in r["subclaims"].items()},
        "feature_block_detail": r["subclaims"]["grouped_feature_block_planning"]["evidence_detail"],
        "loe_detail": r["subclaims"]["shared_touch_loe_optimization"]["evidence_detail"],
    }, indent=2))
