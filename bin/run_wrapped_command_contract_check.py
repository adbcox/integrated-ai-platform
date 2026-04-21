#!/usr/bin/env python3
"""P1-05: Validate wrapped command contract YAML and emit validation artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CONTRACT_PATH = REPO_ROOT / "governance/wrapped_command_contract.v1.yaml"
ARTIFACT_PATH = REPO_ROOT / "artifacts/governance/wrapped_command_contract_validation.json"

GROUNDING_INPUTS = [
    REPO_ROOT / "governance/workspace_contract.v1.yaml",
    REPO_ROOT / "governance/inference_gateway_contract.v1.yaml",
    REPO_ROOT / "governance/definition_of_done.v1.yaml",
    REPO_ROOT / "docs/specs/workspace_contract.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

REQUIRED_SECTIONS = [
    "version",
    "command_boundary",
    "command_categories",
    "result_contract",
    "timeout_policy",
    "side_effect_metadata",
    "exceptions",
]

REQUIRED_COMMAND_BOUNDARY_KEYS = ["canonical_interface", "raw_shell_not_canonical", "approved_entrypoints"]
REQUIRED_COMMAND_CATEGORIES = ["build", "test", "lint", "diff", "inspect"]
REQUIRED_RESULT_FIELDS = ["status", "stdout", "stderr", "exit_code", "duration_ms"]
REQUIRED_TIMEOUT_KEYS = ["default_timeout_seconds", "category_overrides", "timeout_failure_handling"]
REQUIRED_SIDE_EFFECT_KEYS = ["files_touched", "write_scope", "artifact_outputs", "repo_write_violation_signal"]


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

    cb = contract.get("command_boundary", {})
    _check_subsection("command_boundary", cb, REQUIRED_COMMAND_BOUNDARY_KEYS, errors)
    if isinstance(cb, dict):
        rnc = _bool_or_value(cb.get("raw_shell_not_canonical"))
        if rnc is not True:
            errors.append("command_boundary.raw_shell_not_canonical must be true")

    cc = contract.get("command_categories", {})
    if not isinstance(cc, dict):
        errors.append("command_categories must be a mapping")
    else:
        for cat in REQUIRED_COMMAND_CATEGORIES:
            if cat not in cc:
                errors.append(f"command_categories missing required category: {cat}")

    rc = contract.get("result_contract", {})
    if not isinstance(rc, dict):
        errors.append("result_contract must be a mapping")
    else:
        for f in REQUIRED_RESULT_FIELDS:
            if f not in rc:
                errors.append(f"result_contract missing required field: {f}")

    tp = contract.get("timeout_policy", {})
    _check_subsection("timeout_policy", tp, REQUIRED_TIMEOUT_KEYS, errors)
    if isinstance(tp, dict):
        dts_raw = tp.get("default_timeout_seconds")
        dts = dts_raw["value"] if isinstance(dts_raw, dict) else dts_raw
        if not isinstance(dts, (int, float)) or dts <= 0:
            errors.append("timeout_policy.default_timeout_seconds must be a positive number")

    se = contract.get("side_effect_metadata", {})
    _check_subsection("side_effect_metadata", se, REQUIRED_SIDE_EFFECT_KEYS, errors)

    exc = contract.get("exceptions", {})
    if not isinstance(exc, dict) or len(exc) == 0:
        errors.append("exceptions must be a non-empty mapping")

    return len(errors) == 0, errors


def main() -> None:
    print("P1-05: verifying grounding inputs...")
    if not _verify_grounding():
        print("HARD STOP: grounding inputs missing", file=sys.stderr)
        sys.exit(1)

    print("Loading wrapped command contract YAML...")
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

    print("Checking result, timeout, and side-effect fields...")
    ok, content_errors = _check_content(contract)
    if not ok:
        for e in content_errors:
            print(f"  FAIL: {e}", file=sys.stderr)
        print("HARD STOP: content check failed", file=sys.stderr)
        sys.exit(1)

    result_fields = REQUIRED_RESULT_FIELDS
    timeout_fields = REQUIRED_TIMEOUT_KEYS
    print(f"  result_fields_present: True ({len(result_fields)} fields)")
    print(f"  timeout_fields_present: True ({len(timeout_fields)} fields)")
    print(f"  side_effect_fields_present: True ({len(REQUIRED_SIDE_EFFECT_KEYS)} fields)")

    artifact = {
        "artifact_id": "P1-05-WRAPPED-COMMAND-CONTRACT-VALIDATION-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contract_path": str(CONTRACT_PATH.relative_to(REPO_ROOT)),
        "yaml_loaded": True,
        "required_sections_checked": REQUIRED_SECTIONS,
        "required_sections_present": True,
        "result_fields_checked": result_fields,
        "result_fields_present": True,
        "timeout_fields_checked": timeout_fields,
        "timeout_fields_present": True,
        "side_effect_fields_checked": REQUIRED_SIDE_EFFECT_KEYS,
        "side_effect_fields_present": True,
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
    print("P1-05: all checks passed.")


if __name__ == "__main__":
    main()
