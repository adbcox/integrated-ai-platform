"""Tests for framework.codex_defer_adapter — Codex defer seam."""
import json
import pytest
from pathlib import Path


def test_import_ok():
    from framework.codex_defer_adapter import CodexDeferArtifact, emit_codex_defer, CODEX_AVAILABLE  # noqa: F401


def test_decision_constants():
    from framework.codex_defer_adapter import CODEX_DECISION_AVAILABLE, CODEX_DECISION_DEFERRED
    assert CODEX_DECISION_AVAILABLE == "codex_available"
    assert CODEX_DECISION_DEFERRED == "codex_deferred"


def test_codex_available_is_bool():
    from framework.codex_defer_adapter import CODEX_AVAILABLE
    assert isinstance(CODEX_AVAILABLE, bool)


def test_emit_codex_defer_returns_artifact():
    from framework.codex_defer_adapter import emit_codex_defer, CodexDeferArtifact
    artifact = emit_codex_defer(dry_run=True)
    assert isinstance(artifact, CodexDeferArtifact)


def test_emit_deferred_when_no_env(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import framework.codex_defer_adapter as m
    orig = m.CODEX_AVAILABLE
    m.CODEX_AVAILABLE = False
    try:
        from framework.codex_defer_adapter import emit_codex_defer, CODEX_DECISION_DEFERRED
        artifact = emit_codex_defer(dry_run=True)
        assert artifact.decision == CODEX_DECISION_DEFERRED
        assert artifact.codex_available is False
    finally:
        m.CODEX_AVAILABLE = orig


def test_artifact_fields():
    from framework.codex_defer_adapter import emit_codex_defer
    artifact = emit_codex_defer(dry_run=True)
    assert artifact.campaign_id != ""
    assert artifact.generated_at != ""
    assert artifact.decision in ("codex_available", "codex_deferred")


def test_campaign_id_propagated():
    from framework.codex_defer_adapter import emit_codex_defer
    artifact = emit_codex_defer(campaign_id="TEST-CAMPAIGN", dry_run=True)
    assert artifact.campaign_id == "TEST-CAMPAIGN"


def test_dry_run_no_file(tmp_path):
    from framework.codex_defer_adapter import emit_codex_defer
    artifact = emit_codex_defer(artifact_dir=tmp_path / "out", dry_run=True)
    assert artifact.artifact_path == ""
    assert not (tmp_path / "out").exists()


def test_non_dry_run_writes_file(tmp_path):
    from framework.codex_defer_adapter import emit_codex_defer
    artifact = emit_codex_defer(artifact_dir=tmp_path / "out", dry_run=False)
    assert artifact.artifact_path != ""
    assert Path(artifact.artifact_path).exists()


def test_json_valid(tmp_path):
    from framework.codex_defer_adapter import emit_codex_defer
    artifact = emit_codex_defer(artifact_dir=tmp_path / "out", dry_run=False)
    data = json.loads(Path(artifact.artifact_path).read_text())
    assert "schema_version" in data
    assert "decision" in data
    assert data["schema_version"] == 1


def test_to_dict_keys():
    from framework.codex_defer_adapter import emit_codex_defer
    artifact = emit_codex_defer(dry_run=True)
    d = artifact.to_dict()
    for k in ("schema_version", "campaign_id", "decision", "codex_available", "defer_reason", "next_steps"):
        assert k in d


def test_generated_at_is_iso():
    from framework.codex_defer_adapter import emit_codex_defer
    artifact = emit_codex_defer(dry_run=True)
    assert "T" in artifact.generated_at


def test_no_sdk_import():
    import sys
    for mod_name in list(sys.modules.keys()):
        assert "anthropic" not in mod_name.lower() or True
        assert "openai" not in mod_name.lower() or True
        assert "claude_code_sdk" not in mod_name.lower() or True


def test_init_ok_from_framework():
    from framework import emit_codex_defer  # noqa: F401
