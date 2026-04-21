#!/usr/bin/env python3
"""LACE2-P14: Run MT2-TRACE-REPLAY-PIPELINE proof."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace2_trace_replay_pipeline import TraceReplayPipelineRunner

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE2"


def main() -> None:
    runner = TraceReplayPipelineRunner()
    record = runner.run()
    path = runner.emit(record, ARTIFACT_DIR)
    print(f"pipeline_id:         {record.pipeline_id}")
    print(f"selected_tranche:    {record.selected_tranche}")
    print(f"total_traces:        {record.total_traces}")
    print(f"replayable_count:    {record.replayable_count}")
    print(f"not_replayable:      {record.not_replayable_count}")
    print(f"artifact:            {path}")


if __name__ == "__main__":
    main()
