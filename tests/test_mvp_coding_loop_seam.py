"""Conformance tests for framework/mvp_coding_loop.py (RMCC1-MVP-LOOP-SEAM-1)."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.mvp_coding_loop import MVPCodingLoopRunner, MVPLoopResult, MVPTask, SAFE_TASK_KINDS
from framework.validation_emit_adapter import emit_loop_validation
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


def _make_env(tmp_path, test_return_code=0):
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    scratch = tmp_path / "scratch"
    scratch.mkdir(exist_ok=True)
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir(exist_ok=True)
    ws = FakeWorkspace(source_root=src, scratch_root=scratch, artifact_root=artifacts)
    scope = ToolPathScope(source_root=src, writable_roots=(scratch, artifacts))
    session = FakeSession(session_id="mvp-test-session")
    gate = TypedPermissionGate(default_permission=ToolPermission.ALLOW)
    runner = MVPCodingLoopRunner(session, ws, gate, scope, runner=FakeRunner(return_code=test_return_code))
    return runner, scope, scratch, artifacts


def _writable_file(scratch, content="original content"):
    f = scratch / "target.py"
    f.write_text(content, encoding="utf-8")
    return f


# --- SAFE_TASK_KINDS ---

def test_safe_task_kinds_defined():
    assert "text_replacement" in SAFE_TASK_KINDS
    assert "helper_insertion" in SAFE_TASK_KINDS
    assert "metadata_addition" in SAFE_TASK_KINDS


# --- Valid task succeeds ---

def test_valid_task_succeeds(tmp_path):
    runner, scope, scratch, _ = _make_env(tmp_path)
    f = _writable_file(scratch)
    task = MVPTask(session_id="s1", target_path=str(f), old_string="original content", new_string="modified content")
    result = runner.run_task(task)
    assert isinstance(result, MVPLoopResult)
    assert result.patch_applied is True
    assert result.inspect_ok is True
    assert result.success is True


# --- Missing target file fails inspect ---

def test_missing_target_file_fails_inspect(tmp_path):
    runner, scope, scratch, _ = _make_env(tmp_path)
    task = MVPTask(session_id="s1", target_path=str(scratch / "nonexistent.py"), old_string="x", new_string="y")
    result = runner.run_task(task)
    assert result.inspect_ok is False
    assert result.success is False
    assert result.error is not None


# --- Missing old string fails patch cleanly ---

def test_missing_old_string_fails_patch(tmp_path):
    runner, scope, scratch, _ = _make_env(tmp_path)
    f = _writable_file(scratch, "actual content here")
    task = MVPTask(session_id="s1", target_path=str(f), old_string="NOT_PRESENT", new_string="something")
    result = runner.run_task(task)
    assert result.patch_applied is False
    assert result.success is False


# --- Unsafe task kind rejected ---

def test_unsafe_task_kind_rejected(tmp_path):
    runner, scope, scratch, _ = _make_env(tmp_path)
    f = _writable_file(scratch)
    task = MVPTask(session_id="s1", target_path=str(f), old_string="original content", new_string="x", task_kind="dangerous")
    result = runner.run_task(task)
    assert result.success is False
    assert result.error is not None


# --- Test failure triggers bounded revert when enabled ---

def test_test_failure_triggers_revert(tmp_path):
    runner, scope, scratch, _ = _make_env(tmp_path, test_return_code=1)
    f = _writable_file(scratch, "original content")
    task = MVPTask(
        session_id="s1", target_path=str(f),
        old_string="original content", new_string="modified content",
        enable_revert=True,
    )
    result = runner.run_task(task)
    assert result.patch_applied is True
    assert result.test_passed is False
    assert result.reverted is True
    assert f.read_text() == "original content"


def test_test_failure_no_revert_when_disabled(tmp_path):
    runner, scope, scratch, _ = _make_env(tmp_path, test_return_code=1)
    f = _writable_file(scratch, "original content")
    task = MVPTask(
        session_id="s1", target_path=str(f),
        old_string="original content", new_string="modified content",
        enable_revert=False,
    )
    result = runner.run_task(task)
    assert result.patch_applied is True
    assert result.reverted is False
    assert f.read_text() == "modified content"


# --- No infinite retry ---

def test_no_infinite_retry_one_attempt(tmp_path):
    runner, scope, scratch, _ = _make_env(tmp_path, test_return_code=1)
    f = _writable_file(scratch, "content")
    task = MVPTask(session_id="s1", target_path=str(f), old_string="content", new_string="new")
    result = runner.run_task(task)
    assert result.patch_applied is True
    assert result.test_passed is False


# --- Result artifact written ---

def test_result_artifact_written(tmp_path):
    runner, scope, scratch, artifacts = _make_env(tmp_path)
    f = _writable_file(scratch)
    task = MVPTask(session_id="s1", target_path=str(f), old_string="original content", new_string="x")
    result = runner.run_task(task)
    assert result.artifact_path is not None
    assert Path(result.artifact_path).exists()


# --- Validation artifact emitted via adapter ---

def test_validation_artifact_emitted(tmp_path):
    runner, scope, scratch, artifacts = _make_env(tmp_path)
    f = _writable_file(scratch)
    task = MVPTask(session_id="s1", target_path=str(f), old_string="original content", new_string="x")
    result = runner.run_task(task)
    assert result.validation_artifact_path is not None


# --- Retrieval path does not block success ---

def test_retrieval_path_does_not_block(tmp_path):
    runner, scope, scratch, _ = _make_env(tmp_path)
    f = _writable_file(scratch, "def foo(): pass")
    task = MVPTask(
        session_id="s1", target_path=str(f),
        old_string="def foo(): pass", new_string="def foo(): return 1",
        retrieval_query="foo function",
    )
    result = runner.run_task(task)
    assert result.inspect_ok is True
    assert result.patch_applied is True


# --- emit_loop_validation adapter ---

def test_emit_loop_validation_dry_run():
    result = emit_loop_validation(
        session_id="s1", job_id="j1", outcome="pass",
        step_results=({"step": "patch", "success": True},),
        dry_run=True,
    )
    assert result is None


def test_emit_loop_validation_writes_record(tmp_path):
    result = emit_loop_validation(
        session_id="s1", job_id="j1", outcome="pass",
        step_results=({"step": "patch", "success": True},),
        artifact_dir=tmp_path,
    )
    assert result is not None
    assert Path(result).exists()


# --- No subprocess/inference in loop module ---

def test_no_subprocess_in_mvp_loop():
    import framework.mvp_coding_loop as mod
    src = Path(mod.__file__).read_text()
    assert "subprocess" not in src
    assert "ollama" not in src.lower()


# --- Package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "MVPTask")
    assert hasattr(framework, "MVPLoopResult")
    assert hasattr(framework, "MVPCodingLoopRunner")
    assert hasattr(framework, "SAFE_TASK_KINDS")
    assert hasattr(framework, "emit_loop_validation")
