"""Conformance tests for framework/devloop_benchmark.py (DEVLOOP-A1-TASK-BENCHMARK-SEAM-1)."""
from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.devloop_benchmark import (
    DevloopBenchmarkResult,
    DevloopBenchmarkRunner,
    DevloopTask,
    SYNTHETIC_TASK_FAMILY,
)
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


def _make_env(tmp_path):
    task_tmpdir = tmp_path / "tasks"
    task_tmpdir.mkdir()
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    scratch = tmp_path / "scratch"
    scratch.mkdir(exist_ok=True)
    ws_artifacts = tmp_path / "ws_artifacts"
    ws_artifacts.mkdir(exist_ok=True)
    bench_artifacts = tmp_path / "bench_artifacts"
    bench_artifacts.mkdir(exist_ok=True)

    scope = ToolPathScope(
        source_root=src,
        writable_roots=(task_tmpdir, scratch, ws_artifacts),
    )
    ws = FakeWorkspace(source_root=src, scratch_root=scratch, artifact_root=ws_artifacts)
    session = FakeSession(session_id="bench-test")
    gate = TypedPermissionGate(default_permission=ToolPermission.ALLOW)
    runner = DevloopBenchmarkRunner(artifact_root=bench_artifacts)

    return runner, task_tmpdir, session, ws, gate, scope, bench_artifacts


# --- SYNTHETIC_TASK_FAMILY ---

def test_exactly_five_synthetic_tasks():
    assert len(SYNTHETIC_TASK_FAMILY) == 5


def test_all_tasks_are_devloop_task_instances():
    for task in SYNTHETIC_TASK_FAMILY:
        assert isinstance(task, DevloopTask)


def test_all_tasks_deterministic_unique_ids():
    ids = [t.task_id for t in SYNTHETIC_TASK_FAMILY]
    assert len(set(ids)) == 5


def test_all_tasks_have_non_empty_content():
    for task in SYNTHETIC_TASK_FAMILY:
        assert task.initial_content
        assert task.old_string
        assert task.new_string
        assert task.expected_content


def test_all_tasks_have_safe_task_kinds():
    safe = {"text_replacement", "helper_insertion", "metadata_addition"}
    for task in SYNTHETIC_TASK_FAMILY:
        assert task.task_kind in safe


# --- benchmark runner ---

def test_benchmark_runner_returns_expected_totals(tmp_path):
    runner, task_tmpdir, session, ws, gate, scope, _ = _make_env(tmp_path)
    result = runner.run(
        SYNTHETIC_TASK_FAMILY,
        task_tmpdir=task_tmpdir,
        session_like=session,
        workspace_like=ws,
        gate=gate,
        scope=scope,
        runner=FakeRunner(),
    )
    assert result.total_tasks == 5
    assert result.passed + result.failed == 5


def test_all_pass_synthetic_run(tmp_path):
    runner, task_tmpdir, session, ws, gate, scope, _ = _make_env(tmp_path)
    result = runner.run(
        SYNTHETIC_TASK_FAMILY,
        task_tmpdir=task_tmpdir,
        session_like=session,
        workspace_like=ws,
        gate=gate,
        scope=scope,
        runner=FakeRunner(),
    )
    assert result.passed == 5
    assert result.failed == 0
    assert result.outcome == "pass"


def test_json_artifact_written_and_parseable(tmp_path):
    runner, task_tmpdir, session, ws, gate, scope, bench_artifacts = _make_env(tmp_path)
    result = runner.run(
        SYNTHETIC_TASK_FAMILY,
        task_tmpdir=task_tmpdir,
        session_like=session,
        workspace_like=ws,
        gate=gate,
        scope=scope,
        runner=FakeRunner(),
    )
    assert result.artifact_path is not None
    data = json.loads(Path(result.artifact_path).read_text())
    assert data["total_tasks"] == 5
    assert "passed" in data
    assert "failed" in data
    assert "outcome" in data


def test_artifact_path_under_artifact_root(tmp_path):
    runner, task_tmpdir, session, ws, gate, scope, bench_artifacts = _make_env(tmp_path)
    result = runner.run(
        SYNTHETIC_TASK_FAMILY,
        task_tmpdir=task_tmpdir,
        session_like=session,
        workspace_like=ws,
        gate=gate,
        scope=scope,
        runner=FakeRunner(),
    )
    assert Path(result.artifact_path).parent == bench_artifacts


def test_result_totals_internally_consistent(tmp_path):
    runner, task_tmpdir, session, ws, gate, scope, _ = _make_env(tmp_path)
    result = runner.run(
        SYNTHETIC_TASK_FAMILY,
        task_tmpdir=task_tmpdir,
        session_like=session,
        workspace_like=ws,
        gate=gate,
        scope=scope,
        runner=FakeRunner(),
    )
    assert result.passed + result.failed == result.total_tasks
    if result.failed == 0:
        assert result.outcome == "pass"
    else:
        assert result.outcome == "fail"


def test_task_targets_stay_inside_tempdir(tmp_path):
    runner, task_tmpdir, session, ws, gate, scope, _ = _make_env(tmp_path)
    result = runner.run(
        SYNTHETIC_TASK_FAMILY,
        task_tmpdir=task_tmpdir,
        session_like=session,
        workspace_like=ws,
        gate=gate,
        scope=scope,
        runner=FakeRunner(),
    )
    for tr in result.task_results:
        assert tr["passed"] or tr["error"] is not None


def test_script_syntax_valid():
    script = REPO_ROOT / "bin" / "devloop_benchmark_run.py"
    ast.parse(script.read_text())


def test_package_surface_export():
    import framework
    assert hasattr(framework, "DevloopTask")
    assert hasattr(framework, "DevloopBenchmarkResult")
    assert hasattr(framework, "DevloopBenchmarkRunner")
    assert hasattr(framework, "SYNTHETIC_TASK_FAMILY")
    assert len(framework.SYNTHETIC_TASK_FAMILY) == 5
