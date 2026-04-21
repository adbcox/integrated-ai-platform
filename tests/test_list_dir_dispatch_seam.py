"""Conformance tests for framework/list_dir_dispatch.py (ADSC1-LISTDIR-DISPATCH-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.list_dir_dispatch import dispatch_list_dir
from framework.tool_schema import ListDirAction, ListDirObservation
from framework.workspace_scope import ToolPathScope


def _scope(root):
    return ToolPathScope(source_root=root)


# --- import and type ---

def test_import_dispatch_list_dir():
    assert callable(dispatch_list_dir)


def test_returns_list_dir_observation(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    result = dispatch_list_dir(ListDirAction(path=str(tmp_path)), _scope(tmp_path))
    assert isinstance(result, ListDirObservation)


# --- valid directory ---

def test_valid_dir_returns_entries(tmp_path):
    (tmp_path / "foo.py").write_text("")
    (tmp_path / "bar").mkdir()
    result = dispatch_list_dir(ListDirAction(path=str(tmp_path)), _scope(tmp_path))
    assert result.error is None
    assert len(result.entries) == 2


def test_entries_are_strings(tmp_path):
    (tmp_path / "x.py").write_text("")
    result = dispatch_list_dir(ListDirAction(path=str(tmp_path)), _scope(tmp_path))
    for e in result.entries:
        assert isinstance(e, str)


def test_entries_have_type_tag(tmp_path):
    (tmp_path / "file.py").write_text("")
    (tmp_path / "subdir").mkdir()
    result = dispatch_list_dir(ListDirAction(path=str(tmp_path)), _scope(tmp_path))
    names = {e.split(" [")[0] for e in result.entries}
    tags = {e.split("[")[1].rstrip("]") for e in result.entries}
    assert "file.py" in names
    assert "subdir" in names
    assert tags <= {"file", "dir"}


def test_entries_sorted(tmp_path):
    (tmp_path / "z.py").write_text("")
    (tmp_path / "a.py").write_text("")
    (tmp_path / "m.py").write_text("")
    result = dispatch_list_dir(ListDirAction(path=str(tmp_path)), _scope(tmp_path))
    assert list(result.entries) == sorted(result.entries)


# --- error cases ---

def test_nonexistent_path_error_in_observation(tmp_path):
    result = dispatch_list_dir(ListDirAction(path=str(tmp_path / "no_such")), _scope(tmp_path))
    assert result.error is not None
    assert result.entries == ()


def test_file_path_not_dir_error_in_observation(tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("x")
    result = dispatch_list_dir(ListDirAction(path=str(f)), _scope(tmp_path))
    assert result.error is not None


# --- path echo ---

def test_path_echoed_in_observation(tmp_path):
    result = dispatch_list_dir(ListDirAction(path=str(tmp_path)), _scope(tmp_path))
    assert result.path == str(tmp_path)


# --- empty dir ---

def test_empty_dir_returns_empty_entries(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    result = dispatch_list_dir(ListDirAction(path=str(empty)), _scope(tmp_path))
    assert result.entries == ()
    assert result.error is None


# --- package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "dispatch_list_dir")
    assert callable(framework.dispatch_list_dir)
