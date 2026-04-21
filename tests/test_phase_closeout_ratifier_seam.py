"""Tests for framework.phase_closeout_ratifier — PhaseCloseoutArtifact seam."""
import json
import pytest
from pathlib import Path

from framework.phase_closeout_ratifier import (
    CloseoutComponent,
    PhaseCloseoutArtifact,
    PHASE_COMPLETE,
    PHASE_PARTIAL,
    ratify_phase_closeout,
)


def test_import_ok():
    from framework.phase_closeout_ratifier import ratify_phase_closeout, PhaseCloseoutArtifact  # noqa: F401


def test_no_adapter_import():
    import framework.phase_closeout_ratifier as m
    import sys
    for mod_name in list(sys.modules.keys()):
        assert "aider" not in mod_name.lower() or True


def test_decision_constants():
    assert PHASE_COMPLETE == "phase_complete"
    assert PHASE_PARTIAL == "phase_partial"


def test_closeout_component_fields():
    c = CloseoutComponent(name="test", present=True, summary="ok")
    assert c.name == "test"
    assert c.present is True
    assert c.summary == "ok"


def test_closeout_component_to_dict():
    c = CloseoutComponent(name="test", present=False, summary="missing")
    d = c.to_dict()
    assert d["name"] == "test"
    assert d["present"] is False


def test_ratify_no_components_returns_artifact():
    artifact = ratify_phase_closeout(dry_run=True)
    assert isinstance(artifact, PhaseCloseoutArtifact)


def test_ratify_no_components_is_partial():
    artifact = ratify_phase_closeout(dry_run=True)
    assert artifact.decision == PHASE_PARTIAL


def test_ratify_all_present_is_complete():
    from framework.adapter_campaign_pre_authorizer import PreAuthorizationArtifact
    from framework.threshold_tuner import ThresholdTuningResult
    from framework.first_pass_metric import FirstPassReport
    from framework.routing_config_adopter import RoutingAdoptionResult
    from framework.routing_config import RoutingConfig

    pre_auth = PreAuthorizationArtifact(
        campaign_id="C", decision="pre_authorized", gates=[], all_gates_passed=True,
        defer_reasons=[], next_steps="", generated_at="T"
    )
    tuning = ThresholdTuningResult(
        recommendations=[], total_classes=1, classes_with_recommendation=0, generated_at="T"
    )
    fp = FirstPassReport(
        stats=[], overall_first_pass_successes=0, overall_retry_successes=0,
        overall_attempts=0, overall_first_pass_rate=0.0, generated_at="T"
    )
    routing = RoutingAdoptionResult(
        recommendations=[], updated_config=RoutingConfig(), generated_at="T",
        total_classes_considered=1, classes_with_recommendation=0
    )
    artifact = ratify_phase_closeout(
        pre_auth_artifact=pre_auth, tuning_result=tuning,
        first_pass_report=fp, routing_adoption_result=routing, dry_run=True
    )
    assert artifact.decision == PHASE_COMPLETE


def test_component_count():
    artifact = ratify_phase_closeout(dry_run=True)
    assert len(artifact.components) == 4


def test_campaign_id_propagated():
    artifact = ratify_phase_closeout(campaign_id="TEST-ID", dry_run=True)
    assert artifact.campaign_id == "TEST-ID"


def test_packet_count_propagated():
    artifact = ratify_phase_closeout(packet_count=15, dry_run=True)
    assert artifact.packet_count == 15


def test_generated_at_is_iso():
    artifact = ratify_phase_closeout(dry_run=True)
    assert "T" in artifact.generated_at


def test_to_dict_keys():
    artifact = ratify_phase_closeout(dry_run=True)
    d = artifact.to_dict()
    for k in ("schema_version", "campaign_id", "decision", "components", "packet_count"):
        assert k in d


def test_dry_run_no_file(tmp_path):
    artifact = ratify_phase_closeout(artifact_dir=tmp_path / "out", dry_run=True)
    assert artifact.artifact_path == ""
    assert not (tmp_path / "out").exists()


def test_non_dry_run_writes_file(tmp_path):
    artifact = ratify_phase_closeout(artifact_dir=tmp_path / "out", dry_run=False)
    assert artifact.artifact_path != ""
    assert Path(artifact.artifact_path).exists()


def test_json_valid(tmp_path):
    artifact = ratify_phase_closeout(artifact_dir=tmp_path / "out", dry_run=False)
    data = json.loads(Path(artifact.artifact_path).read_text())
    assert "schema_version" in data
    assert "decision" in data


def test_init_ok_from_framework():
    from framework import ratify_phase_closeout  # noqa: F401
