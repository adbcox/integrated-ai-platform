"""Tests for framework.aider_adapter_contract — Aider adapter contract seam."""
import pytest

from framework.aider_adapter_contract import (
    AiderAdapterPolicy,
    AiderAdapterConfig,
    AiderAdapterRequest,
    AiderAdapterArtifact,
    DEFAULT_AIDER_POLICY,
)


def test_import_ok():
    from framework.aider_adapter_contract import AiderAdapterPolicy, AiderAdapterConfig  # noqa: F401


def test_default_policy_ollama_first():
    assert DEFAULT_AIDER_POLICY.ollama_first is True


def test_default_policy_dry_run_default():
    assert DEFAULT_AIDER_POLICY.dry_run_default is True


def test_default_policy_frozen():
    with pytest.raises((AttributeError, TypeError)):
        DEFAULT_AIDER_POLICY.ollama_first = False  # type: ignore


def test_policy_fields():
    p = AiderAdapterPolicy(ollama_first=True, max_context_files=4)
    assert p.max_context_files == 4


def test_config_valid_ollama():
    cfg = AiderAdapterConfig(
        model="ollama/qwen2.5-coder:14b",
        target_files=["framework/foo.py"],
        message="add helper",
    )
    assert cfg.is_valid()
    assert cfg.validate() == []


def test_config_invalid_empty_model():
    cfg = AiderAdapterConfig(model="", target_files=["f.py"], message="x")
    errors = cfg.validate()
    assert any("model" in e for e in errors)


def test_config_invalid_bad_prefix():
    cfg = AiderAdapterConfig(model="unknown_provider/model", target_files=["f.py"], message="x")
    errors = cfg.validate()
    assert any("allowed prefix" in e for e in errors)


def test_config_invalid_empty_files():
    cfg = AiderAdapterConfig(model="ollama/qwen2.5", target_files=[], message="x")
    errors = cfg.validate()
    assert any("target_files" in e for e in errors)


def test_config_invalid_empty_message():
    cfg = AiderAdapterConfig(model="ollama/qwen2.5", target_files=["f.py"], message="  ")
    errors = cfg.validate()
    assert any("message" in e for e in errors)


def test_config_too_many_files():
    cfg = AiderAdapterConfig(
        model="ollama/qwen2.5",
        target_files=["a.py", "b.py", "c.py", "d.py", "e.py"],
        message="x",
    )
    errors = cfg.validate()
    assert any("max" in e for e in errors)


def test_request_fields():
    cfg = AiderAdapterConfig(model="ollama/qwen2.5", target_files=["f.py"], message="x")
    req = AiderAdapterRequest(config=cfg, session_id="s1")
    assert req.session_id == "s1"
    assert req.config is cfg


def test_artifact_to_dict_keys():
    art = AiderAdapterArtifact(
        success=True, exit_code=0, stdout="ok", stderr="",
        dry_run=True, model="ollama/q", target_files=["f.py"]
    )
    d = art.to_dict()
    for k in ("schema_version", "success", "exit_code", "dry_run", "model", "target_files"):
        assert k in d


def test_artifact_schema_version():
    art = AiderAdapterArtifact(
        success=False, exit_code=-1, stdout="", stderr="err",
        dry_run=True, model="ollama/q", target_files=[]
    )
    assert art.to_dict()["schema_version"] == 1


def test_init_ok_from_framework():
    from framework import AiderAdapterConfig  # noqa: F401
