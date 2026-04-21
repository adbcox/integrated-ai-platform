"""Conformance tests for framework/gated_tool_dispatch.py (DEVLOOP-A1-PERMISSION-DISPATCH-SEAM-1)."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.gated_tool_dispatch import GatedDispatchError, gated_run_command, gated_run_tests
from framework.tool_schema import RunCommandAction, RunTestsAction
from framework.typed_permission_gate import PermissionRule, ToolPermission, TypedPermissionGate
from framework.workspace_scope import ToolPathScope


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
        self.called = False

    def run_command(self, *, command, cwd, env=None):
        self.called = True
        return _FakeResult(return_code=self._return_code, stdout=self._stdout, stderr=self._stderr)


def _scope(tmp_path):
    scratch = tmp_path / "scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    return ToolPathScope(source_root=tmp_path / "src", writable_roots=(scratch,))


def _allow_gate():
    return TypedPermissionGate(default_permission=ToolPermission.ALLOW)


def _deny_gate():
    return TypedPermissionGate(default_permission=ToolPermission.DENY)


def _ask_gate():
    return TypedPermissionGate(rules=[
        PermissionRule(tool_name="*", permission=ToolPermission.ASK),
    ])


# --- ALLOW passes through ---

def test_allow_run_command_returns_observation(tmp_path):
    action = RunCommandAction(command="echo hi")
    result = gated_run_command(action, _scope(tmp_path), _allow_gate(), runner=FakeRunner())
    from framework.tool_schema import RunCommandObservation
    assert isinstance(result, RunCommandObservation)


def test_allow_run_tests_returns_observation(tmp_path):
    action = RunTestsAction()
    result = gated_run_tests(action, _scope(tmp_path), _allow_gate(), runner=FakeRunner(stdout="1 passed"))
    from framework.tool_schema import RunTestsObservation
    assert isinstance(result, RunTestsObservation)


# --- DENY raises GatedDispatchError ---

def test_deny_run_command_raises(tmp_path):
    action = RunCommandAction(command="echo hi")
    with pytest.raises(GatedDispatchError) as exc_info:
        gated_run_command(action, _scope(tmp_path), _deny_gate(), runner=FakeRunner())
    assert exc_info.value.ask_required is False


def test_deny_run_tests_raises(tmp_path):
    action = RunTestsAction()
    with pytest.raises(GatedDispatchError) as exc_info:
        gated_run_tests(action, _scope(tmp_path), _deny_gate(), runner=FakeRunner())
    assert exc_info.value.ask_required is False


# --- ASK raises GatedDispatchError with ask_required=True ---

def test_ask_run_command_raises_with_ask_required(tmp_path):
    action = RunCommandAction(command="echo hi")
    with pytest.raises(GatedDispatchError) as exc_info:
        gated_run_command(action, _scope(tmp_path), _ask_gate(), runner=FakeRunner())
    assert exc_info.value.ask_required is True


def test_ask_run_tests_raises_with_ask_required(tmp_path):
    action = RunTestsAction()
    with pytest.raises(GatedDispatchError) as exc_info:
        gated_run_tests(action, _scope(tmp_path), _ask_gate(), runner=FakeRunner())
    assert exc_info.value.ask_required is True


# --- Gate fires before runner invocation ---

def test_deny_gate_fires_before_runner_run_command(tmp_path):
    fake = FakeRunner()
    action = RunCommandAction(command="echo hi")
    with pytest.raises(GatedDispatchError):
        gated_run_command(action, _scope(tmp_path), _deny_gate(), runner=fake)
    assert fake.called is False


def test_deny_gate_fires_before_runner_run_tests(tmp_path):
    fake = FakeRunner()
    action = RunTestsAction()
    with pytest.raises(GatedDispatchError):
        gated_run_tests(action, _scope(tmp_path), _deny_gate(), runner=fake)
    assert fake.called is False


# --- GatedDispatchError is a PermissionError ---

def test_gated_dispatch_error_is_permission_error():
    err = GatedDispatchError("blocked", ask_required=False)
    assert isinstance(err, PermissionError)


def test_gated_dispatch_error_ask_flag_preserved():
    err = GatedDispatchError("ask me", ask_required=True)
    assert err.ask_required is True


# --- Wildcard and command-pattern rules ---

def test_wildcard_allow_passes_run_command(tmp_path):
    gate = TypedPermissionGate(rules=[
        PermissionRule(tool_name="*", permission=ToolPermission.ALLOW),
    ])
    action = RunCommandAction(command="ls")
    result = gated_run_command(action, _scope(tmp_path), gate, runner=FakeRunner())
    assert result.exit_code == 0


def test_command_pattern_deny_blocks(tmp_path):
    gate = TypedPermissionGate(rules=[
        PermissionRule(tool_name="run_command", permission=ToolPermission.DENY, command_pattern=r"rm\s+-rf"),
        PermissionRule(tool_name="run_command", permission=ToolPermission.ALLOW),
    ])
    dangerous = RunCommandAction(command="rm -rf /tmp/x")
    safe = RunCommandAction(command="ls -la")
    with pytest.raises(GatedDispatchError):
        gated_run_command(dangerous, _scope(tmp_path), gate, runner=FakeRunner())
    result = gated_run_command(safe, _scope(tmp_path), gate, runner=FakeRunner())
    assert result.exit_code == 0


# --- Package surface export ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "GatedDispatchError")
    assert hasattr(framework, "gated_run_command")
    assert hasattr(framework, "gated_run_tests")
