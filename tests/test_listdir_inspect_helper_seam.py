"""Conformance tests for framework/listdir_inspect_helper.py (LARAC2-LISTDIR-ADOPTION-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.listdir_inspect_helper import ListDirInspectHelper, TargetDiscoveryResult
from framework.listdir_loop_adapter import DirEntry, DirListing


def _mock_adapter(entries=None):
    adapter = MagicMock()
    if entries is None:
        entries = []
    listing = DirListing(
        root_path="/some/dir",
        entries=entries,
        listed_at="2026-01-01T00:00:00+00:00",
        entry_count=len(entries),
    )
    adapter.list_dir.return_value = listing
    return adapter


def _entry(path, is_dir=False):
    return DirEntry(path=path, is_dir=is_dir, is_file=not is_dir)


# --- import and type ---

def test_import_listdir_inspect_helper():
    assert callable(ListDirInspectHelper)


def test_returns_target_discovery_result():
    r = ListDirInspectHelper(adapter=_mock_adapter()).discover("some/file.py")
    assert isinstance(r, TargetDiscoveryResult)


# --- fields ---

def test_result_fields_present():
    r = ListDirInspectHelper(adapter=_mock_adapter()).discover("some/file.py")
    assert hasattr(r, "target_path")
    assert hasattr(r, "target_dir")
    assert hasattr(r, "sibling_names")
    assert hasattr(r, "sibling_count")
    assert hasattr(r, "discovery_error")


# --- target_dir derivation ---

def test_target_dir_is_parent():
    r = ListDirInspectHelper(adapter=_mock_adapter()).discover("framework/tool.py")
    assert r.target_dir == "framework"


def test_target_dir_nested():
    r = ListDirInspectHelper(adapter=_mock_adapter()).discover("a/b/c.py")
    assert r.target_dir == "a/b"


# --- siblings ---

def test_siblings_populated():
    entries = [_entry("a.py"), _entry("b.py"), _entry("subdir", is_dir=True)]
    r = ListDirInspectHelper(adapter=_mock_adapter(entries)).discover("a/b.py")
    assert set(r.sibling_names) == {"a.py", "b.py", "subdir"}
    assert r.sibling_count == 3


def test_sibling_uses_path_field():
    entries = [_entry("src/foo.py"), _entry("src/bar.py")]
    r = ListDirInspectHelper(adapter=_mock_adapter(entries)).discover("src/baz.py")
    assert r.sibling_count == 2


def test_empty_siblings():
    r = ListDirInspectHelper(adapter=_mock_adapter([])).discover("x/y.py")
    assert r.sibling_names == ()
    assert r.sibling_count == 0


# --- failure is non-blocking ---

def test_discovery_failure_non_blocking():
    adapter = MagicMock()
    adapter.list_dir.side_effect = OSError("permission denied")
    r = ListDirInspectHelper(adapter=adapter).discover("x/y.py")
    assert r.discovery_error is not None
    assert "permission denied" in r.discovery_error


def test_discovery_failure_returns_empty_siblings():
    adapter = MagicMock()
    adapter.list_dir.side_effect = RuntimeError("unexpected error")
    r = ListDirInspectHelper(adapter=adapter).discover("x/y.py")
    assert r.sibling_names == ()
    assert r.sibling_count == 0


# --- target_path preserved ---

def test_target_path_preserved():
    r = ListDirInspectHelper(adapter=_mock_adapter()).discover("my/file.py")
    assert r.target_path == "my/file.py"


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "ListDirInspectHelper")
    assert hasattr(framework, "TargetDiscoveryResult")
