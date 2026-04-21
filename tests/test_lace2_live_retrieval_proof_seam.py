"""Seam tests for LACE2-P2-LIVE-RETRIEVAL-WIRING-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.live_retrieval_proof import LiveRetrievalProofRunner, LiveRetrievalProofRecord


def _runner():
    return LiveRetrievalProofRunner(REPO_ROOT)


def test_import_runner():
    from framework.live_retrieval_proof import LiveRetrievalProofRunner
    assert callable(LiveRetrievalProofRunner)


def test_run_returns_record():
    r = _runner().run("add guard clause to WorkerRuntime", max_files=50, top_n=5)
    assert isinstance(r, LiveRetrievalProofRecord)


def test_top_candidate_paths_nonempty():
    r = _runner().run("improve ExecutorFactory", max_files=50, top_n=5)
    assert len(r.top_candidate_paths) >= 1


def test_enriched_top_paths_nonempty():
    r = _runner().run("add guard clause to WorkerRuntime", max_files=50, top_n=5)
    assert len(r.enriched_top_paths) >= 1


def test_total_files_scanned_positive():
    r = _runner().run("replace scheduler timeout", max_files=50, top_n=5)
    assert r.total_files_scanned > 0


def test_emit_writes_json(tmp_path):
    runner = _runner()
    r = runner.run("add test for job schema", max_files=50, top_n=5)
    path = runner.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "proof_id" in data
    assert "top_candidate_paths" in data
    assert "enriched_top_paths" in data
    assert data["total_files_scanned"] > 0
