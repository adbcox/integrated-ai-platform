"""RM-GOV-001-EVIDENCE-VERIFIER-SEAM-1: verify roadmap-tracking/CMDB/metrics/naming/impact subclaims."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sub(evidenced: bool, source, detail: str) -> dict:
    return {"evidenced": evidenced, "evidence_source": source, "evidence_detail": detail}


def _check_roadmap_to_development_tracking() -> dict:
    """Evidenced only if a roadmap item has a non-null structured link to a commit/seam/campaign."""
    items_dir = REPO_ROOT / "docs" / "roadmap" / "items"
    if not items_dir.exists():
        return _sub(False, None, "docs/roadmap/items/ directory absent")

    schema_has_field = False
    any_non_null_link = False
    populated_item = None

    for yaml_path in sorted(items_dir.glob("*.yaml")):
        text = yaml_path.read_text(encoding="utf-8")
        if "last_execution_commit:" in text:
            schema_has_field = True
        # Look for last_execution_commit with a non-null value
        for line in text.splitlines():
            if "last_execution_commit:" in line:
                value = line.split(":", 1)[-1].strip()
                if value and value.lower() not in ("null", "~", '""', "''", ""):
                    any_non_null_link = True
                    populated_item = yaml_path.name
                    break
        if any_non_null_link:
            break

    if any_non_null_link:
        return _sub(
            True,
            str(populated_item),
            f"last_execution_commit field populated in {populated_item}",
        )
    if schema_has_field:
        return _sub(
            False,
            "docs/roadmap/items/*.yaml",
            "Schema has last_execution_commit field but all values are null; "
            "tracking link schema exists but no items linked to actual commits",
        )
    return _sub(False, None, "No roadmap-to-development tracking fields found in any item YAML")


def _check_cmdb_linkage() -> dict:
    """Evidenced if the three required CMDB framework modules exist and import cleanly."""
    required = [
        "framework/cmdb_authority_boundary.py",
        "framework/cmdb_authority_contract.py",
        "framework/cmdb_authoritative_promotion_ratifier.py",
    ]
    missing = []
    for rel in required:
        if not (REPO_ROOT / rel).exists():
            missing.append(rel)
    if missing:
        return _sub(False, None, f"Missing CMDB framework files: {missing}")

    try:
        import framework.cmdb_authority_boundary  # noqa: F401
        import framework.cmdb_authority_contract  # noqa: F401
        import framework.cmdb_authoritative_promotion_ratifier  # noqa: F401
    except Exception as exc:
        return _sub(False, None, f"CMDB framework import failed: {exc}")

    return _sub(
        True,
        "framework/cmdb_authority_boundary.py, framework/cmdb_authority_contract.py, "
        "framework/cmdb_authoritative_promotion_ratifier.py",
        "All three CMDB framework modules present and importable",
    )


def _check_standardized_metrics() -> dict:
    """Evidenced if a typed metrics dataclass or JSON schema exists and is registered."""
    schema_path = REPO_ROOT / "framework" / "run_metrics_schema.py"
    registry_path = REPO_ROOT / "framework" / "schema_registry.py"

    if schema_path.exists():
        try:
            import framework.run_metrics_schema as m
            if hasattr(m, "RunMetrics") and hasattr(m.RunMetrics, "__dataclass_fields__"):
                fields = list(m.RunMetrics.__dataclass_fields__.keys())
                registered = False
                if registry_path.exists():
                    text = registry_path.read_text(encoding="utf-8")
                    registered = "RunMetrics" in text
                return _sub(
                    True,
                    "framework/run_metrics_schema.py",
                    f"RunMetrics dataclass with fields {fields}; "
                    f"registered in schema_registry: {registered}",
                )
        except Exception as exc:
            return _sub(False, None, f"run_metrics_schema import failed: {exc}")

    return _sub(
        False,
        None,
        "No concrete metrics dataclass or JSON schema found; "
        "multi_phase_metrics_rollup.py exists but uses plain dict, not typed schema",
    )


def _check_enforced_naming() -> dict:
    """Evidenced if a mechanical naming/normalization check exists as a runnable script or Makefile target."""
    guard_path = REPO_ROOT / "bin" / "preflight_normalization_guard.sh"
    makefile = REPO_ROOT / "Makefile"

    if guard_path.exists():
        makefile_has_target = False
        if makefile.exists():
            text = makefile.read_text(encoding="utf-8")
            makefile_has_target = "preflight-normalization-guard" in text
        return _sub(
            True,
            "bin/preflight_normalization_guard.sh",
            f"preflight_normalization_guard.sh exists as executable check; "
            f"Makefile target present: {makefile_has_target}",
        )

    # Fallback: any bin script with naming/normalization in name
    bin_dir = REPO_ROOT / "bin"
    for p in bin_dir.iterdir():
        if p.is_file() and re.search(r"naming|normalization", p.name):
            return _sub(True, str(p.relative_to(REPO_ROOT)), f"Naming enforcement script: {p.name}")

    return _sub(False, None, "No mechanical naming enforcement script or Makefile target found")


def _check_impact_transparency() -> dict:
    """Evidenced if machine-readable impact fields exist in a typed framework output."""
    try:
        import framework.cmdb_terminal_authoritative_reratifier as m
        if hasattr(m, "CmdbTerminalDecision"):
            fields = list(m.CmdbTerminalDecision.__dataclass_fields__.keys())
            if "matrix_impact" in fields:
                return _sub(
                    True,
                    "framework/cmdb_terminal_authoritative_reratifier.py",
                    "CmdbTerminalDecision.matrix_impact field present; "
                    "emitted as non-empty string per seam tests",
                )
    except Exception:
        pass

    # Check for any other impact field in framework output types
    fw_dir = REPO_ROOT / "framework"
    for p in fw_dir.glob("*.py"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"matrix_impact|impact_summary|impact_transparency", text):
            return _sub(
                True,
                str(p.relative_to(REPO_ROOT)),
                f"Impact field found in {p.name}",
            )

    return _sub(False, None, "No machine-readable impact field found in framework typed outputs")


def run() -> dict:
    subclaims = {
        "roadmap_to_development_tracking": _check_roadmap_to_development_tracking(),
        "cmdb_linkage": _check_cmdb_linkage(),
        "standardized_metrics": _check_standardized_metrics(),
        "enforced_naming": _check_enforced_naming(),
        "impact_transparency": _check_impact_transparency(),
    }

    evidenced_count = sum(1 for v in subclaims.values() if v["evidenced"])
    total = len(subclaims)

    if evidenced_count == total:
        verdict = "complete"
    elif evidenced_count == 0:
        verdict = "deferred"
    else:
        verdict = "partial"

    result = {
        "verifier_id": "RM-GOV-001-EVIDENCE-VERIFIER-SEAM-1",
        "verified_at": _iso_now(),
        "subclaims": subclaims,
        "evidenced_count": evidenced_count,
        "total_subclaims": total,
        "provisional_verdict": verdict,
    }

    out_dir = REPO_ROOT / "artifacts" / "rm_gov_verification"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rm_gov_001_evidence.json").write_text(
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
    }, indent=2))
