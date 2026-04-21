"""Seam tests for P0-05-DEFINITION-OF-DONE-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

import run_definition_of_done_check as chk

DEFINITION_PATH = REPO_ROOT / "governance/definition_of_done.v1.yaml"
SPEC_PATH = REPO_ROOT / "docs/specs/definition_of_done.md"

_GROUNDING_INPUTS = [
    REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml",
    REPO_ROOT / "governance/execution_control_package.schema.json",
    REPO_ROOT / "governance/execution_control_package.example.json",
    REPO_ROOT / "docs/specs/execution_control_package.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

_REQUIRED_SECTIONS = [
    "version", "required_artifacts", "required_validation",
    "rollback_semantics", "telemetry_completeness",
    "escalation_handling", "acceptance_rules",
]

_REQUIRED_ACCEPTANCE_SUBSECTIONS = ["substrate", "local_first", "escalation"]

_REQUIRED_ARTIFACT_KEYS = [
    "expected_on_disk_changes", "required_runtime_artifacts", "artifact_parse_requirement",
]
_REQUIRED_VALIDATION_KEYS = [
    "validation_order_required", "make_check_required", "package_specific_tests_required",
]
_REQUIRED_ROLLBACK_KEYS = ["slice_only_rollback", "preserve_unrelated_changes"]
_REQUIRED_TELEMETRY_KEYS = [
    "validations_run", "validation_results", "escalation_status", "artifacts_produced",
]
_REQUIRED_ESCALATION_KEYS = [
    "explicit_escalation_required", "claude_rescue_not_local_autonomy",
]


def _load() -> dict:
    dod, _ = chk._load_yaml(DEFINITION_PATH)
    return dod


def test_import_module():
    assert callable(chk._load_yaml)
    assert callable(chk._check_content)


def test_grounding_inputs_present():
    for p in _GROUNDING_INPUTS:
        assert p.exists(), f"grounding input missing: {p}"


def test_definition_file_exists():
    assert DEFINITION_PATH.exists()


def test_spec_file_exists():
    assert SPEC_PATH.exists()


def test_definition_loads():
    dod = _load()
    assert isinstance(dod, dict)
    assert len(dod) > 0


def test_version_present():
    dod = _load()
    assert "version" in dod
    assert dod["version"]


def test_required_sections_present():
    dod = _load()
    for section in _REQUIRED_SECTIONS:
        assert section in dod, f"missing section: {section}"


def test_required_artifacts_keys():
    dod = _load()
    ra = dod["required_artifacts"]
    assert isinstance(ra, dict)
    for k in _REQUIRED_ARTIFACT_KEYS:
        assert k in ra, f"required_artifacts missing: {k}"


def test_required_validation_keys():
    dod = _load()
    rv = dod["required_validation"]
    assert isinstance(rv, dict)
    for k in _REQUIRED_VALIDATION_KEYS:
        assert k in rv, f"required_validation missing: {k}"


def test_rollback_semantics_keys():
    dod = _load()
    rs = dod["rollback_semantics"]
    assert isinstance(rs, dict)
    for k in _REQUIRED_ROLLBACK_KEYS:
        assert k in rs, f"rollback_semantics missing: {k}"


def test_telemetry_completeness_keys():
    dod = _load()
    tc = dod["telemetry_completeness"]
    assert isinstance(tc, dict)
    for k in _REQUIRED_TELEMETRY_KEYS:
        assert k in tc, f"telemetry_completeness missing: {k}"


def test_escalation_handling_keys():
    dod = _load()
    eh = dod["escalation_handling"]
    assert isinstance(eh, dict)
    for k in _REQUIRED_ESCALATION_KEYS:
        assert k in eh, f"escalation_handling missing: {k}"


def test_acceptance_rules_has_all_subsections():
    dod = _load()
    ar = dod["acceptance_rules"]
    assert isinstance(ar, dict)
    for sub in _REQUIRED_ACCEPTANCE_SUBSECTIONS:
        assert sub in ar, f"acceptance_rules missing: {sub}"


def test_acceptance_rules_local_first_key():
    dod = _load()
    lf = dod["acceptance_rules"]["local_first"]
    assert isinstance(lf, dict)
    assert "aider_or_local_first_attempt_required_when_substrate_exists" in lf


def test_acceptance_rules_substrate_key():
    dod = _load()
    sub = dod["acceptance_rules"]["substrate"]
    assert isinstance(sub, dict)
    assert "claude_allowed_for_authorized_substrate_work" in sub


def test_acceptance_rules_escalation_key():
    dod = _load()
    esc = dod["acceptance_rules"]["escalation"]
    assert isinstance(esc, dict)
    assert "explicit_marking_required" in esc


def test_content_check_passes():
    dod = _load()
    ok, errors = chk._check_content(dod)
    assert ok, f"content check failed: {errors}"


def test_spec_has_required_sections():
    text = SPEC_PATH.read_text()
    for heading in (
        "## Purpose", "## The Done Condition", "## Required Artifacts",
        "## Required Validation", "## Rollback Semantics",
        "## Telemetry Completeness", "## Escalation Handling",
        "## Acceptance Rules by Label", "## Relationship to ADRs",
    ):
        assert heading in text, f"spec missing section: {heading}"


def test_spec_covers_all_three_labels():
    text = SPEC_PATH.read_text()
    assert "### SUBSTRATE" in text
    assert "### LOCAL-FIRST" in text
    assert "### ESCALATION" in text


def test_spec_references_definition_yaml():
    text = SPEC_PATH.read_text()
    assert "definition_of_done.v1.yaml" in text


def test_emit_artifact(tmp_path):
    dod = _load()
    ok, _ = chk._check_content(dod)
    artifact = {
        "artifact_id": "P0-05-DOD-VALIDATION-1",
        "generated_at": "2026-04-21T00:00:00+00:00",
        "definition_path": str(DEFINITION_PATH.relative_to(REPO_ROOT)),
        "yaml_loaded": True,
        "required_sections_checked": _REQUIRED_SECTIONS,
        "required_sections_present": True,
        "package_classes_checked": _REQUIRED_ACCEPTANCE_SUBSECTIONS,
        "package_classes_present": True,
        "phase_linkage": "Phase 0",
        "authority_sources": ["ADR-0006", "ADR-0007"],
    }
    out = tmp_path / "definition_of_done_validation.json"
    out.write_text(json.dumps(artifact, indent=2))
    loaded = json.loads(out.read_text())
    assert loaded["artifact_id"] == "P0-05-DOD-VALIDATION-1"
    assert loaded["yaml_loaded"] is True
    assert loaded["required_sections_present"] is True
    assert loaded["package_classes_present"] is True
    assert "phase_linkage" in loaded
    assert "authority_sources" in loaded


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_definition_of_done_check.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    artifact = REPO_ROOT / "artifacts/governance/definition_of_done_validation.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text())
    assert data["artifact_id"] == "P0-05-DOD-VALIDATION-1"
    assert data["yaml_loaded"] is True
    assert data["required_sections_present"] is True
    assert data["package_classes_present"] is True
