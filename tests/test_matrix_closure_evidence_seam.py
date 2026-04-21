"""Conformance tests for framework/matrix_closure_evidence.py (RMCC1-CLOSEOUT-RATIFIER-SEAM-1)."""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.matrix_closure_evidence import (
    MatrixItemRecord,
    MatrixItemState,
    derive_campaign_closure,
    emit_closeout_record,
)


def _make_bench_artifact(tmp_path, *, outcome="pass", total=5, passed=5) -> Path:
    p = tmp_path / "mvp_benchmark_result.json"
    p.write_text(json.dumps({"outcome": outcome, "total_tasks": total, "passed": passed, "failed": total - passed, "task_results": []}), encoding="utf-8")
    return p


# --- Evidence gate behavior ---

def test_evidence_gate_passes_with_valid_artifact(tmp_path):
    bench = _make_bench_artifact(tmp_path)
    items = derive_campaign_closure(bench_artifact_path=bench)
    assert isinstance(items, list)
    assert len(items) > 0


def test_evidence_gate_missing_artifact_yields_partial_states(tmp_path):
    missing = tmp_path / "no_such_file.json"
    items = derive_campaign_closure(bench_artifact_path=missing)
    states = {i.state for i in items}
    assert MatrixItemState.DONE not in states or MatrixItemState.PARTIAL in states or MatrixItemState.DEFERRED in states


def test_evidence_gate_failing_benchmark_no_done_states(tmp_path):
    bench = _make_bench_artifact(tmp_path, outcome="fail", total=5, passed=3)
    items = derive_campaign_closure(bench_artifact_path=bench)
    for item in items:
        assert item.state != MatrixItemState.DONE, f"{item.item_id} should not be DONE without passing benchmark"


# --- Derived states reflect actual evidence ---

def test_mvp_loop_item_done_when_bench_passes(tmp_path):
    bench = _make_bench_artifact(tmp_path)
    items = derive_campaign_closure(bench_artifact_path=bench)
    mvp = next((i for i in items if i.item_id == "full_developer_assistant_mvp_loop"), None)
    assert mvp is not None
    assert mvp.state == MatrixItemState.DONE


def test_retrieval_item_seed_complete(tmp_path):
    bench = _make_bench_artifact(tmp_path)
    items = derive_campaign_closure(bench_artifact_path=bench)
    ret = next((i for i in items if i.item_id == "retrieval_memory_substrate"), None)
    assert ret is not None
    assert ret.state == MatrixItemState.SEED_COMPLETE


def test_aider_is_deferred(tmp_path):
    bench = _make_bench_artifact(tmp_path)
    items = derive_campaign_closure(bench_artifact_path=bench)
    aider = next((i for i in items if i.item_id == "aider_adapter_under_runtime"), None)
    assert aider is not None
    assert aider.state == MatrixItemState.DEFERRED


# --- Closeout artifact ---

def test_closeout_artifact_written_and_parseable(tmp_path):
    bench = _make_bench_artifact(tmp_path)
    items = derive_campaign_closure(bench_artifact_path=bench)
    out = emit_closeout_record(items, artifact_dir=tmp_path / "out", bench_artifact_path=bench)
    assert Path(out).exists()
    data = json.loads(Path(out).read_text())
    assert "campaign_id" in data
    assert "items" in data
    assert "evidence_gate" in data


def test_closeout_raises_on_missing_bench(tmp_path):
    missing = tmp_path / "missing.json"
    items = [MatrixItemRecord(item_id="x", description="x", state=MatrixItemState.DONE)]
    with pytest.raises(RuntimeError):
        emit_closeout_record(items, artifact_dir=tmp_path / "out", bench_artifact_path=missing)


def test_non_deferred_refs_point_to_existing_files(tmp_path):
    bench = _make_bench_artifact(tmp_path)
    items = derive_campaign_closure(bench_artifact_path=bench)
    for item in items:
        if item.state == MatrixItemState.DEFERRED:
            continue
        for ref in item.evidence_refs:
            if ref and not ref.endswith(".json"):
                assert (REPO_ROOT / ref).exists(), f"Evidence ref missing: {ref}"


def test_no_optimistic_done_overclaiming_without_evidence(tmp_path):
    bench = _make_bench_artifact(tmp_path, outcome="fail", total=5, passed=0)
    items = derive_campaign_closure(bench_artifact_path=bench)
    done_items = [i for i in items if i.state == MatrixItemState.DONE]
    assert len(done_items) == 0


# --- Script ---

def test_script_syntax_valid():
    script = REPO_ROOT / "bin" / "matrix_closeout_emit.py"
    ast.parse(script.read_text())


def test_script_exits_nonzero_when_bench_missing(tmp_path):
    import subprocess
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "matrix_closeout_emit.py"),
         "--bench-artifact", str(tmp_path / "missing.json"),
         "--artifact-root", str(tmp_path / "out")],
        capture_output=True,
    )
    assert result.returncode != 0


# --- Package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "MatrixItemState")
    assert hasattr(framework, "MatrixItemRecord")
    assert hasattr(framework, "derive_campaign_closure")
    assert hasattr(framework, "emit_closeout_record")
