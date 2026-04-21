"""Seam tests for LACE2-P6-LIVE-REPLAY-PROOF-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.replay_proof import ReplayProofRunner, ReplayProofRecord


def test_import_runner():
    from framework.replay_proof import ReplayProofRunner
    assert callable(ReplayProofRunner)


def test_run_returns_record():
    r = ReplayProofRunner().run()
    assert isinstance(r, ReplayProofRecord)


def test_total_traces_5():
    r = ReplayProofRunner().run()
    assert r.total_traces == 5


def test_replayable_count_at_least_2():
    r = ReplayProofRunner().run()
    assert r.replayable_count >= 2


def test_priority_distribution_keys():
    r = ReplayProofRunner().run()
    valid = {"high", "medium", "low", "n/a"}
    assert all(k in valid for k in r.priority_distribution)


def test_emit_artifact(tmp_path):
    runner = ReplayProofRunner()
    r = runner.run()
    path = runner.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["total_traces"] == 5
    assert "replayable_count" in data
    assert "priority_distribution" in data
    assert "rows" in data
