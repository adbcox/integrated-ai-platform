"""Tests for framework.codex_adapter_contract — Codex adapter contract seam."""
import pytest

from framework.codex_adapter_contract import (
    CodexAdapterPolicy,
    CodexAdapterConfig,
    CodexAdapterRequest,
    CodexAdapterArtifact,
    CODEX_DEFER_REASON,
    DEFAULT_CODEX_POLICY,
)


def test_import_ok():
    from framework.codex_adapter_contract import CodexAdapterPolicy, CodexAdapterConfig  # noqa: F401


def test_default_policy_optional():
    assert DEFAULT_CODEX_POLICY.optional is True


def test_default_policy_dry_run_default():
    assert DEFAULT_CODEX_POLICY.dry_run_default is True


def test_default_policy_require_authorization():
    assert DEFAULT_CODEX_POLICY.require_explicit_authorization is True


def test_default_policy_frozen():
    with pytest.raises((AttributeError, TypeError)):
        DEFAULT_CODEX_POLICY.optional = False  # type: ignore


def test_defer_reason_non_empty():
    assert len(CODEX_DEFER_REASON) > 0


def test_is_defer_candidate_no_env(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cfg = CodexAdapterConfig(model="claude-3-5-sonnet", target_files=["f.py"], message="x")
    assert cfg.is_defer_candidate() is True


def test_config_valid_claude():
    cfg = CodexAdapterConfig(model="claude-3-5-sonnet", target_files=["f.py"], message="add helper")
    errors = cfg.validate()
    assert len(errors) == 0


def test_config_invalid_empty_model():
    cfg = CodexAdapterConfig(model="", target_files=["f.py"], message="x")
    errors = cfg.validate()
    assert any("model" in e for e in errors)


def test_config_invalid_bad_model_prefix():
    cfg = CodexAdapterConfig(model="ollama/qwen", target_files=["f.py"], message="x")
    errors = cfg.validate()
    assert any("Codex prefix" in e for e in errors)


def test_config_invalid_empty_files():
    cfg = CodexAdapterConfig(model="claude-3-5-sonnet", target_files=[], message="x")
    errors = cfg.validate()
    assert any("target_files" in e for e in errors)


def test_config_invalid_empty_message():
    cfg = CodexAdapterConfig(model="claude-3-5-sonnet", target_files=["f.py"], message="  ")
    errors = cfg.validate()
    assert any("message" in e for e in errors)


def test_artifact_deferred_field():
    art = CodexAdapterArtifact(
        success=False, exit_code=-1, stdout="", stderr="",
        dry_run=True, deferred=True, model="claude-3-5-sonnet",
        target_files=["f.py"], defer_reason="no key"
    )
    assert art.deferred is True
    assert art.defer_reason == "no key"


def test_artifact_to_dict_keys():
    art = CodexAdapterArtifact(
        success=False, exit_code=-1, stdout="", stderr="",
        dry_run=True, deferred=True, model="claude-3-5-sonnet", target_files=[]
    )
    d = art.to_dict()
    for k in ("schema_version", "success", "deferred", "defer_reason", "dry_run", "model"):
        assert k in d


def test_init_ok_from_framework():
    from framework import CodexAdapterConfig  # noqa: F401
