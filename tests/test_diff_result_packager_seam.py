"""Conformance tests for framework/diff_result_packager.py (LARAC2-GITDIFF-RESULT-SEAM-1)."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.diff_result_packager import DiffResultPackager, DiffResultPackage


@dataclass
class _FakeResult:
    return_code: int
    stdout: str
    stderr: str


def _fake_runner(output="diff output", return_code=0):
    runner = MagicMock()
    runner.run_command.return_value = _FakeResult(return_code=return_code, stdout=output, stderr="")
    return runner


# --- import and type ---

def test_import_diff_result_packager():
    assert callable(DiffResultPackager)


def test_returns_diff_result_package():
    r = DiffResultPackager(runner=_fake_runner()).package("sess-1")
    assert isinstance(r, DiffResultPackage)


# --- fields ---

def test_result_fields_present():
    r = DiffResultPackager(runner=_fake_runner()).package("sess-1")
    assert hasattr(r, "session_id")
    assert hasattr(r, "diff")
    assert hasattr(r, "diff_error")
    assert hasattr(r, "ref")
    assert hasattr(r, "packaged_at")


# --- session_id preserved ---

def test_session_id_preserved():
    r = DiffResultPackager(runner=_fake_runner()).package("my-session")
    assert r.session_id == "my-session"


# --- diff populated ---

def test_diff_populated_from_runner():
    runner = _fake_runner(output="--- a/f.py\n+++ b/f.py\n@@ -1 +1 @@\n+x=1")
    r = DiffResultPackager(runner=runner).package("s")
    assert "f.py" in r.diff


# --- ref propagation ---

def test_ref_none_by_default():
    r = DiffResultPackager(runner=_fake_runner()).package("s")
    assert r.ref is None


def test_ref_propagated():
    r = DiffResultPackager(runner=_fake_runner()).package("s", ref="HEAD~1")
    assert r.ref == "HEAD~1"


# --- error non-raising ---

def test_error_non_raising():
    runner = MagicMock()
    runner.run_command.side_effect = OSError("git not found")
    r = DiffResultPackager(runner=runner).package("s")
    assert r.diff_error is not None
    assert r.diff == ""


def test_no_exception_propagated():
    runner = MagicMock()
    runner.run_command.side_effect = RuntimeError("unexpected")
    r = DiffResultPackager(runner=runner).package("s")
    assert isinstance(r, DiffResultPackage)


# --- packaged_at timestamp ---

def test_packaged_at_is_string():
    r = DiffResultPackager(runner=_fake_runner()).package("s")
    assert isinstance(r.packaged_at, str)
    assert len(r.packaged_at) > 0


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "DiffResultPackager")
    assert hasattr(framework, "DiffResultPackage")
