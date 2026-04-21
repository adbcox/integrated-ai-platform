"""Seam tests for LACE2-P11-FAILURE-MINER-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.real_run_failure_miner import RealRunFailureMiner, FailureMinerRecord


def test_import_miner():
    assert callable(RealRunFailureMiner)


def test_mine_returns_record():
    r = RealRunFailureMiner().mine()
    assert isinstance(r, FailureMinerRecord)


def test_benchmark_failures_zero():
    r = RealRunFailureMiner().mine()
    assert r.benchmark_failures == 0


def test_repair_mismatches_zero():
    r = RealRunFailureMiner().mine()
    assert r.repair_mismatches == 0


def test_total_failures_has_value():
    r = RealRunFailureMiner().mine()
    assert isinstance(r.total_failures, int)
    assert r.total_failures >= 0


def test_emit_artifact(tmp_path):
    miner = RealRunFailureMiner()
    r = miner.mine()
    path = miner.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "benchmark_failures" in data
    assert "repair_mismatches" in data
    assert "replay_not_replayable" in data
    assert "failure_entries" in data
