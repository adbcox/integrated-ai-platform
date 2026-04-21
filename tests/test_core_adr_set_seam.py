"""Seam tests for P0-02-CORE-ADR-SET-1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))

import run_core_adr_index as idx

_EXPECTED_ADR_IDS = [
    "ADR-0001", "ADR-0002", "ADR-0003", "ADR-0004",
    "ADR-0005", "ADR-0006", "ADR-0007",
]

_ADR_PATHS = [
    REPO_ROOT / "docs/adr/ADR-0001-canonical-session-job-schema.md",
    REPO_ROOT / "docs/adr/ADR-0002-typed-tool-system.md",
    REPO_ROOT / "docs/adr/ADR-0003-workspace-contract.md",
    REPO_ROOT / "docs/adr/ADR-0004-inference-gateway.md",
    REPO_ROOT / "docs/adr/ADR-0005-permission-model.md",
    REPO_ROOT / "docs/adr/ADR-0006-artifact-bundle.md",
    REPO_ROOT / "docs/adr/ADR-0007-autonomy-scorecard.md",
]

_REQUIRED_INPUTS = [
    REPO_ROOT / "docs/authority_inputs/revised_target_architecture_handoff_v4.docx",
    REPO_ROOT / "docs/authority_inputs/revised_target_architecture_handoff_v7.docx",
    REPO_ROOT / "docs/authority_inputs/control_window_architecture_adoption_packet.md",
    REPO_ROOT / "artifacts/governance/phase_authority_inventory.json",
]


def test_import_module():
    assert callable(idx.build_index)


def test_required_inputs_present():
    for p in _REQUIRED_INPUTS:
        assert p.exists(), f"required input missing: {p}"


def test_all_adr_files_exist():
    for p in _ADR_PATHS:
        assert p.exists(), f"ADR file missing: {p}"


def test_adr_files_have_title():
    for p in _ADR_PATHS:
        text = p.read_text(encoding="utf-8")
        assert text.strip().startswith("# ADR-"), f"no title in {p.name}"


def test_adr_files_have_status():
    import re
    pattern = re.compile(r"\*\*Status\*\*:\s*\S+", re.IGNORECASE)
    for p in _ADR_PATHS:
        text = p.read_text(encoding="utf-8")
        assert pattern.search(text), f"no Status field in {p.name}"


def test_adr_files_have_context():
    for p in _ADR_PATHS:
        text = p.read_text(encoding="utf-8")
        assert "## Context" in text, f"no Context section in {p.name}"


def test_adr_files_have_decision():
    for p in _ADR_PATHS:
        text = p.read_text(encoding="utf-8")
        assert "## Decision" in text, f"no Decision section in {p.name}"


def test_adr_files_have_consequences():
    for p in _ADR_PATHS:
        text = p.read_text(encoding="utf-8")
        assert "## Consequences" in text, f"no Consequences section in {p.name}"


def test_adr_files_have_phase_linkage():
    for p in _ADR_PATHS:
        text = p.read_text(encoding="utf-8")
        assert "Phase linkage" in text, f"no Phase linkage in {p.name}"


def test_adr_files_have_authority_sources():
    for p in _ADR_PATHS:
        text = p.read_text(encoding="utf-8")
        assert "Authority sources" in text, f"no Authority sources in {p.name}"


def test_build_index_returns_dict():
    result = idx.build_index()
    assert isinstance(result, dict)


def test_index_required_keys():
    result = idx.build_index()
    for key in ("artifact_id", "generated_at", "adr_count", "adr_ids",
                "adr_titles", "adr_statuses", "phase_linkage", "authority_sources"):
        assert key in result, f"missing key: {key}"


def test_index_adr_count_is_7():
    result = idx.build_index()
    assert result["adr_count"] == 7


def test_index_contains_all_adr_ids():
    result = idx.build_index()
    for adr_id in _EXPECTED_ADR_IDS:
        assert adr_id in result["adr_ids"], f"missing adr_id: {adr_id}"


def test_index_statuses_are_accepted():
    result = idx.build_index()
    for adr_id, status in result["adr_statuses"].items():
        assert status == "accepted", f"{adr_id} status is '{status}', expected 'accepted'"


def test_emit_artifact(tmp_path):
    index = idx.build_index()
    out = tmp_path / "core_adr_index.json"
    out.write_text(json.dumps(index, indent=2), encoding="utf-8")
    loaded = json.loads(out.read_text())
    assert loaded["artifact_id"] == "P0-02-CORE-ADR-INDEX-1"
    assert loaded["adr_count"] == 7
    assert set(_EXPECTED_ADR_IDS).issubset(set(loaded["adr_ids"]))
    for adr_id in _EXPECTED_ADR_IDS:
        assert adr_id in loaded["adr_titles"]
        assert adr_id in loaded["adr_statuses"]
        assert adr_id in loaded["phase_linkage"]
        assert adr_id in loaded["authority_sources"]


def test_runner_script_executes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run_core_adr_index.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"runner failed:\n{result.stderr}"
    artifact = REPO_ROOT / "artifacts/governance/core_adr_index.json"
    assert artifact.exists()
    data = json.loads(artifact.read_text())
    assert data["artifact_id"] == "P0-02-CORE-ADR-INDEX-1"
    assert data["adr_count"] == 7
    assert set(_EXPECTED_ADR_IDS).issubset(set(data["adr_ids"]))
