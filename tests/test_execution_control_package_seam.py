"""Seam tests for P0-03-EXECUTION-CONTROL-PACKAGE-1."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

import run_execution_control_package_check as chk

SCHEMA_PATH = REPO_ROOT / "governance/execution_control_package.schema.json"
EXAMPLE_PATH = REPO_ROOT / "governance/execution_control_package.example.json"
SPEC_PATH = REPO_ROOT / "docs/specs/execution_control_package.md"

_REQUIRED_SCHEMA_FIELDS = [
    "package_id", "label", "objective", "allowed_files", "forbidden_files",
    "validation_order", "rollback_rule", "artifact_outputs", "escalation_rule",
    "acceptance_gates", "phase_linkage", "authority_sources", "schema_version",
]

_GROUNDING_INPUTS = [
    REPO_ROOT / "docs/adr/ADR-0001-canonical-session-job-schema.md",
    REPO_ROOT / "docs/adr/ADR-0002-typed-tool-system.md",
    REPO_ROOT / "docs/adr/ADR-0003-workspace-contract.md",
    REPO_ROOT / "docs/adr/ADR-0006-artifact-bundle.md",
    REPO_ROOT / "docs/adr/ADR-0007-autonomy-scorecard.md",
]


def test_import_module():
    assert callable(chk._validate_example_against_schema)


def test_grounding_inputs_present():
    for p in _GROUNDING_INPUTS:
        assert p.exists(), f"grounding input missing: {p}"


def test_schema_file_exists():
    assert SCHEMA_PATH.exists()


def test_example_file_exists():
    assert EXAMPLE_PATH.exists()


def test_spec_file_exists():
    assert SPEC_PATH.exists()


def test_schema_parses_as_json():
    data = json.loads(SCHEMA_PATH.read_text())
    assert isinstance(data, dict)


def test_schema_has_required_array():
    data = json.loads(SCHEMA_PATH.read_text())
    assert "required" in data
    assert isinstance(data["required"], list)


def test_schema_required_array_complete():
    data = json.loads(SCHEMA_PATH.read_text())
    declared = set(data["required"])
    for field in _REQUIRED_SCHEMA_FIELDS:
        assert field in declared, f"schema missing required field: {field}"


def test_schema_has_properties_for_all_required():
    data = json.loads(SCHEMA_PATH.read_text())
    props = set(data.get("properties", {}).keys())
    for field in _REQUIRED_SCHEMA_FIELDS:
        assert field in props, f"schema missing property definition: {field}"


def test_example_parses_as_json():
    data = json.loads(EXAMPLE_PATH.read_text())
    assert isinstance(data, dict)


def test_example_has_all_required_fields():
    data = json.loads(EXAMPLE_PATH.read_text())
    for field in _REQUIRED_SCHEMA_FIELDS:
        assert field in data, f"example missing field: {field}"


def test_example_label_is_valid_enum():
    data = json.loads(EXAMPLE_PATH.read_text())
    assert data["label"] in ("SUBSTRATE", "LOCAL-FIRST", "ESCALATION")


def test_example_package_id_matches_pattern():
    schema = json.loads(SCHEMA_PATH.read_text())
    data = json.loads(EXAMPLE_PATH.read_text())
    pattern = schema["properties"]["package_id"]["pattern"]
    assert re.match(pattern, data["package_id"]), f"package_id pattern mismatch: {data['package_id']}"


def test_example_validates_against_schema():
    schema = json.loads(SCHEMA_PATH.read_text())
    example = json.loads(EXAMPLE_PATH.read_text())
    valid, errors = chk._validate_example_against_schema(schema, example)
    assert valid, f"example validation errors: {errors}"


def test_example_rollback_rule_structure():
    data = json.loads(EXAMPLE_PATH.read_text())
    rr = data["rollback_rule"]
    assert isinstance(rr, dict)
    assert "remove_on_failure" in rr
    assert "preserve_always" in rr
    assert isinstance(rr["remove_on_failure"], list)
    assert len(rr["remove_on_failure"]) >= 1


def test_example_artifact_outputs_structure():
    data = json.loads(EXAMPLE_PATH.read_text())
    ao = data["artifact_outputs"]
    assert isinstance(ao, list) and len(ao) >= 1
    for item in ao:
        assert "path" in item
        assert "artifact_id" in item
        assert "required_fields" in item
        assert isinstance(item["required_fields"], list)


def test_example_validation_order_is_sequential():
    data = json.loads(EXAMPLE_PATH.read_text())
    steps = [s["step"] for s in data["validation_order"]]
    assert steps == sorted(steps)
    assert steps[0] == 1


def test_spec_has_required_sections():
    text = SPEC_PATH.read_text()
    for section in ("## Purpose", "## Structure", "## Package Lifecycle",
                    "## Scope Compliance Rule", "## Recovery Protocol",
                    "## Relationship to ADRs"):
        assert section in text, f"spec missing section: {section}"


def test_spec_references_schema():
    text = SPEC_PATH.read_text()
    assert "execution_control_package.schema.json" in text


def test_emit_artifact(tmp_path):
    schema = json.loads(SCHEMA_PATH.read_text())
    example = json.loads(EXAMPLE_PATH.read_text())
    valid, errors = chk._validate_example_against_schema(schema, example)
    fields_ok, _ = chk._check_required_fields_in_schema(schema)
    artifact = {
        "artifact_id": "P0-03-EXEC-CTRL-PKG-VALIDATION-1",
        "generated_at": "2026-04-21T00:00:00+00:00",
        "schema_path": str(SCHEMA_PATH.relative_to(REPO_ROOT)),
        "example_path": str(EXAMPLE_PATH.relative_to(REPO_ROOT)),
        "schema_loaded": True,
        "example_valid": valid,
        "required_fields_checked": _REQUIRED_SCHEMA_FIELDS,
        "required_fields_present": fields_ok,
        "phase_linkage": "Phase 0",
        "authority_sources": ["ADR-0001", "ADR-0003", "ADR-0006"],
    }
    out = tmp_path / "execution_control_package_validation.json"
    out.write_text(json.dumps(artifact, indent=2))
    loaded = json.loads(out.read_text())
    assert loaded["artifact_id"] == "P0-03-EXEC-CTRL-PKG-VALIDATION-1"
    assert loaded["schema_loaded"] is True
    assert loaded["example_valid"] is True
    assert loaded["required_fields_present"] is True
    assert "phase_linkage" in loaded
    assert "authority_sources" in loaded


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_execution_control_package_check.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    artifact = REPO_ROOT / "artifacts/governance/execution_control_package_validation.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text())
    assert data["artifact_id"] == "P0-03-EXEC-CTRL-PKG-VALIDATION-1"
    assert data["schema_loaded"] is True
    assert data["example_valid"] is True
    assert data["required_fields_present"] is True
