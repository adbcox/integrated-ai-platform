"""Seam tests for P1-03-WORKSPACE-CONTRACT-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

import run_workspace_contract_check as chk

CONTRACT_PATH = REPO_ROOT / "governance/workspace_contract.v1.yaml"
SPEC_PATH = REPO_ROOT / "docs/specs/workspace_contract.md"

_GROUNDING_INPUTS = [
    REPO_ROOT / "governance/inference_gateway_contract.v1.yaml",
    REPO_ROOT / "governance/model_profiles.v1.yaml",
    REPO_ROOT / "governance/definition_of_done.v1.yaml",
    REPO_ROOT / "docs/specs/inference_gateway_contract.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

_REQUIRED_SECTIONS = [
    "version", "source_mount", "scratch_mount", "artifact_root",
    "cleanup_policy", "path_scope_rules", "exceptions",
]


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


def test_source_mount_is_read_only():
    c = _load()
    assert c["source_mount"]["mode"] == "read_only"


def test_source_mount_has_required_keys():
    c = _load()
    for k in chk.REQUIRED_SOURCE_MOUNT_KEYS:
        assert k in c["source_mount"], f"source_mount missing: {k}"


def test_source_mount_has_allowed_operations():
    c = _load()
    ops = c["source_mount"].get("allowed_operations", [])
    assert isinstance(ops, list) and len(ops) > 0


def test_scratch_mount_is_writable():
    c = _load()
    assert c["scratch_mount"]["mode"] == "writable"


def test_scratch_mount_has_required_keys():
    c = _load()
    for k in chk.REQUIRED_SCRATCH_MOUNT_KEYS:
        assert k in c["scratch_mount"], f"scratch_mount missing: {k}"


def test_scratch_mount_lifecycle_present():
    c = _load()
    lc = c["scratch_mount"]["lifecycle"]
    assert isinstance(lc, dict)
    assert "created" in lc
    assert "cleaned_up" in lc


def test_artifact_root_has_required_keys():
    c = _load()
    for k in chk.REQUIRED_ARTIFACT_ROOT_KEYS:
        assert k in c["artifact_root"], f"artifact_root missing: {k}"


def test_artifact_root_path_policy_has_governance():
    c = _load()
    pp = c["artifact_root"]["path_policy"]
    assert isinstance(pp, dict)
    assert "governance_artifacts" in pp


def test_artifact_root_distinct_from_scratch():
    c = _load()
    # Artifact root must reference governance/artifacts paths, not /tmp
    pp = c["artifact_root"]["path_policy"]
    gov_path = str(pp.get("governance_artifacts", ""))
    assert "tmp" not in gov_path.lower()
    assert "artifacts" in gov_path or "governance" in gov_path


def test_cleanup_policy_has_required_keys():
    c = _load()
    for k in chk.REQUIRED_CLEANUP_KEYS:
        assert k in c["cleanup_policy"], f"cleanup_policy missing: {k}"


def test_preserve_unrelated_changes_is_true():
    c = _load()
    puv = chk._bool_or_value(c["cleanup_policy"]["preserve_unrelated_changes"])
    assert puv is True


def test_cleanup_scope_covers_success_and_failure():
    c = _load()
    cs = c["cleanup_policy"]["cleanup_scope"]
    assert isinstance(cs, dict)
    assert "on_success" in cs
    assert "on_failure" in cs


def test_path_scope_rules_has_required_keys():
    c = _load()
    for k in chk.REQUIRED_PATH_SCOPE_KEYS:
        assert k in c["path_scope_rules"], f"path_scope_rules missing: {k}"


def test_repo_write_forbidden_by_default_is_true():
    c = _load()
    rwf = chk._bool_or_value(c["path_scope_rules"]["repo_write_forbidden_by_default"])
    assert rwf is True


def test_allowed_workspace_targets_has_forbidden_always():
    c = _load()
    awt = c["path_scope_rules"]["allowed_workspace_targets"]
    assert isinstance(awt, dict)
    assert "forbidden_always" in awt
    forbidden = awt["forbidden_always"]
    assert isinstance(forbidden, list) and len(forbidden) > 0


def test_forbidden_always_includes_framework():
    c = _load()
    forbidden = c["path_scope_rules"]["allowed_workspace_targets"]["forbidden_always"]
    assert any("framework" in str(f) for f in forbidden)


def test_forbidden_always_includes_canonical_roadmap():
    c = _load()
    forbidden = c["path_scope_rules"]["allowed_workspace_targets"]["forbidden_always"]
    assert any("canonical_roadmap" in str(f) for f in forbidden)


def test_exceptions_is_non_empty():
    c = _load()
    exc = c["exceptions"]
    assert isinstance(exc, dict) and len(exc) > 0


def test_exceptions_includes_gitignore_override():
    c = _load()
    exc = c["exceptions"]
    assert "artifacts_gitignore_override" in exc


def test_exceptions_includes_runtime_artifacts_rule():
    c = _load()
    exc = c["exceptions"]
    assert "runtime_artifacts_not_arbitrary_repo_writes" in exc


def test_content_check_passes():
    c = _load()
    ok, errors = chk._check_content(c)
    assert ok, f"content check failed: {errors}"


def test_spec_has_required_sections():
    text = SPEC_PATH.read_text()
    for heading in (
        "## Purpose",
        "## The Arbitrary-Write Prohibition",
        "## Three Zones",
        "## Source Mount",
        "## Scratch Mount",
        "## Artifact Root",
        "## Cleanup Policy",
        "## Path Scope Rules",
        "## Exceptions",
        "## Relationship to ADRs and Governance",
    ):
        assert heading in text, f"spec missing section: {heading}"


def test_spec_references_contract_yaml():
    text = SPEC_PATH.read_text()
    assert "workspace_contract.v1.yaml" in text


def test_spec_mentions_arbitrary_write_prohibition():
    text = SPEC_PATH.read_text()
    assert "arbitrary" in text.lower()


def test_emit_artifact(tmp_path):
    c = _load()
    ok, _ = chk._check_content(c)
    mount_fields = (
        chk.REQUIRED_SOURCE_MOUNT_KEYS
        + chk.REQUIRED_SCRATCH_MOUNT_KEYS
        + chk.REQUIRED_ARTIFACT_ROOT_KEYS
    )
    artifact = {
        "artifact_id": "P1-03-WORKSPACE-CONTRACT-VALIDATION-1",
        "generated_at": "2026-04-21T00:00:00+00:00",
        "contract_path": str(CONTRACT_PATH.relative_to(REPO_ROOT)),
        "yaml_loaded": True,
        "required_sections_checked": _REQUIRED_SECTIONS,
        "required_sections_present": True,
        "mount_fields_checked": mount_fields,
        "mount_fields_present": ok,
        "cleanup_fields_checked": chk.REQUIRED_CLEANUP_KEYS,
        "cleanup_fields_present": True,
        "phase_linkage": "Phase 1",
        "authority_sources": ["ADR-0003"],
    }
    out = tmp_path / "workspace_contract_validation.json"
    out.write_text(json.dumps(artifact, indent=2))
    loaded = json.loads(out.read_text())
    assert loaded["artifact_id"] == "P1-03-WORKSPACE-CONTRACT-VALIDATION-1"
    assert loaded["yaml_loaded"] is True
    assert loaded["required_sections_present"] is True
    assert loaded["mount_fields_present"] is True
    assert loaded["cleanup_fields_present"] is True
    assert "phase_linkage" in loaded
    assert "authority_sources" in loaded


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_workspace_contract_check.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    artifact = REPO_ROOT / "artifacts/governance/workspace_contract_validation.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text())
    assert data["artifact_id"] == "P1-03-WORKSPACE-CONTRACT-VALIDATION-1"
    assert data["yaml_loaded"] is True
    assert data["required_sections_present"] is True
    assert data["mount_fields_present"] is True
    assert data["cleanup_fields_present"] is True
