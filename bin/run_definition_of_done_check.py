#!/usr/bin/env python3
"""P0-05: Validate Definition of Done YAML and emit validation artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFINITION_PATH = REPO_ROOT / "governance/definition_of_done.v1.yaml"
ARTIFACT_PATH = REPO_ROOT / "artifacts/governance/definition_of_done_validation.json"

GROUNDING_INPUTS = [
    REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml",
    REPO_ROOT / "governance/execution_control_package.schema.json",
    REPO_ROOT / "governance/execution_control_package.example.json",
    REPO_ROOT / "docs/specs/execution_control_package.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

REQUIRED_SECTIONS = [
    "version",
    "required_artifacts",
    "required_validation",
    "rollback_semantics",
    "telemetry_completeness",
    "escalation_handling",
    "acceptance_rules",
]

REQUIRED_ACCEPTANCE_SUBSECTIONS = ["substrate", "local_first", "escalation"]

# Minimum content keys per section
REQUIRED_ARTIFACT_KEYS = [
    "expected_on_disk_changes",
    "required_runtime_artifacts",
    "artifact_parse_requirement",
]
REQUIRED_VALIDATION_KEYS = [
    "validation_order_required",
    "make_check_required",
    "package_specific_tests_required",
]
REQUIRED_ROLLBACK_KEYS = ["slice_only_rollback", "preserve_unrelated_changes"]
REQUIRED_TELEMETRY_KEYS = [
    "validations_run",
    "validation_results",
    "escalation_status",
    "artifacts_produced",
]
REQUIRED_ESCALATION_KEYS = [
    "explicit_escalation_required",
    "claude_rescue_not_local_autonomy",
]
REQUIRED_LOCAL_FIRST_KEYS = ["aider_or_local_first_attempt_required_when_substrate_exists"]
REQUIRED_SUBSTRATE_KEYS = ["claude_allowed_for_authorized_substrate_work"]
REQUIRED_ESCALATION_RULE_KEYS = ["explicit_marking_required"]


def _load_yaml(path: Path):
    try:
        import yaml  # type: ignore
        return yaml.safe_load(path.read_text(encoding="utf-8")), None
    except ImportError:
        pass
    return _minimal_yaml_keys(path.read_text(encoding="utf-8")), None


def _minimal_yaml_keys(text: str) -> dict:
    import re
    keys = {}
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


def _check_content(dod: dict) -> tuple[bool, list[str]]:
    errors = []

    def _check_keys(section_name: str, obj, keys: list[str]) -> None:
        if not isinstance(obj, dict):
            errors.append(f"{section_name} must be a mapping")
            return
        for k in keys:
            if k not in obj:
                errors.append(f"{section_name} missing required key: {k}")

    _check_keys("required_artifacts", dod.get("required_artifacts"), REQUIRED_ARTIFACT_KEYS)
    _check_keys("required_validation", dod.get("required_validation"), REQUIRED_VALIDATION_KEYS)
    _check_keys("rollback_semantics", dod.get("rollback_semantics"), REQUIRED_ROLLBACK_KEYS)
    _check_keys("telemetry_completeness", dod.get("telemetry_completeness"), REQUIRED_TELEMETRY_KEYS)
    _check_keys("escalation_handling", dod.get("escalation_handling"), REQUIRED_ESCALATION_KEYS)

    ar = dod.get("acceptance_rules", {})
    if not isinstance(ar, dict):
        errors.append("acceptance_rules must be a mapping")
    else:
        for sub in REQUIRED_ACCEPTANCE_SUBSECTIONS:
            if sub not in ar:
                errors.append(f"acceptance_rules missing subsection: {sub}")
        _check_keys("acceptance_rules.local_first", ar.get("local_first"), REQUIRED_LOCAL_FIRST_KEYS)
        _check_keys("acceptance_rules.substrate", ar.get("substrate"), REQUIRED_SUBSTRATE_KEYS)
        _check_keys("acceptance_rules.escalation", ar.get("escalation"), REQUIRED_ESCALATION_RULE_KEYS)

    return len(errors) == 0, errors


def main() -> None:
    print("P0-05: verifying grounding inputs...")
    if not _verify_grounding():
        print("HARD STOP: grounding inputs missing", file=sys.stderr)
        sys.exit(1)

    print("Loading definition YAML...")
    dod, err = _load_yaml(DEFINITION_PATH)
    if dod is None:
        print(f"HARD STOP: definition load failed: {err}", file=sys.stderr)
        sys.exit(1)
    print(f"  yaml loaded: {DEFINITION_PATH.relative_to(REPO_ROOT)}")

    print("Checking required sections...")
    missing = [s for s in REQUIRED_SECTIONS if s not in dod]
    if missing:
        print(f"HARD STOP: missing sections: {missing}", file=sys.stderr)
        sys.exit(1)
    print(f"  required_sections_present: True ({len(REQUIRED_SECTIONS)} sections)")

    print("Checking package-class acceptance rules...")
    ar = dod.get("acceptance_rules", {})
    missing_classes = [c for c in REQUIRED_ACCEPTANCE_SUBSECTIONS if c not in (ar if isinstance(ar, dict) else {})]
    if missing_classes:
        print(f"HARD STOP: acceptance_rules missing: {missing_classes}", file=sys.stderr)
        sys.exit(1)
    print(f"  package_classes_present: True ({REQUIRED_ACCEPTANCE_SUBSECTIONS})")

    print("Checking minimum content requirements...")
    ok, content_errors = _check_content(dod)
    if not ok:
        for e in content_errors:
            print(f"  FAIL: {e}", file=sys.stderr)
        print("HARD STOP: content check failed", file=sys.stderr)
        sys.exit(1)
    print("  content requirements: all satisfied")

    artifact = {
        "artifact_id": "P0-05-DOD-VALIDATION-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "definition_path": str(DEFINITION_PATH.relative_to(REPO_ROOT)),
        "yaml_loaded": True,
        "required_sections_checked": REQUIRED_SECTIONS,
        "required_sections_present": True,
        "package_classes_checked": REQUIRED_ACCEPTANCE_SUBSECTIONS,
        "package_classes_present": True,
        "content_errors": [],
        "phase_linkage": "Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation)",
        "authority_sources": [
            "ADR-0001", "ADR-0003", "ADR-0004", "ADR-0005", "ADR-0006", "ADR-0007",
            "governance/execution_control_package.schema.json",
            "governance/cmdb_lite_registry.v1.yaml",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print("P0-05: all checks passed.")


if __name__ == "__main__":
    main()
