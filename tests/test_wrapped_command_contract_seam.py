"""Seam tests for P1-05-WRAPPED-COMMAND-CONTRACT-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

import run_wrapped_command_contract_check as chk

CONTRACT_PATH = REPO_ROOT / "governance/wrapped_command_contract.v1.yaml"
SPEC_PATH = REPO_ROOT / "docs/specs/wrapped_command_contract.md"

_GROUNDING_INPUTS = [
    REPO_ROOT / "governance/workspace_contract.v1.yaml",
    REPO_ROOT / "governance/inference_gateway_contract.v1.yaml",
    REPO_ROOT / "governance/definition_of_done.v1.yaml",
    REPO_ROOT / "docs/specs/workspace_contract.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

_REQUIRED_SECTIONS = [
    "version", "command_boundary", "command_categories", "result_contract",
    "timeout_policy", "side_effect_metadata", "exceptions",
]

_REQUIRED_COMMAND_CATEGORIES = ["build", "test", "lint", "diff", "inspect"]

_REQUIRED_RESULT_FIELDS = ["status", "stdout", "stderr", "exit_code", "duration_ms"]


def _load() -> dict:
    c, _ = chk._load_yaml(CONTRACT_PATH)
    return c


def test_import_module():
    assert callable(chk._load_yaml)
    assert callable(chk._check_content)


def test_grounding_inputs_present():
    for p in _GROUNDING_INPUTS:
        assert p.exists(), f"grounding input missing: {p}"


def test_contract_file_exists():
    assert CONTRACT_PATH.exists()


def test_spec_file_exists():
    assert SPEC_PATH.exists()


def test_contract_loads():
    c = _load()
    assert isinstance(c, dict) and len(c) > 0


def test_version_present():
    c = _load()
    assert "version" in c and c["version"]


def test_required_sections_present():
    c = _load()
    for s in _REQUIRED_SECTIONS:
        assert s in c, f"missing section: {s}"


def test_command_boundary_has_required_keys():
    c = _load()
    for k in chk.REQUIRED_COMMAND_BOUNDARY_KEYS:
        assert k in c["command_boundary"], f"command_boundary missing: {k}"


def test_raw_shell_not_canonical_is_true():
    c = _load()
    rnc = chk._bool_or_value(c["command_boundary"]["raw_shell_not_canonical"])
    assert rnc is True


def test_canonical_interface_is_wrapper():
    c = _load()
    ci = c["command_boundary"]["canonical_interface"]
    assert isinstance(ci, str) and len(ci) > 0
    assert "wrapper" in ci.lower() or "runner" in ci.lower() or "framework" in ci.lower()


def test_approved_entrypoints_present():
    c = _load()
    ae = c["command_boundary"]["approved_entrypoints"]
    assert isinstance(ae, dict) and len(ae) > 0


def test_command_categories_has_required():
    c = _load()
    cc = c["command_categories"]
    for cat in chk.REQUIRED_COMMAND_CATEGORIES:
        assert cat in cc, f"command_categories missing: {cat}"


def test_each_category_has_write_scope():
    c = _load()
    cc = c["command_categories"]
    for cat in _REQUIRED_COMMAND_CATEGORIES:
        entry = cc[cat]
        assert isinstance(entry, dict), f"{cat} must be a mapping"
        assert "write_scope" in entry, f"{cat} missing write_scope"


def test_each_category_has_default_timeout():
    c = _load()
    cc = c["command_categories"]
    for cat in _REQUIRED_COMMAND_CATEGORIES:
        entry = cc[cat]
        assert "default_timeout_seconds" in entry, f"{cat} missing default_timeout_seconds"
        assert isinstance(entry["default_timeout_seconds"], (int, float))
        assert entry["default_timeout_seconds"] > 0


def test_lint_diff_inspect_are_read_only():
    c = _load()
    cc = c["command_categories"]
    for cat in ("lint", "diff", "inspect"):
        assert cc[cat]["write_scope"] == "read_only", f"{cat} should be read_only"


def test_result_contract_has_required_fields():
    c = _load()
    rc = c["result_contract"]
    for f in chk.REQUIRED_RESULT_FIELDS:
        assert f in rc, f"result_contract missing: {f}"


def test_result_status_has_allowed_values():
    c = _load()
    status = c["result_contract"]["status"]
    assert isinstance(status, dict)
    allowed = status.get("allowed_values", [])
    assert "success" in allowed
    assert "failure" in allowed
    assert "timeout" in allowed
    assert "error" in allowed


def test_result_exit_code_type_is_integer():
    c = _load()
    ec = c["result_contract"]["exit_code"]
    assert isinstance(ec, dict)
    assert ec.get("type") == "integer"


def test_result_duration_ms_type_is_integer():
    c = _load()
    dm = c["result_contract"]["duration_ms"]
    assert isinstance(dm, dict)
    assert dm.get("type") == "integer"


def test_timeout_policy_has_required_keys():
    c = _load()
    for k in chk.REQUIRED_TIMEOUT_KEYS:
        assert k in c["timeout_policy"], f"timeout_policy missing: {k}"


def test_default_timeout_is_positive():
    c = _load()
    dts = c["timeout_policy"]["default_timeout_seconds"]
    val = dts["value"] if isinstance(dts, dict) else dts
    assert isinstance(val, (int, float)) and val > 0


def test_category_overrides_covers_required_categories():
    c = _load()
    co = c["timeout_policy"]["category_overrides"]
    assert isinstance(co, dict)
    for cat in _REQUIRED_COMMAND_CATEGORIES:
        assert cat in co, f"category_overrides missing: {cat}"


def test_timeout_failure_handling_present():
    c = _load()
    tfh = c["timeout_policy"]["timeout_failure_handling"]
    assert isinstance(tfh, dict)
    assert "status_on_timeout" in tfh
    assert tfh["status_on_timeout"] == "timeout"


def test_side_effect_metadata_has_required_keys():
    c = _load()
    for k in chk.REQUIRED_SIDE_EFFECT_KEYS:
        assert k in c["side_effect_metadata"], f"side_effect_metadata missing: {k}"


def test_write_scope_has_allowed_values():
    c = _load()
    ws = c["side_effect_metadata"]["write_scope"]
    assert isinstance(ws, dict)
    allowed = ws.get("allowed_values", [])
    assert "read_only" in allowed
    assert "scratch_only" in allowed
    assert "artifact_root_only" in allowed


def test_repo_write_violation_signal_is_boolean():
    c = _load()
    rws = c["side_effect_metadata"]["repo_write_violation_signal"]
    assert isinstance(rws, dict)
    assert rws.get("type") == "boolean"


def test_exceptions_is_non_empty():
    c = _load()
    exc = c["exceptions"]
    assert isinstance(exc, dict) and len(exc) > 0


def test_exceptions_includes_seam_tests():
    c = _load()
    exc = c["exceptions"]
    assert "direct_shell_in_seam_tests" in exc


def test_exceptions_includes_runner_scripts():
    c = _load()
    exc = c["exceptions"]
    assert "runner_scripts_use_subprocess" in exc


def test_exceptions_includes_raw_shell_declaration():
    c = _load()
    exc = c["exceptions"]
    assert "raw_shell_exception_requires_declaration" in exc


def test_content_check_passes():
    c = _load()
    ok, errors = chk._check_content(c)
    assert ok, f"content check failed: {errors}"


def test_spec_has_required_sections():
    text = SPEC_PATH.read_text()
    for heading in (
        "## Purpose",
        "## The Raw-Shell Prohibition",
        "## Command Boundary",
        "## Command Categories",
        "## Result Contract",
        "## Timeout Policy",
        "## Side-Effect Metadata",
        "## Exceptions",
        "## Relationship to ADRs and Governance",
    ):
        assert heading in text, f"spec missing section: {heading}"


def test_spec_references_contract_yaml():
    text = SPEC_PATH.read_text()
    assert "wrapped_command_contract.v1.yaml" in text


def test_spec_mentions_raw_shell_prohibition():
    text = SPEC_PATH.read_text()
    assert "raw" in text.lower() or "direct" in text.lower()


def test_emit_artifact(tmp_path):
    c = _load()
    ok, _ = chk._check_content(c)
    all_fields = (
        chk.REQUIRED_RESULT_FIELDS
        + chk.REQUIRED_TIMEOUT_KEYS
        + chk.REQUIRED_SIDE_EFFECT_KEYS
    )
    artifact = {
        "artifact_id": "P1-05-WRAPPED-COMMAND-CONTRACT-VALIDATION-1",
        "generated_at": "2026-04-21T00:00:00+00:00",
        "contract_path": str(CONTRACT_PATH.relative_to(REPO_ROOT)),
        "yaml_loaded": True,
        "required_sections_checked": _REQUIRED_SECTIONS,
        "required_sections_present": True,
        "result_fields_checked": chk.REQUIRED_RESULT_FIELDS,
        "result_fields_present": ok,
        "timeout_fields_checked": chk.REQUIRED_TIMEOUT_KEYS,
        "timeout_fields_present": ok,
        "phase_linkage": "Phase 1",
        "authority_sources": ["ADR-0003"],
    }
    out = tmp_path / "wrapped_command_contract_validation.json"
    out.write_text(json.dumps(artifact, indent=2))
    loaded = json.loads(out.read_text())
    assert loaded["artifact_id"] == "P1-05-WRAPPED-COMMAND-CONTRACT-VALIDATION-1"
    assert loaded["yaml_loaded"] is True
    assert loaded["required_sections_present"] is True
    assert loaded["result_fields_present"] is True
    assert loaded["timeout_fields_present"] is True
    assert "phase_linkage" in loaded
    assert "authority_sources" in loaded


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_wrapped_command_contract_check.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    artifact = REPO_ROOT / "artifacts/governance/wrapped_command_contract_validation.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text())
    assert data["artifact_id"] == "P1-05-WRAPPED-COMMAND-CONTRACT-VALIDATION-1"
    assert data["yaml_loaded"] is True
    assert data["required_sections_present"] is True
    assert data["result_fields_present"] is True
    assert data["timeout_fields_present"] is True
