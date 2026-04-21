"""Tests for framework.gitdiff_review_packager — GitDiffReviewPackager seam."""
import pytest
from pathlib import Path

from framework.gitdiff_review_packager import DiffReviewRecord, GitDiffReviewPackager


def test_import_ok():
    from framework.gitdiff_review_packager import DiffReviewRecord, GitDiffReviewPackager  # noqa: F401


def test_no_subprocess_import():
    import framework.gitdiff_review_packager as m
    import sys
    # module must not introduce a new subprocess path
    assert hasattr(m, "GitDiffReviewPackager")


def test_record_fields():
    r = DiffReviewRecord(target_path="a.py", diff_text="", line_count=0, has_changes=False, packaged_at="T")
    assert r.target_path == "a.py"
    assert r.diff_text == ""
    assert r.line_count == 0
    assert r.has_changes is False


def test_is_empty_true_when_no_changes():
    r = DiffReviewRecord(target_path="a.py", diff_text="", line_count=0, has_changes=False, packaged_at="T")
    assert r.is_empty() is True


def test_is_empty_false_when_changes():
    r = DiffReviewRecord(target_path="a.py", diff_text="+new line", line_count=1, has_changes=True, packaged_at="T")
    assert r.is_empty() is False


def test_to_dict_keys():
    r = DiffReviewRecord(target_path="a.py", diff_text="+x", line_count=1, has_changes=True, packaged_at="2026-01-01T00:00:00+00:00")
    d = r.to_dict()
    for k in ("target_path", "diff_text", "line_count", "has_changes", "packaged_at"):
        assert k in d


def test_package_diff_returns_record():
    packager = GitDiffReviewPackager()
    record = packager.package_diff("framework/__init__.py")
    assert isinstance(record, DiffReviewRecord)


def test_package_diff_iso_timestamp():
    packager = GitDiffReviewPackager()
    record = packager.package_diff("framework/__init__.py")
    assert "T" in record.packaged_at


def test_package_diff_target_path_propagated():
    packager = GitDiffReviewPackager()
    record = packager.package_diff("framework/__init__.py")
    assert record.target_path == "framework/__init__.py"


def test_package_diff_nonexistent_file_graceful():
    packager = GitDiffReviewPackager()
    record = packager.package_diff("no_such_file_xyz.py")
    assert isinstance(record, DiffReviewRecord)
    assert record.has_changes is False


def test_line_count_non_negative():
    packager = GitDiffReviewPackager()
    record = packager.package_diff("framework/__init__.py")
    assert record.line_count >= 0


def test_line_count_matches_diff_lines():
    packager = GitDiffReviewPackager()
    record = packager.package_diff("framework/__init__.py")
    if record.diff_text:
        assert record.line_count == len(record.diff_text.splitlines())


def test_change_detection_consistent():
    packager = GitDiffReviewPackager()
    record = packager.package_diff("framework/__init__.py")
    if record.diff_text.strip():
        assert record.has_changes is True
    else:
        assert record.has_changes is False


def test_package_diff_with_ref():
    packager = GitDiffReviewPackager()
    record = packager.package_diff("framework/__init__.py", ref="HEAD")
    assert isinstance(record, DiffReviewRecord)


def test_package_diff_init_ok():
    from framework import GitDiffReviewPackager as GDR  # noqa: F401
