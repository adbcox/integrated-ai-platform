"""Seam tests for LACE2-P14-MINI-TRANCHE-IMPLEMENTATION-SEAM-1 (MT2-TRACE-REPLAY-PIPELINE)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace2_trace_replay_pipeline import (
    TraceReplayPipelineRunner,
    TraceReplayPipelineRecord,
    PipelineStageResult,
)


def test_import_runner():
    assert callable(TraceReplayPipelineRunner)


def test_run_returns_record():
    r = TraceReplayPipelineRunner().run()
    assert isinstance(r, TraceReplayPipelineRecord)


def test_five_traces():
    r = TraceReplayPipelineRunner().run()
    assert r.total_traces == 5
    assert len(r.pipeline_stages) == 5


def test_at_least_two_replayable():
    r = TraceReplayPipelineRunner().run()
    assert r.replayable_count >= 2


def test_selected_tranche_correct():
    r = TraceReplayPipelineRunner().run()
    assert r.selected_tranche == "MT2-TRACE-REPLAY-PIPELINE"


def test_emit_artifact(tmp_path):
    runner = TraceReplayPipelineRunner()
    r = runner.run()
    path = runner.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["total_traces"] == 5
    assert data["selected_tranche"] == "MT2-TRACE-REPLAY-PIPELINE"
    assert data["replayable_count"] >= 2
    assert len(data["pipeline_stages"]) == 5
