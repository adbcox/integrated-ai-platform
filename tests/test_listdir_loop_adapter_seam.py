"""Tests for framework.listdir_loop_adapter — ListDirLoopAdapter seam."""
import pytest
from pathlib import Path

from framework.listdir_loop_adapter import DirEntry, DirListing, ListDirLoopAdapter


def test_import_ok():
    from framework.listdir_loop_adapter import DirEntry, DirListing, ListDirLoopAdapter  # noqa: F401


def test_dir_entry_frozen():
    e = DirEntry(path="a/b.py", is_file=True, is_dir=False)
    with pytest.raises(Exception):
        e.path = "other"


def test_dir_entry_fields():
    e = DirEntry(path="a/b.py", is_file=True, is_dir=False)
    assert e.path == "a/b.py"
    assert e.is_file is True
    assert e.is_dir is False


def test_dir_listing_fields():
    listing = DirListing(root_path=".", entries=[], listed_at="2026-01-01T00:00:00+00:00", entry_count=0)
    assert listing.root_path == "."
    assert listing.entries == []
    assert listing.entry_count == 0


def test_list_dir_returns_listing(tmp_path):
    adapter = ListDirLoopAdapter(source_root=tmp_path)
    listing = adapter.list_dir(".")
    assert isinstance(listing, DirListing)


def test_list_dir_empty_dir(tmp_path):
    adapter = ListDirLoopAdapter(source_root=tmp_path)
    listing = adapter.list_dir(".")
    assert listing.entry_count == 0
    assert listing.entries == []


def test_list_dir_with_files(tmp_path):
    (tmp_path / "a.py").write_text("x")
    (tmp_path / "b.py").write_text("y")
    adapter = ListDirLoopAdapter(source_root=tmp_path)
    listing = adapter.list_dir(".")
    assert listing.entry_count >= 2


def test_file_paths_returns_files(tmp_path):
    (tmp_path / "a.py").write_text("x")
    adapter = ListDirLoopAdapter(source_root=tmp_path)
    listing = adapter.list_dir(".")
    fps = listing.file_paths()
    assert isinstance(fps, list)
    assert any("a.py" in p for p in fps)


def test_file_paths_excludes_dirs(tmp_path):
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file.py").write_text("x")
    adapter = ListDirLoopAdapter(source_root=tmp_path)
    listing = adapter.list_dir(".")
    fps = listing.file_paths()
    assert all("subdir" not in p for p in fps)


def test_to_snippet_returns_string(tmp_path):
    adapter = ListDirLoopAdapter(source_root=tmp_path)
    listing = adapter.list_dir(".")
    snippet = listing.to_snippet()
    assert isinstance(snippet, str)


def test_to_snippet_empty_dir(tmp_path):
    adapter = ListDirLoopAdapter(source_root=tmp_path)
    listing = adapter.list_dir(".")
    snippet = listing.to_snippet()
    assert "empty" in snippet.lower() or "." in snippet


def test_to_snippet_contains_dir_path(tmp_path):
    (tmp_path / "myfile.txt").write_text("z")
    adapter = ListDirLoopAdapter(source_root=tmp_path)
    listing = adapter.list_dir(".")
    snippet = listing.to_snippet()
    assert "." in snippet


def test_nonexistent_path_returns_empty(tmp_path):
    adapter = ListDirLoopAdapter(source_root=tmp_path)
    listing = adapter.list_dir("nonexistent_path_xyz")
    assert isinstance(listing, DirListing)
    assert listing.entry_count == 0


def test_listed_at_is_iso(tmp_path):
    adapter = ListDirLoopAdapter(source_root=tmp_path)
    listing = adapter.list_dir(".")
    assert "T" in listing.listed_at


def test_entry_count_matches_entries(tmp_path):
    (tmp_path / "x.py").write_text("x")
    (tmp_path / "y.py").write_text("y")
    adapter = ListDirLoopAdapter(source_root=tmp_path)
    listing = adapter.list_dir(".")
    assert listing.entry_count == len(listing.entries)


def test_init_ok_from_framework():
    from framework import ListDirLoopAdapter  # noqa: F401
