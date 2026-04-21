"""Conformance tests for framework/workspace_scope.py (RUNTIME-CONTRACT-A1-WORKSPACE-SEAM-1)."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.workspace_scope import ToolPathScope, scope_from_runtime_workspace, scope_from_workspace_context


def test_construct_minimal_scope(tmp_path):
    scope = ToolPathScope(source_root=tmp_path)
    assert scope.source_root == tmp_path
    assert scope.writable_roots == ()


def test_resolve_read_returns_absolute(tmp_path):
    scope = ToolPathScope(source_root=tmp_path)
    resolved = scope.resolve_path(tmp_path / "file.py")
    assert resolved.is_absolute()


def test_write_into_source_root_raises(tmp_path):
    scope = ToolPathScope(source_root=tmp_path)
    with pytest.raises(PermissionError):
        scope.resolve_path(tmp_path / "src" / "main.py", writable=True)


def test_write_into_writable_root_succeeds(tmp_path):
    writable = tmp_path / "scratch"
    writable.mkdir()
    scope = ToolPathScope(source_root=tmp_path / "src", writable_roots=(writable,))
    result = scope.resolve_path(writable / "out.txt", writable=True)
    assert result.is_absolute()


def test_write_with_no_writable_roots_raises(tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    scope = ToolPathScope(source_root=tmp_path / "src")
    with pytest.raises(PermissionError):
        scope.resolve_path(other / "out.txt", writable=True)


def test_write_outside_all_roots_raises(tmp_path):
    writable = tmp_path / "scratch"
    writable.mkdir()
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    scope = ToolPathScope(source_root=tmp_path / "src", writable_roots=(writable,))
    with pytest.raises(PermissionError):
        scope.resolve_path(outside / "out.txt", writable=True)


def test_is_writable_true_under_writable_root(tmp_path):
    writable = tmp_path / "scratch"
    writable.mkdir()
    scope = ToolPathScope(source_root=tmp_path / "src", writable_roots=(writable,))
    assert scope.is_writable(writable / "out.txt") is True


def test_is_writable_false_under_source_root(tmp_path):
    scope = ToolPathScope(source_root=tmp_path)
    assert scope.is_writable(tmp_path / "src" / "main.py") is False


def test_scope_from_runtime_workspace(tmp_path):
    @dataclass
    class FakeRuntimeWorkspace:
        source_root: Path
        scratch_root: Path
        artifact_root: Path

    ws = FakeRuntimeWorkspace(
        source_root=tmp_path / "src",
        scratch_root=tmp_path / "scratch",
        artifact_root=tmp_path / "artifacts",
    )
    scope = scope_from_runtime_workspace(ws)
    assert scope.source_root == (tmp_path / "src").resolve()
    assert len(scope.writable_roots) == 2


def test_scope_from_workspace_context(tmp_path):
    @dataclass
    class FakeWorkspaceContext:
        repo_root: Path
        worktree_target: Path
        artifact_root: Path

    ctx = FakeWorkspaceContext(
        repo_root=tmp_path / "repo",
        worktree_target=tmp_path / "worktree",
        artifact_root=tmp_path / "artifacts",
    )
    scope = scope_from_workspace_context(ctx)
    assert scope.source_root == (tmp_path / "repo").resolve()
    assert len(scope.writable_roots) == 2
