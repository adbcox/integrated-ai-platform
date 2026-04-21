"""Seam tests for LACE2-P3-LIVE-DECOMP-HANDOFF-PROOF-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.decomp_handoff_proof import DecompHandoffProofRunner, DecompHandoffProofRecord

_TARGET_FILES = ["framework/scheduler.py", "framework/job_schema.py"]
_DESC = "add guard clause to scheduler job submission"


def test_import_runner():
    from framework.decomp_handoff_proof import DecompHandoffProofRunner
    assert callable(DecompHandoffProofRunner)


def test_run_returns_record():
    r = DecompHandoffProofRunner().run(_DESC, _TARGET_FILES)
    assert isinstance(r, DecompHandoffProofRecord)


def test_subtask_count_matches_file_count():
    r = DecompHandoffProofRunner().run(_DESC, _TARGET_FILES)
    assert r.subtask_count == len(_TARGET_FILES)


def test_total_orders_matches_subtask_count():
    r = DecompHandoffProofRunner().run(_DESC, _TARGET_FILES)
    assert r.total_orders == r.subtask_count


def test_handoff_policy_sequential():
    r = DecompHandoffProofRunner().run(_DESC, _TARGET_FILES)
    assert r.handoff_policy == "sequential"


def test_emit_artifact(tmp_path):
    runner = DecompHandoffProofRunner()
    r = runner.run(_DESC, _TARGET_FILES)
    path = runner.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "bundle_id" in data
    assert "handoff_id" in data
    assert data["total_orders"] > 0
