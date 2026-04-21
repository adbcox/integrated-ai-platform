"""Seam tests for LACE2-P7-REAL-FILE-BENCHMARK-PACK-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.real_file_benchmark_pack import (
    RealFileTask, LACE2_REAL_FILE_PACK, validate_real_file_greps,
    emit_real_file_pack, load_real_file_pack,
)


def test_import_pack():
    assert callable(emit_real_file_pack)


def test_eight_tasks():
    assert len(LACE2_REAL_FILE_PACK) == 8


def test_kind_distribution():
    kinds = {}
    for t in LACE2_REAL_FILE_PACK:
        kinds[t.task_kind] = kinds.get(t.task_kind, 0) + 1
    assert kinds.get("text_replacement", 0) == 2
    assert kinds.get("insert_block", 0) == 2
    assert kinds.get("add_guard", 0) == 2
    assert kinds.get("add_field", 0) == 2


def test_all_source_files_exist():
    for t in LACE2_REAL_FILE_PACK:
        p = REPO_ROOT / t.source_fixture_file
        assert p.exists(), f"{t.task_id}: {t.source_fixture_file} not found"


def test_expected_content_derivation():
    for t in LACE2_REAL_FILE_PACK:
        assert t.new_string in t.expected_content, f"{t.task_id}: new_string not in expected_content"
        assert t.old_string != t.expected_content, f"{t.task_id}: expected_content unchanged"


def test_round_trip(tmp_path):
    path = emit_real_file_pack(LACE2_REAL_FILE_PACK, tmp_path)
    loaded = load_real_file_pack(path)
    assert len(loaded) == 8
    assert all(isinstance(t, RealFileTask) for t in loaded)
    assert loaded[0].task_id == "LACE2-RF-01"
