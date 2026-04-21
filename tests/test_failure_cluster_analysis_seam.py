"""Conformance tests for framework/failure_cluster_analysis.py (LARAC2-FAILURE-CLUSTER-ANALYSIS-SEAM-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.failure_cluster_analysis import (
    FailureCluster, FailureClusterReport, FailureClusterAnalyzer, emit_failure_clusters
)
from framework.local_memory_store import FailurePattern


def _pattern(task_kind="text_replacement", error_type="SyntaxError", summary="unexpected indent", session_id="s"):
    return FailurePattern(
        task_kind=task_kind, error_type=error_type, error_summary=summary,
        target_file_suffix=".py", old_string_prefix="def f",
        recorded_at="2026-01-01T00:00:00+00:00", session_id=session_id,
        recurrence_count=1,
    )


def _store(patterns=None):
    store = MagicMock()
    store.read_failures.return_value = patterns or []
    return store


# --- import and type ---

def test_import_failure_cluster_analyzer():
    assert callable(FailureClusterAnalyzer)


def test_returns_failure_cluster_report():
    r = FailureClusterAnalyzer(memory_store=_store()).analyze()
    assert isinstance(r, FailureClusterReport)


# --- fields ---

def test_report_fields_present():
    r = FailureClusterAnalyzer(memory_store=_store()).analyze()
    assert hasattr(r, "clusters")
    assert hasattr(r, "total_failures_analyzed")
    assert hasattr(r, "top_cluster_key")
    assert hasattr(r, "analyzed_at")


# --- empty failures ---

def test_empty_failures():
    r = FailureClusterAnalyzer(memory_store=_store()).analyze()
    assert r.total_failures_analyzed == 0
    assert r.clusters == []
    assert r.top_cluster_key is None


# --- clustering ---

def test_clusters_same_kind_and_error():
    patterns = [_pattern("text_replacement", "SyntaxError")] * 3
    r = FailureClusterAnalyzer(memory_store=_store(patterns)).analyze()
    assert r.total_failures_analyzed == 3
    assert len(r.clusters) == 1
    assert r.clusters[0].occurrence_count == 3


def test_clusters_different_kinds():
    patterns = [
        _pattern("text_replacement", "SyntaxError"),
        _pattern("helper_insertion", "IndentationError"),
    ]
    r = FailureClusterAnalyzer(memory_store=_store(patterns)).analyze()
    assert len(r.clusters) == 2


def test_top_cluster_is_most_frequent():
    patterns = (
        [_pattern("text_replacement", "SyntaxError")] * 3 +
        [_pattern("helper_insertion", "IndentationError")]
    )
    r = FailureClusterAnalyzer(memory_store=_store(patterns)).analyze()
    assert r.top_cluster_key is not None
    assert "text_replacement" in r.top_cluster_key or "SyntaxError" in r.top_cluster_key


# --- cluster fields ---

def test_cluster_fields():
    patterns = [_pattern("text_replacement", "SyntaxError", "unexpected indent")]
    r = FailureClusterAnalyzer(memory_store=_store(patterns)).analyze()
    c = r.clusters[0]
    assert hasattr(c, "task_kind")
    assert hasattr(c, "error_type")
    assert hasattr(c, "occurrence_count")
    assert hasattr(c, "cluster_key")


# --- emit artifact ---

def test_artifact_written(tmp_path):
    r = FailureClusterAnalyzer(memory_store=_store()).analyze()
    path = emit_failure_clusters(r, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable(tmp_path):
    r = FailureClusterAnalyzer(memory_store=_store()).analyze()
    path = emit_failure_clusters(r, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "total_failures_analyzed" in data
    assert "clusters" in data


# --- store error non-raising ---

def test_store_error_non_raising():
    store = MagicMock()
    store.read_failures.side_effect = RuntimeError("DB error")
    r = FailureClusterAnalyzer(memory_store=store).analyze()
    assert isinstance(r, FailureClusterReport)
    assert r.total_failures_analyzed == 0


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "FailureClusterAnalyzer")
    assert hasattr(framework, "FailureClusterReport")
    assert hasattr(framework, "FailureCluster")
    assert hasattr(framework, "emit_failure_clusters")
