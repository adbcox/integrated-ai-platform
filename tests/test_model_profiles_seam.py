"""Seam tests for P1-01-MODEL-PROFILES-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

import run_model_profiles_check as chk

PROFILES_PATH = REPO_ROOT / "governance/model_profiles.v1.yaml"
SPEC_PATH = REPO_ROOT / "docs/specs/model_profiles.md"

_GROUNDING_INPUTS = [
    REPO_ROOT / "governance/cmdb_lite_registry.v1.yaml",
    REPO_ROOT / "governance/autonomy_scorecard.v1.yaml",
    REPO_ROOT / "governance/definition_of_done.v1.yaml",
    REPO_ROOT / "docs/specs/cmdb_lite_registry.md",
    REPO_ROOT / "artifacts/governance/core_adr_index.json",
]

_REQUIRED_SECTIONS = ["version", "default_backend", "profiles", "routing_notes", "exceptions"]
_REQUIRED_PROFILES = ["fast", "balanced", "hard", "long_context"]
_REQUIRED_PROFILE_FIELDS = [
    "profile_id", "backend", "model_name", "context_window",
    "timeout_seconds", "temperature_policy", "intended_task_class", "enabled",
]


def _load() -> dict:
    mp, _ = chk._load_yaml(PROFILES_PATH)
    return mp


def test_import_module():
    assert callable(chk._load_yaml)
    assert callable(chk._check_content)


def test_grounding_inputs_present():
    for p in _GROUNDING_INPUTS:
        assert p.exists(), f"grounding input missing: {p}"


def test_profiles_file_exists():
    assert PROFILES_PATH.exists()


def test_spec_file_exists():
    assert SPEC_PATH.exists()


def test_profiles_loads():
    mp = _load()
    assert isinstance(mp, dict)
    assert len(mp) > 0


def test_version_present():
    mp = _load()
    assert "version" in mp and mp["version"]


def test_required_sections_present():
    mp = _load()
    for s in _REQUIRED_SECTIONS:
        assert s in mp, f"missing section: {s}"


def test_default_backend_is_ollama():
    mp = _load()
    assert mp.get("default_backend") == "ollama"


def test_all_required_profiles_present():
    mp = _load()
    profiles = mp["profiles"]
    assert isinstance(profiles, dict)
    for p in _REQUIRED_PROFILES:
        assert p in profiles, f"profiles missing: {p}"


def test_each_profile_has_required_fields():
    mp = _load()
    for pid, entry in mp["profiles"].items():
        if not isinstance(entry, dict):
            continue
        for f in _REQUIRED_PROFILE_FIELDS:
            assert f in entry, f"profiles.{pid} missing field: {f}"


def test_profile_ids_match_keys():
    mp = _load()
    for pid, entry in mp["profiles"].items():
        if isinstance(entry, dict):
            assert entry.get("profile_id") == pid, f"profiles.{pid}.profile_id mismatch"


def test_all_profiles_use_ollama_backend():
    mp = _load()
    for pid, entry in mp["profiles"].items():
        if isinstance(entry, dict):
            assert entry.get("backend") == "ollama", f"profiles.{pid}.backend must be 'ollama'"


def test_all_profiles_have_positive_context_window():
    mp = _load()
    for pid, entry in mp["profiles"].items():
        if isinstance(entry, dict):
            cw = entry.get("context_window")
            assert isinstance(cw, int) and cw > 0, f"profiles.{pid}.context_window must be positive int"


def test_all_profiles_have_positive_timeout():
    mp = _load()
    for pid, entry in mp["profiles"].items():
        if isinstance(entry, dict):
            to = entry.get("timeout_seconds")
            assert isinstance(to, int) and to > 0, f"profiles.{pid}.timeout_seconds must be positive int"


def test_all_profiles_have_enabled_field():
    mp = _load()
    for pid, entry in mp["profiles"].items():
        if isinstance(entry, dict):
            assert "enabled" in entry, f"profiles.{pid} missing 'enabled'"
            assert isinstance(entry["enabled"], bool), f"profiles.{pid}.enabled must be bool"


def test_at_least_one_narrow_routine_profile():
    mp = _load()
    narrow = [
        pid for pid, entry in mp["profiles"].items()
        if isinstance(entry, dict)
        and any("narrow_routine" in tc or "guard_clause" in tc or "single_file" in tc
                for tc in (entry.get("intended_task_class") or []))
    ]
    assert len(narrow) >= 1, "no profile with narrow_routine/guard_clause task class found"


def test_at_least_one_harder_profile():
    mp = _load()
    harder = [
        pid for pid, entry in mp["profiles"].items()
        if isinstance(entry, dict)
        and any("complex" in tc or "large_context" in tc or "hard" in tc or "long" in tc
                for tc in (entry.get("intended_task_class") or []))
    ]
    assert len(harder) >= 1, "no profile with complex/large_context task class found"


def test_exceptions_has_claude_not_routine():
    mp = _load()
    exc = mp.get("exceptions", {})
    assert isinstance(exc, dict)
    assert "claude_is_not_a_routine_profile" in exc


def test_content_check_passes():
    mp = _load()
    ok, errors = chk._check_content(mp)
    assert ok, f"content check failed: {errors}"


def test_fast_profile_timeout_lte_balanced():
    mp = _load()
    fast_to = mp["profiles"]["fast"]["timeout_seconds"]
    balanced_to = mp["profiles"]["balanced"]["timeout_seconds"]
    assert fast_to <= balanced_to, "fast profile timeout should be <= balanced"


def test_long_context_has_largest_context_window():
    mp = _load()
    lc_cw = mp["profiles"]["long_context"]["context_window"]
    for pid in ["fast", "balanced", "hard"]:
        assert lc_cw >= mp["profiles"][pid]["context_window"], \
            f"long_context context_window should be >= {pid}"


def test_spec_has_required_sections():
    text = SPEC_PATH.read_text()
    for heading in (
        "## Purpose", "## Scope", "## Required Profiles",
        "## Profile Fields", "## Routing Rules",
        "## Exceptions", "## Package Class Gate",
        "## Relationship to ADRs and Governance",
    ):
        assert heading in text, f"spec missing section: {heading}"


def test_spec_covers_all_profiles():
    text = SPEC_PATH.read_text()
    for p in _REQUIRED_PROFILES:
        assert f"### `{p}`" in text, f"spec does not document profile: {p}"


def test_spec_references_profiles_yaml():
    text = SPEC_PATH.read_text()
    assert "model_profiles.v1.yaml" in text


def test_emit_artifact(tmp_path):
    mp = _load()
    ok, _ = chk._check_content(mp)
    artifact = {
        "artifact_id": "P1-01-MODEL-PROFILES-VALIDATION-1",
        "generated_at": "2026-04-21T00:00:00+00:00",
        "profiles_path": str(PROFILES_PATH.relative_to(REPO_ROOT)),
        "yaml_loaded": True,
        "required_profiles_checked": _REQUIRED_PROFILES,
        "required_profiles_present": ok,
        "required_fields_checked": _REQUIRED_PROFILE_FIELDS,
        "required_fields_present": True,
        "phase_linkage": "Phase 1",
        "authority_sources": ["ADR-0004"],
    }
    out = tmp_path / "model_profiles_validation.json"
    out.write_text(json.dumps(artifact, indent=2))
    loaded = json.loads(out.read_text())
    assert loaded["artifact_id"] == "P1-01-MODEL-PROFILES-VALIDATION-1"
    assert loaded["yaml_loaded"] is True
    assert loaded["required_profiles_present"] is True
    assert loaded["required_fields_present"] is True
    assert "phase_linkage" in loaded
    assert "authority_sources" in loaded


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_model_profiles_check.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    artifact = REPO_ROOT / "artifacts/governance/model_profiles_validation.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text())
    assert data["artifact_id"] == "P1-01-MODEL-PROFILES-VALIDATION-1"
    assert data["yaml_loaded"] is True
    assert data["required_profiles_present"] is True
    assert data["required_fields_present"] is True
