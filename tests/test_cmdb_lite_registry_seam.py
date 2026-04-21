"""Seam tests for P0-04-CMDB-LITE-REGISTRY-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

import run_cmdb_lite_registry_check as chk

REGISTRY_PATH = REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml"
SPEC_PATH = REPO_ROOT / "docs/specs/cmdb_lite_registry.md"

_GROUNDING_INPUTS = [
    REPO_ROOT / "artifacts/governance/phase_authority_inventory.json",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
    REPO_ROOT / "governance/execution_control_package.schema.json",
    REPO_ROOT / "governance/execution_control_package.example.json",
    REPO_ROOT / "docs/specs/execution_control_package.md",
]

_REQUIRED_SECTIONS = [
    "registry_version", "phase", "subsystems", "migration_map",
    "model_profiles", "runtime_contract", "artifact_policy",
    "adapter_status", "waivers", "autonomy_scorecard", "environments",
]

_REQUIRED_SUBSYSTEMS = [
    "control_plane", "inference_fabric", "agent_runtime",
    "retrieval_memory", "evaluation_governance",
]

_REQUIRED_MODEL_PROFILES = ["fast", "balanced", "hard"]

_REQUIRED_RUNTIME_CONTRACT_KEYS = [
    "session_job_schema", "tool_contract", "workspace_contract", "artifact_contract",
]

_REQUIRED_ADAPTER_KEYS = ["aider", "claude", "codex"]

_REQUIRED_AUTONOMY_KEYS = [
    "first_pass_success", "retry_count", "escalation_rate", "artifact_completeness",
]


def _load_registry() -> dict:
    reg, _ = chk._load_yaml(REGISTRY_PATH)
    return reg


def test_import_module():
    assert callable(chk._load_yaml)
    assert callable(chk._check_content)


def test_grounding_inputs_present():
    for p in _GROUNDING_INPUTS:
        assert p.exists(), f"grounding input missing: {p}"


def test_registry_file_exists():
    assert REGISTRY_PATH.exists()


def test_spec_file_exists():
    assert SPEC_PATH.exists()


def test_registry_loads():
    reg = _load_registry()
    assert isinstance(reg, dict)
    assert len(reg) > 0


def test_registry_has_version():
    reg = _load_registry()
    assert "registry_version" in reg
    assert reg["registry_version"]


def test_registry_required_sections_present():
    reg = _load_registry()
    for section in _REQUIRED_SECTIONS:
        assert section in reg, f"registry missing section: {section}"


def test_phase_has_current_and_status():
    reg = _load_registry()
    phase = reg["phase"]
    assert isinstance(phase, dict)
    assert "current" in phase, "phase missing 'current'"
    assert "status" in phase, "phase missing 'status'"


def test_phase_current_is_zero():
    reg = _load_registry()
    assert reg["phase"]["current"] == 0


def test_phase_status_is_open():
    reg = _load_registry()
    assert reg["phase"]["status"] == "open"


def test_subsystems_has_required_keys():
    reg = _load_registry()
    subs = reg["subsystems"]
    assert isinstance(subs, dict)
    for key in _REQUIRED_SUBSYSTEMS:
        assert key in subs, f"subsystems missing key: {key}"


def test_migration_map_has_min_entries():
    reg = _load_registry()
    mm = reg["migration_map"]
    assert isinstance(mm, list)
    assert len(mm) >= 5, f"migration_map has {len(mm)} entries, need >= 5"


def test_model_profiles_has_required_profiles():
    reg = _load_registry()
    mp = reg["model_profiles"]
    assert isinstance(mp, dict)
    for key in _REQUIRED_MODEL_PROFILES:
        assert key in mp, f"model_profiles missing: {key}"


def test_runtime_contract_has_required_keys():
    reg = _load_registry()
    rc = reg["runtime_contract"]
    assert isinstance(rc, dict)
    for key in _REQUIRED_RUNTIME_CONTRACT_KEYS:
        assert key in rc, f"runtime_contract missing: {key}"


def test_artifact_policy_has_root_and_retention():
    reg = _load_registry()
    ap = reg["artifact_policy"]
    assert isinstance(ap, dict)
    assert "artifact_root" in ap
    assert "retention_policy" in ap


def test_adapter_status_has_required_adapters():
    reg = _load_registry()
    ads = reg["adapter_status"]
    assert isinstance(ads, dict)
    for key in _REQUIRED_ADAPTER_KEYS:
        assert key in ads, f"adapter_status missing: {key}"


def test_autonomy_scorecard_has_required_keys():
    reg = _load_registry()
    asc = reg["autonomy_scorecard"]
    assert isinstance(asc, dict)
    for key in _REQUIRED_AUTONOMY_KEYS:
        assert key in asc, f"autonomy_scorecard missing: {key}"


def test_environments_section_exists():
    reg = _load_registry()
    assert "environments" in reg


def test_waivers_is_list():
    reg = _load_registry()
    assert isinstance(reg["waivers"], list)


def test_content_check_passes():
    reg = _load_registry()
    ok, errors = chk._check_content(reg)
    assert ok, f"content check failed: {errors}"


def test_spec_has_required_sections():
    text = SPEC_PATH.read_text()
    for heading in (
        "## Purpose", "## Registry File", "## Required Top-Level Sections",
        "## Required Subsystem Keys", "## Required Model Profiles",
        "## Required Runtime Contract Components",
        "## Required Autonomy Scorecard Fields",
        "## Versioning", "## Relationship to Governance Artifacts",
        "## Relationship to ADRs",
    ):
        assert heading in text, f"spec missing section: {heading}"


def test_spec_references_registry_file():
    text = SPEC_PATH.read_text()
    assert "cmdb_lite_registry.v1.yaml" in text


def test_emit_artifact(tmp_path):
    reg = _load_registry()
    ok, errors = chk._check_content(reg)
    artifact = {
        "artifact_id": "P0-04-CMDB-LITE-REGISTRY-VALIDATION-1",
        "generated_at": "2026-04-21T00:00:00+00:00",
        "registry_path": str(REGISTRY_PATH.relative_to(REPO_ROOT)),
        "registry_version": reg.get("registry_version", "unknown"),
        "yaml_loaded": True,
        "required_sections_checked": _REQUIRED_SECTIONS,
        "required_sections_present": True,
        "phase_linkage": "Phase 0",
        "authority_sources": ["ADR-0001", "ADR-0007"],
    }
    out = tmp_path / "cmdb_lite_registry_validation.json"
    out.write_text(json.dumps(artifact, indent=2))
    loaded = json.loads(out.read_text())
    assert loaded["artifact_id"] == "P0-04-CMDB-LITE-REGISTRY-VALIDATION-1"
    assert loaded["yaml_loaded"] is True
    assert loaded["required_sections_present"] is True
    assert "phase_linkage" in loaded
    assert "authority_sources" in loaded


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_cmdb_lite_registry_check.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    artifact = REPO_ROOT / "artifacts/governance/cmdb_lite_registry_validation.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text())
    assert data["artifact_id"] == "P0-04-CMDB-LITE-REGISTRY-VALIDATION-1"
    assert data["yaml_loaded"] is True
    assert data["required_sections_present"] is True
