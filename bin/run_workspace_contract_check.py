#!/usr/bin/env python3
"""P1-03: Validate workspace contract YAML and emit validation artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CONTRACT_PATH = REPO_ROOT / "governance/workspace_contract.v1.yaml"
ARTIFACT_PATH = REPO_ROOT / "artifacts/governance/workspace_contract_validation.json"

GROUNDING_INPUTS = [
    REPO_ROOT / "governance/inference_gateway_contract.v1.yaml",
    REPO_ROOT / "governance/model_profiles.v1.yaml",
    REPO_ROOT / "governance/definition_of_done.v1.yaml",
    REPO_ROOT / "docs/specs/inference_gateway_contract.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

REQUIRED_SECTIONS = [
    "version",
    "source_mount",
    "scratch_mount",
    "artifact_root",
    "cleanup_policy",
    "path_scope_rules",
    "exceptions",
]

REQUIRED_SOURCE_MOUNT_KEYS = ["mode", "mutability", "allowed_operations"]
REQUIRED_SCRATCH_MOUNT_KEYS = ["mode", "mutability", "lifecycle"]
REQUIRED_ARTIFACT_ROOT_KEYS = ["path_policy", "write_rule", "retention_reference"]
REQUIRED_CLEANUP_KEYS = ["cleanup_required", "cleanup_scope", "preserve_unrelated_changes"]
REQUIRED_PATH_SCOPE_KEYS = [
    "repo_write_forbidden_by_default",
    "artifact_write_location",
    "allowed_workspace_targets",
]


def _load_yaml(path: Path):
    try:
        import yaml  # type: ignore
        return yaml.safe_load(path.read_text(encoding="utf-8")), None
    except ImportError:
        pass
    return _minimal_yaml_keys(path.read_text(encoding="utf-8")), None


def _minimal_yaml_keys(text: str) -> dict:
    import re
    keys: dict = {}
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:', line)
        if m:
            keys[m.group(1)] = True
    return keys


def _verify_grounding() -> bool:
    all_ok = True
    for p in GROUNDING_INPUTS:
        ok = p.exists() and p.stat().st_size > 50
        print(f"  grounding [{'OK' if ok else 'FAIL'}]: {p.relative_to(REPO_ROOT)}")
        if not ok:
            all_ok = False
    return all_ok


def _bool_or_value(obj) -> bool | None:
    """Extract boolean from a plain bool or a dict with a 'value' key."""
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, dict):
        return obj.get("value")
    return None


def _check_subsection(name: str, obj, keys: list[str], errors: list[str]) -> None:
    if not isinstance(obj, dict):
        errors.append(f"{name} must be a mapping")
        return
    for k in keys:
        if k not in obj:
            errors.append(f"{name} missing required key: {k}")


def _check_content(contract: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []

    sm = contract.get("source_mount", {})
    _check_subsection("source_mount", sm, REQUIRED_SOURCE_MOUNT_KEYS, errors)
    if isinstance(sm, dict) and sm.get("mode") != "read_only":
        errors.append(f"source_mount.mode must be 'read_only', got {sm.get('mode')!r}")

    scratch = contract.get("scratch_mount", {})
    _check_subsection("scratch_mount", scratch, REQUIRED_SCRATCH_MOUNT_KEYS, errors)
    if isinstance(scratch, dict) and scratch.get("mode") != "writable":
        errors.append(f"scratch_mount.mode must be 'writable', got {scratch.get('mode')!r}")

    ar = contract.get("artifact_root", {})
    _check_subsection("artifact_root", ar, REQUIRED_ARTIFACT_ROOT_KEYS, errors)

    cp = contract.get("cleanup_policy", {})
    _check_subsection("cleanup_policy", cp, REQUIRED_CLEANUP_KEYS, errors)
    if isinstance(cp, dict):
        puv = _bool_or_value(cp.get("preserve_unrelated_changes"))
        if puv is not True:
            errors.append("cleanup_policy.preserve_unrelated_changes must be true")

    psr = contract.get("path_scope_rules", {})
    _check_subsection("path_scope_rules", psr, REQUIRED_PATH_SCOPE_KEYS, errors)
    if isinstance(psr, dict):
        rwf = _bool_or_value(psr.get("repo_write_forbidden_by_default"))
        if rwf is not True:
            errors.append("path_scope_rules.repo_write_forbidden_by_default must be true")

    exc = contract.get("exceptions", {})
    if not isinstance(exc, dict) or len(exc) == 0:
        errors.append("exceptions must be a non-empty mapping with narrowly approved write paths")

    return len(errors) == 0, errors


def main() -> None:
    print("P1-03: verifying grounding inputs...")
    if not _verify_grounding():
        print("HARD STOP: grounding inputs missing", file=sys.stderr)
        sys.exit(1)

    print("Loading workspace contract YAML...")
    contract, err = _load_yaml(CONTRACT_PATH)
    if contract is None:
        print(f"HARD STOP: contract load failed: {err}", file=sys.stderr)
        sys.exit(1)
    print(f"  yaml loaded: {CONTRACT_PATH.relative_to(REPO_ROOT)}")

    print("Checking required sections...")
    missing = [s for s in REQUIRED_SECTIONS if s not in contract]
    if missing:
        print(f"HARD STOP: missing sections: {missing}", file=sys.stderr)
        sys.exit(1)
    print(f"  required_sections_present: True ({len(REQUIRED_SECTIONS)} sections)")

    print("Checking mount, path, and cleanup fields...")
    ok, content_errors = _check_content(contract)
    if not ok:
        for e in content_errors:
            print(f"  FAIL: {e}", file=sys.stderr)
        print("HARD STOP: content check failed", file=sys.stderr)
        sys.exit(1)

    mount_fields = REQUIRED_SOURCE_MOUNT_KEYS + REQUIRED_SCRATCH_MOUNT_KEYS + REQUIRED_ARTIFACT_ROOT_KEYS
    cleanup_fields = REQUIRED_CLEANUP_KEYS
    print(f"  mount_fields_present: True ({len(mount_fields)} fields)")
    print(f"  cleanup_fields_present: True ({len(cleanup_fields)} fields)")

    artifact = {
        "artifact_id": "P1-03-WORKSPACE-CONTRACT-VALIDATION-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contract_path": str(CONTRACT_PATH.relative_to(REPO_ROOT)),
        "yaml_loaded": True,
        "required_sections_checked": REQUIRED_SECTIONS,
        "required_sections_present": True,
        "mount_fields_checked": mount_fields,
        "mount_fields_present": True,
        "cleanup_fields_checked": cleanup_fields,
        "cleanup_fields_present": True,
        "content_errors": [],
        "phase_linkage": "Phase 1 (runtime_contract_foundation)",
        "authority_sources": [
            "ADR-0003",
            "ADR-0006",
            "governance/definition_of_done.v1.yaml",
            "governance/execution_control_package.schema.json",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print("P1-03: all checks passed.")


if __name__ == "__main__":
    main()
