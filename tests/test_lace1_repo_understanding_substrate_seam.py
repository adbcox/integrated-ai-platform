"""Seam tests for LACE1-P2-REPO-UNDERSTANDING-SUBSTRATE-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.repo_understanding_substrate import RepoUnderstandingSubstrate, RepoUnderstandingSummary


def test_import_substrate():
    from framework.repo_understanding_substrate import RepoUnderstandingSubstrate
    assert callable(RepoUnderstandingSubstrate)


def test_scan_returns_summary():
    s = RepoUnderstandingSubstrate(REPO_ROOT).scan()
    assert isinstance(s, RepoUnderstandingSummary)


def test_real_repo_scan_nonzero():
    s = RepoUnderstandingSubstrate(REPO_ROOT).scan()
    assert s.total_files_scanned > 0
    assert s.total_symbols > 0


def test_framework_file_count_nonzero():
    s = RepoUnderstandingSubstrate(REPO_ROOT).scan()
    assert s.framework_file_count > 0


def test_top_files_populated():
    s = RepoUnderstandingSubstrate(REPO_ROOT).scan()
    assert len(s.top_files_by_symbol_count) > 0
    for entry in s.top_files_by_symbol_count:
        assert "path" in entry
        assert "symbol_count" in entry


def test_emit_artifact_written(tmp_path):
    sub = RepoUnderstandingSubstrate(REPO_ROOT)
    s = sub.scan()
    path = sub.emit(s, artifact_dir=tmp_path)
    assert Path(path).exists()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["total_files_scanned"] > 0
    assert data["total_symbols"] > 0
