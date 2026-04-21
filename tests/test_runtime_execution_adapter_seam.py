"""Conformance tests for framework/runtime_execution_adapter.py (DEVLOOP-A1-RUNTIME-EXECUTION-ADAPTER-SEAM-1)."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.runtime_execution_adapter import (
    BoundedExecutionSummary,
    ExecutionStepResult,
    execute_typed_actions,
    extract_session_id,
    make_job_id,
    emit_runtime_validation_record,
)
from framework.tool_schema import RunCommandAction, RunTestsAction
from framework.typed_permission_gate import PermissionRule, ToolPermission, TypedPermissionGate


@dataclass
class _FakeResult:
    return_code: int
    stdout: str
    stderr: str


class FakeRunner:
    def __init__(self, return_code=0, stdout="ok", stderr=""):
        self._return_code = return_code
        self._stdout = stdout
        self._stderr = stderr

    def run_command(self, *, command, cwd, env=None):
        return _FakeResult(return_code=self._return_code, stdout=self._stdout, stderr=self._stderr)


@dataclass
class FakeSession:
    session_id: str


@dataclass
class FakeWorkspace:
    source_root: Path
    scratch_root: Path
    artifact_root: Path


def _make_workspace(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    return FakeWorkspace(source_root=src, scratch_root=scratch, artifact_root=artifacts)


def _allow_gate():
    return TypedPermissionGate(default_permission=ToolPermission.ALLOW)


def _deny_gate():
    return TypedPermissionGate(default_permission=ToolPermission.DENY)


# --- extract_session_id ---

def test_extract_session_id_from_object():
    session = FakeSession(session_id="sess-abc")
    assert extract_session_id(session) == "sess-abc"


def test_extract_session_id_from_mapping():
    assert extract_session_id({"session_id": "sess-xyz"}) == "sess-xyz"


def test_extract_session_id_missing_raises():
    with pytest.raises(ValueError):
        extract_session_id({"other_key": "value"})


def test_extract_session_id_missing_attr_raises():
    class NoSession:
        pass
    with pytest.raises(ValueError):
        extract_session_id(NoSession())


# --- make_job_id ---

def test_make_job_id_format():
    jid = make_job_id()
    assert jid.startswith("job-")
    assert len(jid) > 8


def test_make_job_id_unique():
    assert make_job_id() != make_job_id()


# --- workspace-like duck typing ---

def test_workspace_like_missing_attrs_raises(tmp_path):
    @dataclass
    class BadWorkspace:
        source_root: Path

    gate = _allow_gate()
    with pytest.raises((ValueError, AttributeError)):
        execute_typed_actions({"session_id": "s1"}, BadWorkspace(source_root=tmp_path), gate, [])


# --- execute_typed_actions ---

def test_empty_action_list_returns_zero_steps(tmp_path):
    ws = _make_workspace(tmp_path)
    result = execute_typed_actions(FakeSession(session_id="s1"), ws, _allow_gate(), [])
    assert isinstance(result, BoundedExecutionSummary)
    assert result.total_steps == 0
    assert result.outcome == "pass"


def test_single_run_command_records_one_step(tmp_path):
    ws = _make_workspace(tmp_path)
    action = RunCommandAction(command="echo hi")
    result = execute_typed_actions(
        FakeSession(session_id="s1"), ws, _allow_gate(), [action], runner=FakeRunner()
    )
    assert result.total_steps == 1
    assert result.succeeded == 1


def test_single_run_tests_records_one_step(tmp_path):
    ws = _make_workspace(tmp_path)
    action = RunTestsAction()
    result = execute_typed_actions(
        FakeSession(session_id="s1"), ws, _allow_gate(), [action], runner=FakeRunner(stdout="3 passed")
    )
    assert result.total_steps == 1


def test_deny_gated_action_records_failure(tmp_path):
    ws = _make_workspace(tmp_path)
    action = RunCommandAction(command="echo hi")
    result = execute_typed_actions(
        FakeSession(session_id="s1"), ws, _deny_gate(), [action], runner=FakeRunner()
    )
    assert result.total_steps == 1
    assert result.failed == 1
    assert result.outcome == "fail"


def test_summary_contains_session_id_and_job_id(tmp_path):
    ws = _make_workspace(tmp_path)
    result = execute_typed_actions({"session_id": "test-sess"}, ws, _allow_gate(), [])
    assert result.session_id == "test-sess"
    assert result.job_id.startswith("job-")


def test_summary_artifact_written_to_artifact_root(tmp_path):
    ws = _make_workspace(tmp_path)
    result = execute_typed_actions(FakeSession(session_id="s1"), ws, _allow_gate(), [])
    assert result.artifact_path is not None
    assert Path(result.artifact_path).exists()


def test_artifact_json_parseable(tmp_path):
    ws = _make_workspace(tmp_path)
    result = execute_typed_actions(FakeSession(session_id="s1"), ws, _allow_gate(), [])
    data = json.loads(Path(result.artifact_path).read_text())
    assert "session_id" in data
    assert "job_id" in data
    assert "total_steps" in data
    assert "outcome" in data


def test_unsupported_action_type_raises(tmp_path):
    ws = _make_workspace(tmp_path)
    with pytest.raises(TypeError):
        execute_typed_actions(FakeSession(session_id="s1"), ws, _allow_gate(), ["not_an_action"])


# --- validation writer adapter ---

def test_validation_writer_adapter_exercised(tmp_path):
    result = emit_runtime_validation_record(
        session_id="s1",
        job_id="j1",
        outcome="pass",
        steps=(),
        artifact_dir=tmp_path,
    )
    assert result is not None
    assert Path(result).exists()


def test_validation_writer_dry_run_returns_none(tmp_path):
    result = emit_runtime_validation_record(
        session_id="s1",
        job_id="j1",
        outcome="pass",
        steps=(),
        artifact_dir=tmp_path,
        dry_run=True,
    )
    assert result is None


# --- package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "ExecutionStepResult")
    assert hasattr(framework, "BoundedExecutionSummary")
    assert hasattr(framework, "execute_typed_actions")
    assert hasattr(framework, "extract_session_id")
    assert hasattr(framework, "make_job_id")
