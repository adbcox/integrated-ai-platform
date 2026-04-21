#!/usr/bin/env python3
"""P0-04: Validate CMDB-lite registry and emit validation artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REGISTRY_PATH = REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml"
ARTIFACT_PATH = REPO_ROOT / "artifacts/governance/cmdb_lite_registry_validation.json"

GROUNDING_INPUTS = [
    REPO_ROOT / "artifacts/governance/phase_authority_inventory.json",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
    REPO_ROOT / "governance/execution_control_package.schema.json",
    REPO_ROOT / "governance/execution_control_package.example.json",
    REPO_ROOT / "docs/specs/execution_control_package.md",
]

REQUIRED_SECTIONS = [
    "registry_version",
    "phase",
    "subsystems",
    "migration_map",
    "model_profiles",
    "runtime_contract",
    "artifact_policy",
    "adapter_status",
    "waivers",
    "autonomy_scorecard",
    "environments",
]

REQUIRED_SUBSYSTEMS = [
    "control_plane",
    "inference_fabric",
    "agent_runtime",
    "retrieval_memory",
    "evaluation_governance",
]

REQUIRED_MODEL_PROFILES = ["fast", "balanced", "hard"]

REQUIRED_RUNTIME_CONTRACT_KEYS = [
    "session_job_schema",
    "tool_contract",
    "workspace_contract",
    "artifact_contract",
]

REQUIRED_ARTIFACT_POLICY_KEYS = ["artifact_root", "retention_policy"]

REQUIRED_ADAPTER_KEYS = ["aider", "claude", "codex"]

REQUIRED_AUTONOMY_KEYS = [
    "first_pass_success",
    "retry_count",
    "escalation_rate",
    "artifact_completeness",
]


def _load_yaml(path: Path):
    """Load YAML using stdlib-only fallback or PyYAML if available."""
    try:
        import yaml  # type: ignore
        return yaml.safe_load(path.read_text(encoding="utf-8")), None
    except ImportError:
        pass
    # stdlib fallback: parse subset of YAML sufficient for validation
    return _minimal_yaml_load(path.read_text(encoding="utf-8")), None


def _minimal_yaml_load(text: str) -> dict:
    """
    Parse a restricted YAML subset: top-level keys only, sufficient to verify
    required section presence without a full YAML library.
    Detects top-level keys (lines that start with non-whitespace word chars followed by colon).
    """
    import re
    top_keys = {}
    current_key = None
    lines = text.splitlines()
    for line in lines:
        if line.startswith("#") or not line.strip():
            continue
        # Top-level key: no leading whitespace, word chars + colon
        m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
        if m:
            current_key = m.group(1)
            top_keys[current_key] = True
    return top_keys


def _verify_grounding() -> bool:
    all_ok = True
    for p in GROUNDING_INPUTS:
        ok = p.exists() and p.stat().st_size > 50
        print(f"  grounding [{'OK' if ok else 'FAIL'}]: {p.relative_to(REPO_ROOT)}")
        if not ok:
            all_ok = False
    return all_ok


def _check_content(reg: dict) -> tuple[bool, list[str]]:
    errors = []

    # Subsystems
    subs = reg.get("subsystems", {})
    if not isinstance(subs, dict):
        errors.append("subsystems must be a mapping")
    else:
        for key in REQUIRED_SUBSYSTEMS:
            if key not in subs:
                errors.append(f"subsystems missing required key: {key}")

    # Migration map
    mm = reg.get("migration_map", [])
    if not isinstance(mm, list) or len(mm) < 5:
        errors.append(f"migration_map must have >= 5 entries, got {len(mm) if isinstance(mm, list) else 'non-list'}")

    # Model profiles
    mp = reg.get("model_profiles", {})
    if not isinstance(mp, dict):
        errors.append("model_profiles must be a mapping")
    else:
        for key in REQUIRED_MODEL_PROFILES:
            if key not in mp:
                errors.append(f"model_profiles missing required profile: {key}")

    # Runtime contract
    rc = reg.get("runtime_contract", {})
    if not isinstance(rc, dict):
        errors.append("runtime_contract must be a mapping")
    else:
        for key in REQUIRED_RUNTIME_CONTRACT_KEYS:
            if key not in rc:
                errors.append(f"runtime_contract missing required key: {key}")

    # Artifact policy
    ap = reg.get("artifact_policy", {})
    if not isinstance(ap, dict):
        errors.append("artifact_policy must be a mapping")
    else:
        for key in REQUIRED_ARTIFACT_POLICY_KEYS:
            if key not in ap:
                errors.append(f"artifact_policy missing required key: {key}")

    # Adapter status
    ads = reg.get("adapter_status", {})
    if not isinstance(ads, dict):
        errors.append("adapter_status must be a mapping")
    else:
        for key in REQUIRED_ADAPTER_KEYS:
            if key not in ads:
                errors.append(f"adapter_status missing required key: {key}")

    # Autonomy scorecard
    asc = reg.get("autonomy_scorecard", {})
    if not isinstance(asc, dict):
        errors.append("autonomy_scorecard must be a mapping")
    else:
        for key in REQUIRED_AUTONOMY_KEYS:
            if key not in asc:
                errors.append(f"autonomy_scorecard missing required key: {key}")

    # Phase fields
    ph = reg.get("phase", {})
    if not isinstance(ph, dict):
        errors.append("phase must be a mapping")
    else:
        if "current" not in ph:
            errors.append("phase missing 'current' field")
        if "status" not in ph:
            errors.append("phase missing 'status' field")

    # Environments must exist (placeholder ok)
    if "environments" not in reg:
        errors.append("environments section missing")

    return len(errors) == 0, errors


def main() -> None:
    print("P0-04: verifying grounding inputs...")
    if not _verify_grounding():
        print("HARD STOP: grounding inputs missing", file=sys.stderr)
        sys.exit(1)

    print("Loading registry YAML...")
    reg, err = _load_yaml(REGISTRY_PATH)
    if reg is None:
        print(f"HARD STOP: registry load failed: {err}", file=sys.stderr)
        sys.exit(1)
    yaml_loaded = True
    print(f"  yaml loaded: {REGISTRY_PATH.relative_to(REPO_ROOT)}")
    print(f"  top-level keys: {list(reg.keys()) if hasattr(reg, 'keys') else 'flat-keys'}")

    print("Checking required sections...")
    missing_sections = [s for s in REQUIRED_SECTIONS if s not in reg]
    if missing_sections:
        print(f"HARD STOP: missing required sections: {missing_sections}", file=sys.stderr)
        sys.exit(1)
    print(f"  required_sections_present: True ({len(REQUIRED_SECTIONS)} sections)")

    print("Checking minimum content requirements...")
    content_ok, content_errors = _check_content(reg)
    if not content_ok:
        for e in content_errors:
            print(f"  FAIL: {e}", file=sys.stderr)
        print("HARD STOP: registry content check failed", file=sys.stderr)
        sys.exit(1)
    print("  content requirements: all satisfied")

    artifact = {
        "artifact_id": "P0-04-CMDB-LITE-REGISTRY-VALIDATION-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry_path": str(REGISTRY_PATH.relative_to(REPO_ROOT)),
        "registry_version": reg.get("registry_version", "unknown"),
        "yaml_loaded": yaml_loaded,
        "required_sections_checked": REQUIRED_SECTIONS,
        "required_sections_present": True,
        "content_errors": [],
        "phase_linkage": "Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation)",
        "authority_sources": [
            "P0-01-AUTHORITY-SURFACE-INVENTORY-1",
            "ADR-0001", "ADR-0002", "ADR-0003", "ADR-0004",
            "ADR-0005", "ADR-0006", "ADR-0007",
            "governance/canonical_roadmap.json",
            "governance/runtime_contract_version.json",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print("P0-04: all checks passed.")


if __name__ == "__main__":
    main()
