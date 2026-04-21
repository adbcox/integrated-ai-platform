"""Conformance tests for framework/file_local_devloop.py (DEVLOOP-A1-BOUNDED-CODING-LOOP-SEAM-1)."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.apply_patch_dispatch import dispatch_apply_patch
from framework.file_local_devloop import FileLocalDevloopRunner, FileLocalResult, FileLocalTask
from framework.tool_schema import ApplyPatchAction
from framework.typed_permission_gate import PermissionRule, ToolPermission, TypedPermissionGate
from framework.workspace_scope import ToolPathScope


@dataclass
class _FakeResult:
    return_code: int
    stdout: str
    stderr: str


class FakeRunner:
    def __init__(self, return_code=0, stdout="1 passed", stderr=""):
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
    src.mkdir(exist_ok=True)
    scratch = tmp_path / "scratch"
    scratch.mkdir(exist_ok=True)
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir(exist_ok=True)
    return FakeWorkspace(source_root=src, scratch_root=scratch, artifact_root=artifacts)


def _make_scope(tmp_path):
    ws = _make_workspace(tmp_path)
    scratch = tmp_path / "scratch"
    return ToolPathScope(source_root=ws.source_root, writable_roots=(scratch, ws.artifact_root))


def _allow_gate():
    return TypedPermissionGate(default_permission=ToolPermission.ALLOW)


def _deny_gate():
    return TypedPermissionGate(default_permission=ToolPermission.DENY)


def _writable_file(tmp_path, content="hello world"):
    scratch = tmp_path / "scratch"
    scratch.mkdir(exist_ok=True)
    f = scratch / "target.py"
    f.write_text(content, encoding="utf-8")
    return f


# --- apply_patch_dispatch tests ---

def test_patch_succeeds_on_writable_file(tmp_path):
    f = _writable_file(tmp_path)
    scope = _make_scope(tmp_path)
    action = ApplyPatchAction(path=str(f), old_string="hello", new_string="goodbye")
    obs = dispatch_apply_patch(action, scope)
    assert obs.applied is True
    assert f.read_text() == "goodbye world"


def test_patch_blocked_outside_writable_scope(tmp_path):
    src = tmp_path / "src" / "protected.py"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("sensitive", encoding="utf-8")
    scope = _make_scope(tmp_path)
    action = ApplyPatchAction(path=str(src), old_string="sensitive", new_string="changed")
    obs = dispatch_apply_patch(action, scope)
    assert obs.applied is False
    assert obs.error is not None


def test_patch_returns_clean_failure_if_old_string_not_found(tmp_path):
    f = _writable_file(tmp_path, "original content")
    scope = _make_scope(tmp_path)
    action = ApplyPatchAction(path=str(f), old_string="NOT_PRESENT", new_string="x")
    obs = dispatch_apply_patch(action, scope)
    assert obs.applied is False
    assert "not found" in (obs.error or "").lower()


def test_empty_old_string_rejected_safely(tmp_path):
    f = _writable_file(tmp_path)
    scope = _make_scope(tmp_path)
    action = ApplyPatchAction(path=str(f), old_string="", new_string="x")
    obs = dispatch_apply_patch(action, scope)
    assert obs.applied is False
    assert obs.error is not None


def test_no_subprocess_use_in_patch_dispatch(tmp_path):
    import subprocess as _sp
    original_run = _sp.run
    calls = []
    _sp.run = lambda *a, **kw: calls.append((a, kw))
    try:
        f = _writable_file(tmp_path)
        scope = _make_scope(tmp_path)
        action = ApplyPatchAction(path=str(f), old_string="hello", new_string="bye")
        dispatch_apply_patch(action, scope)
    finally:
        _sp.run = original_run
    assert len(calls) == 0, "dispatch_apply_patch must not use subprocess"


# --- file_local_devloop tests ---

def _make_runner(tmp_path, test_return_code=0):
    ws = _make_workspace(tmp_path)
    scope = _make_scope(tmp_path)
    return FileLocalDevloopRunner(
        FakeSession(session_id="test-session"),
        ws,
        _allow_gate(),
        scope,
        runner=FakeRunner(return_code=test_return_code, stdout="1 passed"),
    )


def test_file_local_devloop_runs_patch_then_tests(tmp_path):
    f = _writable_file(tmp_path)
    runner = _make_runner(tmp_path)
    task = FileLocalTask(
        session_id="s1",
        target_path=str(f),
        old_string="hello",
        new_string="goodbye",
    )
    result = runner.run_task(task)
    assert result.patch_applied is True
    assert isinstance(result, FileLocalResult)


def test_result_success_requires_patch_and_test_pass(tmp_path):
    f = _writable_file(tmp_path)
    runner = _make_runner(tmp_path, test_return_code=0)
    task = FileLocalTask(
        session_id="s1",
        target_path=str(f),
        old_string="hello",
        new_string="goodbye",
    )
    result = runner.run_task(task)
    assert result.success is True
    assert result.patch_applied is True
    assert result.test_passed is True


def test_result_artifact_is_written(tmp_path):
    f = _writable_file(tmp_path)
    runner = _make_runner(tmp_path)
    task = FileLocalTask(session_id="s1", target_path=str(f), old_string="hello", new_string="bye")
    result = runner.run_task(task)
    assert result.artifact_path is not None
    assert Path(result.artifact_path).exists()


def test_single_file_safety_enforced(tmp_path):
    f = _writable_file(tmp_path)
    runner = _make_runner(tmp_path)
    task = FileLocalTask(
        session_id="s1",
        target_path=str(f),
        old_string="NOT_PRESENT",
        new_string="x",
    )
    result = runner.run_task(task)
    assert result.patch_applied is False
    assert result.success is False


def test_unsafe_task_kind_fails_cleanly(tmp_path):
    f = _writable_file(tmp_path)
    runner = _make_runner(tmp_path)
    task = FileLocalTask(
        session_id="s1",
        target_path=str(f),
        old_string="hello",
        new_string="bye",
        task_kind="dangerous_operation",
    )
    result = runner.run_task(task)
    assert result.success is False
    assert result.error is not None


def test_bounded_one_attempt_semantics(tmp_path):
    f = _writable_file(tmp_path, "once")
    runner = _make_runner(tmp_path)
    task = FileLocalTask(session_id="s1", target_path=str(f), old_string="once", new_string="done")
    result = runner.run_task(task)
    assert f.read_text() == "done"
    result2 = runner.run_task(task)
    assert result2.patch_applied is False


def test_helper_task_kind_passes(tmp_path):
    f = _writable_file(tmp_path, "def old(): pass")
    runner = _make_runner(tmp_path)
    task = FileLocalTask(
        session_id="s1",
        target_path=str(f),
        old_string="def old(): pass",
        new_string="def old(): pass\ndef helper(): pass",
        task_kind="helper_insertion",
    )
    result = runner.run_task(task)
    assert result.patch_applied is True


def test_metadata_task_kind_passes(tmp_path):
    f = _writable_file(tmp_path, "# version: 1")
    runner = _make_runner(tmp_path)
    task = FileLocalTask(
        session_id="s1",
        target_path=str(f),
        old_string="# version: 1",
        new_string="# version: 2",
        task_kind="metadata_addition",
    )
    result = runner.run_task(task)
    assert result.patch_applied is True


def test_denied_write_path_fails_cleanly(tmp_path):
    src = tmp_path / "src" / "protected.py"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("protected content", encoding="utf-8")
    runner = _make_runner(tmp_path)
    task = FileLocalTask(
        session_id="s1",
        target_path=str(src),
        old_string="protected content",
        new_string="modified",
    )
    result = runner.run_task(task)
    assert result.patch_applied is False
    assert result.success is False


def test_package_surface_export():
    import framework
    assert hasattr(framework, "dispatch_apply_patch")
    assert hasattr(framework, "FileLocalTask")
    assert hasattr(framework, "FileLocalResult")
    assert hasattr(framework, "FileLocalDevloopRunner")
