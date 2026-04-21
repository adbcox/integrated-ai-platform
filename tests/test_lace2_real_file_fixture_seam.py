"""Seam tests for LACE2-P8-REAL-FILE-FIXTURE-SEAM-1."""
from __future__ import annotations
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.real_file_benchmark_fixture import FixtureResult, RealFileBenchmarkFixture
from framework.real_file_benchmark_pack import LACE2_REAL_FILE_PACK


def test_import_fixture():
    assert callable(RealFileBenchmarkFixture)


def test_setup_returns_fixture_result(tmp_path):
    task = LACE2_REAL_FILE_PACK[0]
    fixture = RealFileBenchmarkFixture()
    result = fixture.setup(task, tmp_path)
    assert isinstance(result, FixtureResult)


def test_setup_ok_true(tmp_path):
    task = LACE2_REAL_FILE_PACK[0]
    result = RealFileBenchmarkFixture().setup(task, tmp_path)
    assert result.setup_ok is True


def test_fixture_file_contains_initial_content(tmp_path):
    task = LACE2_REAL_FILE_PACK[0]
    result = RealFileBenchmarkFixture().setup(task, tmp_path)
    on_disk = result.fixture_path.read_text(encoding="utf-8")
    assert on_disk == task.initial_content


def test_teardown_removes_file(tmp_path):
    task = LACE2_REAL_FILE_PACK[0]
    fixture = RealFileBenchmarkFixture()
    result = fixture.setup(task, tmp_path)
    assert result.fixture_path.exists()
    ok = fixture.teardown(result)
    assert ok is True
    assert not result.fixture_path.exists()


def test_all_tasks_setup_ok(tmp_path):
    fixture = RealFileBenchmarkFixture()
    for task in LACE2_REAL_FILE_PACK:
        result = fixture.setup(task, tmp_path)
        assert result.setup_ok, f"{task.task_id}: setup failed"
        fixture.teardown(result)
