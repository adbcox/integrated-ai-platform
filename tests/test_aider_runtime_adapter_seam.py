"""Tests for framework.aider_runtime_adapter — offline-safe seam tests."""
import pytest

from framework.aider_adapter_contract import (
    AiderAdapterConfig,
    AiderAdapterRequest,
    AiderAdapterArtifact,
    DEFAULT_AIDER_POLICY,
)
from framework.aider_runtime_adapter import AiderRuntimeAdapter, _EXPERIMENTAL_FLAG


def _make_request(model="ollama/qwen2.5-coder:14b", files=None, message="add helper", session="s1"):
    cfg = AiderAdapterConfig(model=model, target_files=files or ["framework/foo.py"], message=message)
    return AiderAdapterRequest(config=cfg, session_id=session)


def test_experimental_flag_present():
    assert _EXPERIMENTAL_FLAG is True


def test_import_ok():
    from framework.aider_runtime_adapter import AiderRuntimeAdapter  # noqa: F401


def test_dry_run_returns_artifact():
    adapter = AiderRuntimeAdapter()
    req = _make_request()
    result = adapter.run(req, dry_run=True)
    assert isinstance(result, AiderAdapterArtifact)


def test_dry_run_success_true():
    adapter = AiderRuntimeAdapter()
    req = _make_request()
    result = adapter.run(req, dry_run=True)
    assert result.success is True


def test_dry_run_exit_code_zero():
    adapter = AiderRuntimeAdapter()
    req = _make_request()
    result = adapter.run(req, dry_run=True)
    assert result.exit_code == 0


def test_dry_run_flag_set():
    adapter = AiderRuntimeAdapter()
    req = _make_request()
    result = adapter.run(req, dry_run=True)
    assert result.dry_run is True


def test_dry_run_stdout_contains_model():
    adapter = AiderRuntimeAdapter()
    req = _make_request(model="ollama/qwen2.5-coder:14b")
    result = adapter.run(req, dry_run=True)
    assert "qwen2.5" in result.stdout


def test_dry_run_target_files_preserved():
    adapter = AiderRuntimeAdapter()
    req = _make_request(files=["framework/bar.py", "framework/baz.py"])
    result = adapter.run(req, dry_run=True)
    assert result.target_files == ["framework/bar.py", "framework/baz.py"]


def test_invalid_config_returns_failure():
    adapter = AiderRuntimeAdapter()
    cfg = AiderAdapterConfig(model="", target_files=[], message="")
    req = AiderAdapterRequest(config=cfg)
    result = adapter.run(req, dry_run=True)
    assert result.success is False
    assert result.exit_code == -1


def test_invalid_config_stderr_contains_error():
    adapter = AiderRuntimeAdapter()
    cfg = AiderAdapterConfig(model="", target_files=[], message="")
    req = AiderAdapterRequest(config=cfg)
    result = adapter.run(req, dry_run=True)
    assert len(result.stderr) > 0


def test_policy_default_dry_run_respected():
    adapter = AiderRuntimeAdapter()
    req = _make_request()
    # Policy dry_run_default=True means no dry_run kwarg should still be dry
    result = adapter.run(req)
    assert result.dry_run is True


def test_session_id_propagated():
    adapter = AiderRuntimeAdapter()
    req = _make_request(session="test-session-42")
    result = adapter.run(req, dry_run=True)
    assert result.session_id == "test-session-42"


def test_artifact_to_dict_works():
    adapter = AiderRuntimeAdapter()
    req = _make_request()
    result = adapter.run(req, dry_run=True)
    d = result.to_dict()
    assert d["schema_version"] == 1
    assert d["dry_run"] is True


def test_preflight_returns_dict():
    adapter = AiderRuntimeAdapter()
    pf = adapter.preflight()
    assert isinstance(pf, dict)
    assert "verdict" in pf


def test_init_ok_from_framework():
    from framework import AiderRuntimeAdapter  # noqa: F401


def test_no_subprocess_in_dry_run(monkeypatch):
    import subprocess
    original_run = subprocess.run

    called = []

    def mock_run(*a, **kw):
        called.append(True)
        return original_run(*a, **kw)

    monkeypatch.setattr(subprocess, "run", mock_run)
    adapter = AiderRuntimeAdapter()
    req = _make_request()
    adapter.run(req, dry_run=True)
    assert len(called) == 0, "subprocess.run was called in dry_run mode"
