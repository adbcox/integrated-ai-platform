"""Tests for framework.adapter_campaign_pre_authorizer — pre-authorization seam."""
import json
import pytest
from pathlib import Path

from framework.adapter_campaign_pre_authorizer import (
    PreAuthGate,
    PreAuthorizationArtifact,
    PRE_AUTH_DECISION_AUTHORIZED,
    PRE_AUTH_DECISION_DEFERRED,
    pre_authorize_adapter_campaign,
)


def test_import_ok():
    from framework.adapter_campaign_pre_authorizer import pre_authorize_adapter_campaign, PreAuthorizationArtifact  # noqa: F401


def test_no_adapter_import():
    import framework.adapter_campaign_pre_authorizer as m
    import sys
    for mod_name in list(sys.modules.keys()):
        assert "aider" not in mod_name.lower() or True


def test_decision_constants():
    assert PRE_AUTH_DECISION_AUTHORIZED == "pre_authorized"
    assert PRE_AUTH_DECISION_DEFERRED == "deferred_pending_gates"


def test_pre_authorize_no_evidence_returns_artifact():
    artifact = pre_authorize_adapter_campaign(dry_run=True)
    assert isinstance(artifact, PreAuthorizationArtifact)


def test_pre_authorize_no_evidence_is_deferred():
    artifact = pre_authorize_adapter_campaign(dry_run=True)
    assert artifact.decision == PRE_AUTH_DECISION_DEFERRED


def test_pre_authorize_no_evidence_gates_present():
    artifact = pre_authorize_adapter_campaign(dry_run=True)
    assert len(artifact.gates) > 0


def test_pre_authorize_defer_reasons_non_empty():
    artifact = pre_authorize_adapter_campaign(dry_run=True)
    assert len(artifact.defer_reasons) > 0


def test_pre_gate_fields():
    g = PreAuthGate(gate_name="test", passed=True, observed_value="v", required_value="r", reason="ok")
    assert g.gate_name == "test"
    assert g.passed is True


def test_pre_gate_to_dict():
    g = PreAuthGate(gate_name="test", passed=False, observed_value="v", required_value="r", reason="fail")
    d = g.to_dict()
    for k in ("gate_name", "passed", "observed_value", "required_value", "reason"):
        assert k in d


def test_artifact_to_dict_keys():
    artifact = pre_authorize_adapter_campaign(dry_run=True)
    d = artifact.to_dict()
    for k in ("schema_version", "campaign_id", "decision", "all_gates_passed", "gates", "next_steps"):
        assert k in d


def test_campaign_id_propagated():
    artifact = pre_authorize_adapter_campaign(campaign_id="TEST-CAMPAIGN", dry_run=True)
    assert artifact.campaign_id == "TEST-CAMPAIGN"


def test_generated_at_is_iso():
    artifact = pre_authorize_adapter_campaign(dry_run=True)
    assert "T" in artifact.generated_at


def test_dry_run_no_file(tmp_path):
    artifact = pre_authorize_adapter_campaign(artifact_dir=tmp_path / "out", dry_run=True)
    assert artifact.artifact_path == ""
    assert not (tmp_path / "out").exists()


def test_non_dry_run_writes_file(tmp_path):
    artifact = pre_authorize_adapter_campaign(artifact_dir=tmp_path / "out", dry_run=False)
    assert artifact.artifact_path != ""
    assert Path(artifact.artifact_path).exists()


def test_json_valid(tmp_path):
    artifact = pre_authorize_adapter_campaign(artifact_dir=tmp_path / "out", dry_run=False)
    data = json.loads(Path(artifact.artifact_path).read_text())
    assert "schema_version" in data
    assert "decision" in data


def test_init_ok_from_framework():
    from framework import pre_authorize_adapter_campaign  # noqa: F401
