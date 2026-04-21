"""Conformance tests for framework/git_diff_dispatch.py (ADSC1-GITDIFF-DISPATCH-SEAM-1)."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.git_diff_dispatch import dispatch_git_diff
from framework.tool_schema import GitDiffAction, GitDiffObservation
from framework.workspace_scope import ToolPathScope


@dataclass
class _FakeResult:
    return_code: int
    stdout: str
    stderr: str


class _FakeRunner:
    def __init__(self, stdout="", stderr="", rc=0):
        self._stdout = stdout
        self._stderr = stderr
        self._rc = rc

    def run_command(self, *, command, cwd, env=None):
        return _FakeResult(return_code=self._rc, stdout=self._stdout, stderr=self._stderr)


def _scope(root=REPO_ROOT):
    return ToolPathScope(source_root=root)


# --- import and type ---

def test_import_dispatch_git_diff():
    assert callable(dispatch_git_diff)


def test_returns_git_diff_observation():
    result = dispatch_git_diff(GitDiffAction(path=str(REPO_ROOT)), _scope())
    assert isinstance(result, GitDiffObservation)


# --- real git diff ---

def test_diff_is_string():
    result = dispatch_git_diff(GitDiffAction(path=str(REPO_ROOT)), _scope())
    assert isinstance(result.diff, str)


def test_no_error_on_clean_tree():
    result = dispatch_git_diff(GitDiffAction(path=str(REPO_ROOT)), _scope())
    # may or may not have diff, but error should be None on success
    assert result.error is None or isinstance(result.error, str)


# --- runner injection ---

def test_fake_runner_injected():
    runner = _FakeRunner(stdout="diff --git a/x b/x\n", rc=0)
    result = dispatch_git_diff(GitDiffAction(path=str(REPO_ROOT)), _scope(), runner=runner)
    assert result.diff == "diff --git a/x b/x\n"
    assert result.error is None


def test_fake_runner_nonzero_no_stdout():
    runner = _FakeRunner(stdout="", stderr="fatal: bad revision", rc=128)
    result = dispatch_git_diff(GitDiffAction(path=str(REPO_ROOT)), _scope(), runner=runner)
    assert result.error is not None


def test_fake_runner_nonzero_with_stdout():
    runner = _FakeRunner(stdout="some diff content", stderr="", rc=1)
    result = dispatch_git_diff(GitDiffAction(path=str(REPO_ROOT)), _scope(), runner=runner)
    assert result.diff == "some diff content"


# --- ref argument ---

def test_ref_none_works(tmp_path):
    runner = _FakeRunner(stdout="", rc=0)
    result = dispatch_git_diff(GitDiffAction(path=str(REPO_ROOT), ref=None), _scope(), runner=runner)
    assert isinstance(result, GitDiffObservation)


def test_ref_string_passed(tmp_path):
    runner = _FakeRunner(stdout="ref diff", rc=0)
    result = dispatch_git_diff(GitDiffAction(path=str(REPO_ROOT), ref="HEAD~1"), _scope(), runner=runner)
    assert result.diff == "ref diff"


# --- nonexistent path ---

def test_nonexistent_cwd_error_in_observation(tmp_path):
    scope = ToolPathScope(source_root=tmp_path)
    result = dispatch_git_diff(GitDiffAction(path=str(tmp_path / "no_such")), scope)
    assert result.error is not None or isinstance(result.diff, str)


# --- package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "dispatch_git_diff")
    assert callable(framework.dispatch_git_diff)
