"""Conformance tests for framework/sandbox_tool_dispatch.py (RUNTIME-CONTRACT-A1-SANDBOX-SEAM-1)."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.sandbox_tool_dispatch import dispatch_run_command, dispatch_run_tests
from framework.tool_schema import RunCommandAction, RunCommandObservation, RunTestsAction, RunTestsObservation
from framework.workspace_scope import ToolPathScope


@dataclass
class _FakeResult:
    return_code: int
    stdout: str
    stderr: str


class FakeRunner:
    def __init__(self, return_code=0, stdout="", stderr=""):
        self._return_code = return_code
        self._stdout = stdout
        self._stderr = stderr
        self.last_command = None

    def run_command(self, *, command, cwd, env=None):
        self.last_command = command
        return _FakeResult(
            return_code=self._return_code,
            stdout=self._stdout,
            stderr=self._stderr,
        )


def _scope(tmp_path):
    scratch = tmp_path / "scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    return ToolPathScope(source_root=tmp_path / "src", writable_roots=(scratch,))


def test_returns_run_command_observation(tmp_path):
    action = RunCommandAction(command="echo hi")
    result = dispatch_run_command(action, _scope(tmp_path), runner=FakeRunner(stdout="hi"))
    assert isinstance(result, RunCommandObservation)


def test_propagates_exit_code(tmp_path):
    action = RunCommandAction(command="false")
    result = dispatch_run_command(action, _scope(tmp_path), runner=FakeRunner(return_code=1))
    assert result.exit_code == 1


def test_passes_command_through(tmp_path):
    fake = FakeRunner()
    action = RunCommandAction(command="ls -la")
    dispatch_run_command(action, _scope(tmp_path), runner=fake)
    assert fake.last_command == "ls -la"


def test_empty_command_returns_error_without_runner_call(tmp_path):
    fake = FakeRunner()
    action = RunCommandAction(command="   ")
    result = dispatch_run_command(action, _scope(tmp_path), runner=fake)
    assert result.exit_code == 1
    assert result.error is not None
    assert fake.last_command is None


def test_wrong_type_raises_type_error_for_run_command(tmp_path):
    with pytest.raises(TypeError):
        dispatch_run_command("not_an_action", _scope(tmp_path), runner=FakeRunner())


def test_returns_run_tests_observation(tmp_path):
    action = RunTestsAction()
    result = dispatch_run_tests(action, _scope(tmp_path), runner=FakeRunner(stdout="5 passed"))
    assert isinstance(result, RunTestsObservation)


def test_parses_passed_count(tmp_path):
    action = RunTestsAction()
    result = dispatch_run_tests(action, _scope(tmp_path), runner=FakeRunner(stdout="3 passed in 0.1s"))
    assert result.passed == 3


def test_parses_failed_count(tmp_path):
    action = RunTestsAction()
    result = dispatch_run_tests(action, _scope(tmp_path), runner=FakeRunner(stdout="2 failed, 1 passed in 0.5s"))
    assert result.failed == 2


def test_run_tests_observation_exposes_exit_code(tmp_path):
    action = RunTestsAction()
    result = dispatch_run_tests(action, _scope(tmp_path), runner=FakeRunner(return_code=2))
    assert result.exit_code == 2


def test_wrong_type_raises_for_tests_dispatch(tmp_path):
    with pytest.raises(TypeError):
        dispatch_run_tests("not_an_action", _scope(tmp_path), runner=FakeRunner())
