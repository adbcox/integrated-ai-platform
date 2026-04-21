#!/usr/bin/env python3
"""P0-03: Validate execution control package schema and example, emit validation artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_PATH = REPO_ROOT / "governance/execution_control_package.schema.json"
EXAMPLE_PATH = REPO_ROOT / "governance/execution_control_package.example.json"
ARTIFACT_PATH = REPO_ROOT / "artifacts/governance/execution_control_package_validation.json"

GROUNDING_INPUTS = [
    REPO_ROOT / "docs/adr/ADR-0001-canonical-session-job-schema.md",
    REPO_ROOT / "docs/adr/ADR-0002-typed-tool-system.md",
    REPO_ROOT / "docs/adr/ADR-0003-workspace-contract.md",
    REPO_ROOT / "docs/adr/ADR-0006-artifact-bundle.md",
    REPO_ROOT / "docs/adr/ADR-0007-autonomy-scorecard.md",
]

REQUIRED_SCHEMA_FIELDS = [
    "package_id", "label", "objective", "allowed_files", "forbidden_files",
    "validation_order", "rollback_rule", "artifact_outputs", "escalation_rule",
    "acceptance_gates", "phase_linkage", "authority_sources", "schema_version",
]


def _verify_grounding() -> bool:
    all_ok = True
    for p in GROUNDING_INPUTS:
        ok = p.exists() and len(p.read_text(encoding="utf-8")) > 100
        status = "OK" if ok else "FAIL"
        print(f"  grounding [{status}]: {p.relative_to(REPO_ROOT)}")
        if not ok:
            all_ok = False
    return all_ok


def _load_schema() -> tuple[dict | None, str | None]:
    try:
        data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        return data, None
    except Exception as exc:
        return None, str(exc)


def _validate_example_against_schema(schema: dict, example: dict) -> tuple[bool, list[str]]:
    """Structural validation: check required fields and enum constraints without jsonschema lib."""
    errors = []
    required = schema.get("required", [])
    for field in required:
        if field not in example:
            errors.append(f"missing required field: {field}")

    # Validate label enum
    label_enum = schema["properties"]["label"]["enum"]
    if example.get("label") not in label_enum:
        errors.append(f"label '{example.get('label')}' not in {label_enum}")

    # Validate package_id pattern (basic check)
    import re
    pid_pattern = schema["properties"]["package_id"]["pattern"]
    if not re.match(pid_pattern, str(example.get("package_id", ""))):
        errors.append(f"package_id '{example.get('package_id')}' does not match pattern {pid_pattern}")

    # Validate schema_version
    sv = example.get("schema_version")
    if not isinstance(sv, int) or sv < 1:
        errors.append(f"schema_version must be integer >= 1, got {sv!r}")

    # Validate structural sub-objects
    for field in ("rollback_rule",):
        sub = example.get(field)
        if not isinstance(sub, dict):
            errors.append(f"{field} must be an object")
        else:
            for sub_req in schema["properties"][field].get("required", []):
                if sub_req not in sub:
                    errors.append(f"{field}.{sub_req} missing")

    for field in ("allowed_files", "forbidden_files", "acceptance_gates", "authority_sources"):
        val = example.get(field)
        if not isinstance(val, list) or len(val) == 0:
            errors.append(f"{field} must be a non-empty array")

    for field in ("validation_order", "artifact_outputs"):
        val = example.get(field)
        if not isinstance(val, list) or len(val) == 0:
            errors.append(f"{field} must be a non-empty array")
        else:
            item_reqs = schema["properties"][field]["items"].get("required", [])
            for i, item in enumerate(val):
                for r in item_reqs:
                    if r not in item:
                        errors.append(f"{field}[{i}] missing required field '{r}'")

    return len(errors) == 0, errors


def _check_required_fields_in_schema(schema: dict) -> tuple[bool, list[str]]:
    """Verify all REQUIRED_SCHEMA_FIELDS appear in the schema's required array."""
    declared = set(schema.get("required", []))
    missing = [f for f in REQUIRED_SCHEMA_FIELDS if f not in declared]
    return len(missing) == 0, missing


def main() -> None:
    print("P0-03: verifying grounding inputs...")
    if not _verify_grounding():
        print("HARD STOP: grounding inputs missing or unreadable", file=sys.stderr)
        sys.exit(1)

    print("Loading schema...")
    schema, schema_err = _load_schema()
    schema_loaded = schema is not None
    if not schema_loaded:
        print(f"HARD STOP: schema load failed: {schema_err}", file=sys.stderr)
        sys.exit(1)
    print(f"  schema loaded: {SCHEMA_PATH.relative_to(REPO_ROOT)}")

    print("Loading example...")
    try:
        example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"HARD STOP: example load failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"  example loaded: {EXAMPLE_PATH.relative_to(REPO_ROOT)}")

    print("Validating example against schema...")
    example_valid, validation_errors = _validate_example_against_schema(schema, example)
    if not example_valid:
        for err in validation_errors:
            print(f"  FAIL: {err}", file=sys.stderr)
        print("HARD STOP: example failed schema validation", file=sys.stderr)
        sys.exit(1)
    print("  example valid: True")

    print("Checking required fields coverage in schema...")
    fields_ok, missing_fields = _check_required_fields_in_schema(schema)
    if not fields_ok:
        print(f"HARD STOP: schema missing required fields: {missing_fields}", file=sys.stderr)
        sys.exit(1)
    print(f"  required_fields_present: True ({len(REQUIRED_SCHEMA_FIELDS)} fields checked)")

    artifact = {
        "artifact_id": "P0-03-EXEC-CTRL-PKG-VALIDATION-1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_path": str(SCHEMA_PATH.relative_to(REPO_ROOT)),
        "example_path": str(EXAMPLE_PATH.relative_to(REPO_ROOT)),
        "schema_loaded": True,
        "example_valid": True,
        "required_fields_checked": REQUIRED_SCHEMA_FIELDS,
        "required_fields_present": True,
        "validation_errors": [],
        "phase_linkage": "Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation)",
        "authority_sources": [
            "P0-01-AUTHORITY-SURFACE-INVENTORY-1",
            "ADR-0001-canonical-session-job-schema",
            "ADR-0003-workspace-contract",
            "ADR-0006-artifact-bundle",
            "ADR-0007-autonomy-scorecard",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")
    print("P0-03: all checks passed.")


if __name__ == "__main__":
    main()
