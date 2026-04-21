"""Seam tests for LACE1-P3-TASK-DECOMP-SUBSTRATE-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.task_decomposition_substrate import TaskDecompositionSubstrate, DecomposedTaskBundle, SubTask


def test_import_substrate():
    from framework.task_decomposition_substrate import TaskDecompositionSubstrate
    assert callable(TaskDecompositionSubstrate)


def test_guard_kind():
    b = TaskDecompositionSubstrate().decompose("add guard clause", ["framework/scheduler.py"])
    assert len(b.subtasks) == 1
    assert b.subtasks[0].kind == "add_guard"


def test_test_kind():
    b = TaskDecompositionSubstrate().decompose("add test for retry", ["tests/t.py"])
    assert b.subtasks[0].kind == "add_test"


def test_replace_kind():
    b = TaskDecompositionSubstrate().decompose("replace constant value", ["framework/a.py"])
    assert b.subtasks[0].kind == "replace_text"


def test_two_files_two_subtasks():
    b = TaskDecompositionSubstrate().decompose("add test and replace logic", ["tests/t.py", "framework/a.py"])
    assert len(b.subtasks) == 2
    assert b.estimated_total_loe == 2


def test_emit_writes_json(tmp_path):
    sub = TaskDecompositionSubstrate()
    b = sub.decompose("add guard clause", ["framework/scheduler.py"], bundle_id="TEST-BUNDLE")
    path = sub.emit(b, artifact_dir=tmp_path)
    assert Path(path).exists()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["bundle_id"] == "TEST-BUNDLE"
    assert len(data["subtasks"]) == 1
