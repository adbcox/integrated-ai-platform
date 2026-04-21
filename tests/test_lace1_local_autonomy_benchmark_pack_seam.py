"""Seam tests for LACE1-P9-LOCAL-BENCHMARK-TASK-PACK-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.local_autonomy_benchmark_pack import (
    LocalAutonomyTask,
    LACE1_TASK_PACK,
    load_benchmark_pack,
    emit_benchmark_pack,
    validate_acceptance_greps,
)


def test_import_pack():
    from framework.local_autonomy_benchmark_pack import LocalAutonomyTask
    assert callable(LocalAutonomyTask)


def test_task_pack_has_12_tasks():
    assert len(LACE1_TASK_PACK) == 12


def test_kind_distribution():
    from collections import Counter
    counts = Counter(t.task_kind for t in LACE1_TASK_PACK)
    assert counts["text_replacement"] == 3
    assert counts["insert_block"] == 3
    assert counts["add_guard"] == 2
    assert counts["add_test"] == 2
    assert counts["add_field"] == 2


def test_acceptance_greps_all_valid():
    bad = validate_acceptance_greps(LACE1_TASK_PACK)
    assert bad == [], f"invalid greps: {bad}"


def test_expected_content_derived_from_replace():
    for t in LACE1_TASK_PACK:
        expected = t.initial_content.replace(t.old_string, t.new_string, 1)
        assert t.expected_content == expected, f"task {t.task_id} expected_content mismatch"


def test_round_trip_via_load(tmp_path):
    path = emit_benchmark_pack(LACE1_TASK_PACK, tmp_path)
    loaded = load_benchmark_pack(path)
    assert len(loaded) == 12
    assert all(isinstance(t, LocalAutonomyTask) for t in loaded)
    assert loaded[0].task_id == LACE1_TASK_PACK[0].task_id
