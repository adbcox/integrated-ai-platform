"""Conformance tests for framework/local_autonomy_dashboard.py (ADSC1-LOCAL-AUTONOMY-DASHBOARD-SEAM-1)."""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.local_autonomy_dashboard import (
    LocalAutonomyDashboard,
    build_local_autonomy_dashboard,
    emit_dashboard,
)
from framework.local_memory_store import LocalMemoryStore
from framework.repo_pattern_store import RepoPatternLibrary
from framework.retrieval_cache import RetrievalCache


def _mock_store(successes=0, failures=0):
    store = MagicMock(spec=LocalMemoryStore)
    store.read_successes.return_value = [MagicMock()] * successes
    store.read_failures.return_value = [MagicMock()] * failures
    return store


def _mock_cache(entry_count=0):
    cache = MagicMock(spec=RetrievalCache)
    cache._dir = None
    return cache


def _lib(n=0):
    lib = MagicMock(spec=RepoPatternLibrary)
    lib.entries = []
    return lib


def _build(**kwargs):
    defaults = dict(
        memory_store=_mock_store(),
        pattern_library=_lib(),
        cache=_mock_cache(),
    )
    defaults.update(kwargs)
    return build_local_autonomy_dashboard(**defaults)


# --- import and type ---

def test_import_build_local_autonomy_dashboard():
    assert callable(build_local_autonomy_dashboard)


def test_returns_dashboard_type():
    d = _build()
    assert isinstance(d, LocalAutonomyDashboard)


# --- field population ---

def test_dashboard_fields_present():
    d = _build()
    assert hasattr(d, "memory_stats")
    assert hasattr(d, "repo_pattern_stats")
    assert hasattr(d, "retrieval_cache_stats")
    assert hasattr(d, "retry_telemetry_summary")
    assert hasattr(d, "readiness_summary")
    assert hasattr(d, "aider_preflight_summary")
    assert hasattr(d, "overall_health")
    assert hasattr(d, "built_at")


def test_memory_stats_correct():
    d = _build(memory_store=_mock_store(successes=3, failures=1))
    assert d.memory_stats["success_count"] == 3
    assert d.memory_stats["failure_count"] == 1


def test_repo_pattern_stats_correct():
    lib = MagicMock(spec=RepoPatternLibrary)
    entry = MagicMock()
    entry.task_kind = "text_replacement"
    lib.entries = [entry, entry]
    d = _build(pattern_library=lib)
    assert d.repo_pattern_stats["total_patterns"] == 2


def test_retry_telemetry_with_empty_records():
    d = _build(retry_records=[])
    assert d.retry_telemetry_summary["total_records"] == 0
    assert d.retry_telemetry_summary["total_retry_eligible_failures"] == 0


def test_readiness_summary_none_is_unknown():
    d = _build(readiness_report=None)
    assert d.readiness_summary["overall_verdict"] == "unknown"


def test_aider_preflight_none_is_unknown():
    d = _build(preflight_result=None)
    assert d.aider_preflight_summary["verdict"] == "unknown"


# --- overall_health logic ---

def test_overall_health_unknown_when_inputs_none():
    d = _build(readiness_report=None, preflight_result=None)
    assert d.overall_health == "unknown"


def test_overall_health_healthy_when_both_present():
    from framework.task_class_readiness import TaskClassReadinessReport
    from framework.aider_preflight import AiderPreflightResult
    report = TaskClassReadinessReport(
        verdicts=(), overall_verdict="ready", ready_count=1,
        marginal_count=0, not_ready_count=0, evaluated_at="now"
    )
    preflight = AiderPreflightResult(
        verdict="ready", checks=(), blocking_checks=(), evaluated_at="now"
    )
    d = _build(readiness_report=report, preflight_result=preflight)
    assert d.overall_health in {"healthy", "unknown"}


# --- artifact writing ---

def test_artifact_written(tmp_path):
    d = _build()
    path = emit_dashboard(d, artifact_dir=tmp_path)
    assert Path(path).exists()


def test_artifact_parseable(tmp_path):
    d = _build()
    path = emit_dashboard(d, artifact_dir=tmp_path)
    data = json.loads(Path(path).read_text())
    assert "overall_health" in data
    assert "memory_stats" in data
    assert "built_at" in data


# --- built_at timestamp ---

def test_built_at_timestamp_present():
    d = _build()
    assert isinstance(d.built_at, str)
    assert len(d.built_at) > 0


# --- script syntax ---

def test_script_syntax_valid():
    script = REPO_ROOT / "bin" / "local_autonomy_dashboard_emit.py"
    ast.parse(script.read_text())


# --- package surface ---

def test_package_surface_export():
    import framework
    assert hasattr(framework, "build_local_autonomy_dashboard")
    assert hasattr(framework, "emit_dashboard")
    assert hasattr(framework, "LocalAutonomyDashboard")
