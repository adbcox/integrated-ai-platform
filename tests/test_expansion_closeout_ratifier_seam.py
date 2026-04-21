"""Tests for framework.expansion_closeout_ratifier — terminal LAEC1 evidence seam."""
import json
import pytest
from pathlib import Path

from framework.expansion_closeout_ratifier import (
    EXPANSION_COMPLETE,
    EXPANSION_PARTIAL,
    ExpansionCloseoutComponent,
    ExpansionCloseoutArtifact,
    ratify_expansion_closeout,
)


def test_import_ok():
    from framework.expansion_closeout_ratifier import ratify_expansion_closeout, ExpansionCloseoutArtifact  # noqa: F401


def test_constants():
    assert EXPANSION_COMPLETE == "expansion_complete"
    assert EXPANSION_PARTIAL == "expansion_partial"


def test_no_components_returns_artifact():
    artifact = ratify_expansion_closeout(dry_run=True)
    assert isinstance(artifact, ExpansionCloseoutArtifact)


def test_no_components_is_partial():
    artifact = ratify_expansion_closeout(dry_run=True)
    assert artifact.decision == EXPANSION_PARTIAL


def test_component_count_is_six():
    artifact = ratify_expansion_closeout(dry_run=True)
    assert len(artifact.components) == 6


def test_component_names():
    artifact = ratify_expansion_closeout(dry_run=True)
    names = {c.name for c in artifact.components}
    expected = {
        "aider_adapter_seam", "codex_defer_seam", "cmdb_authority_pilot",
        "cmdb_integration_gate", "first_wave_branches", "second_wave_branches"
    }
    assert names == expected


def test_all_present_is_complete():
    from framework.aider_runtime_adapter import AiderRuntimeAdapter
    from framework.codex_defer_adapter import CodexDeferArtifact, emit_codex_defer
    from framework.cmdb_authority_pilot import CmdbAuthorityPilot
    from framework.cmdb_integration_gate import evaluate_cmdb_gate
    from framework.domain_branch_first_wave import FIRST_WAVE_MANIFEST
    from framework.domain_branch_second_wave import SECOND_WAVE_MANIFEST

    artifact = ratify_expansion_closeout(
        aider_adapter_present=AiderRuntimeAdapter(),
        codex_defer_present=emit_codex_defer(dry_run=True),
        cmdb_authority_present=CmdbAuthorityPilot().read_authority(),
        cmdb_gate_present=evaluate_cmdb_gate(),
        first_wave_present=FIRST_WAVE_MANIFEST,
        second_wave_present=SECOND_WAVE_MANIFEST,
        dry_run=True,
    )
    assert artifact.decision == EXPANSION_COMPLETE
    assert artifact.all_components_present is True


def test_campaign_id_propagated():
    artifact = ratify_expansion_closeout(campaign_id="TEST-ID", dry_run=True)
    assert artifact.campaign_id == "TEST-ID"


def test_packet_count_propagated():
    artifact = ratify_expansion_closeout(packet_count=12, dry_run=True)
    assert artifact.packet_count == 12


def test_generated_at_is_iso():
    artifact = ratify_expansion_closeout(dry_run=True)
    assert "T" in artifact.generated_at


def test_to_dict_keys():
    artifact = ratify_expansion_closeout(dry_run=True)
    d = artifact.to_dict()
    for k in ("schema_version", "campaign_id", "decision", "components", "packet_count", "notes"):
        assert k in d


def test_dry_run_no_file(tmp_path):
    artifact = ratify_expansion_closeout(artifact_dir=tmp_path / "out", dry_run=True)
    assert artifact.artifact_path == ""
    assert not (tmp_path / "out").exists()


def test_non_dry_run_writes_file(tmp_path):
    artifact = ratify_expansion_closeout(artifact_dir=tmp_path / "out", dry_run=False)
    assert artifact.artifact_path != ""
    assert Path(artifact.artifact_path).exists()


def test_json_valid(tmp_path):
    artifact = ratify_expansion_closeout(artifact_dir=tmp_path / "out", dry_run=False)
    data = json.loads(Path(artifact.artifact_path).read_text())
    assert "schema_version" in data
    assert data["schema_version"] == 1


def test_init_ok_from_framework():
    from framework import ratify_expansion_closeout  # noqa: F401
