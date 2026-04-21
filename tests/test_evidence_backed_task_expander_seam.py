"""Conformance tests for framework/evidence_backed_task_expander.py (LARAC2-SAFE-TASK-EXPANSION-SEAM-1)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.evidence_backed_task_expander import (
    EXPANSION_CANDIDATES, TaskExpansionDecision, TaskExpansionRecord,
    EvidenceBackedTaskExpander, emit_expansion_record
)
from framework.task_class_benchmark import TaskClassBenchmarkReport, TaskClassBenchmarkEntry
from framework.unified_local_metrics import UnifiedLocalMetrics


def _bench(classes, pass_rate=1.0, tasks_per_class=5):
    entries = tuple(
        TaskClassBenchmarkEntry(
            task_class=tc, total=tasks_per_class,
            passed=int(pass_rate * tasks_per_class),
            failed=tasks_per_class - int(pass_rate * tasks_per_class),
            pass_rate=pass_rate,
        )
        for tc in classes
    )
    total = tasks_per_class * len(classes)
    return TaskClassBenchmarkReport(
        entries=entries, total_tasks=total,
        total_passed=int(pass_rate * total), total_failed=total - int(pass_rate * total),
        overall_pass_rate=pass_rate, evaluated_at="now", artifact_path=None
    )


def _metrics(first_pass=0.85, failure_rate=0.10):
    return UnifiedLocalMetrics(
        first_pass_rate=first_pass, failure_rate=failure_rate,
        total_retry_burden=0, readiness_verdict="ready",
        task_classes_total=3, computed_at="now",
    )


# --- import and type ---

def test_import_evidence_backed_task_expander():
    assert callable(EvidenceBackedTaskExpander)


def test_returns_task_expansion_record():
    r = EvidenceBackedTaskExpander().evaluate()
    assert isinstance(r, TaskExpansionRecord)


# --- fields ---

def test_record_fields_present():
    r = EvidenceBackedTaskExpander().evaluate()
    assert hasattr(r, "decisions")
    assert hasattr(r, "expansion_candidates")
    assert hasattr(r, "evaluated_at")


# --- default insufficient_evidence ---

def test_no_benchmark_insufficient_evidence():
    r = EvidenceBackedTaskExpander().evaluate()
    for d in r.decisions:
        assert d.decision == "insufficient_evidence"


def test_no_metrics_insufficient_evidence():
    bench = _bench(["bug_fix"], tasks_per_class=5)
    r = EvidenceBackedTaskExpander().evaluate(benchmark_report=bench, unified_metrics=None)
    for d in r.decisions:
        assert d.decision == "insufficient_evidence"


def test_not_benchmarked_insufficient_evidence():
    bench = _bench(["text_replacement"])
    r = EvidenceBackedTaskExpander().evaluate(
        benchmark_report=bench, unified_metrics=_metrics(),
        candidates=["bug_fix"]
    )
    assert r.decisions[0].decision == "insufficient_evidence"
    assert "bug_fix" in r.decisions[0].rationale


# --- expansion_candidates ---

def test_expansion_candidates_constant():
    assert "bug_fix" in EXPANSION_CANDIDATES
    assert "narrow_test_update" in EXPANSION_CANDIDATES


def test_custom_candidates():
    r = EvidenceBackedTaskExpander().evaluate(candidates=["text_replacement"])
    assert r.expansion_candidates == ("text_replacement",)


# --- decision values ---

def test_decision_is_valid():
    r = EvidenceBackedTaskExpander().evaluate()
    for d in r.decisions:
        assert d.decision in {"expand", "insufficient_evidence", "not_ready"}


# --- does NOT mutate SAFE_TASK_KINDS ---

def test_no_safe_task_kinds_mutation():
    from framework.mvp_coding_loop import SAFE_TASK_KINDS
    original = set(SAFE_TASK_KINDS)
    EvidenceBackedTaskExpander().evaluate(
        benchmark_report=_bench(["bug_fix"], tasks_per_class=5),
        unified_metrics=_metrics(),
        candidates=["bug_fix"],
    )
    assert set(SAFE_TASK_KINDS) == original


# --- package surface ---

def test_package_surface():
    import framework
    assert hasattr(framework, "EvidenceBackedTaskExpander")
    assert hasattr(framework, "TaskExpansionRecord")
    assert hasattr(framework, "TaskExpansionDecision")
    assert hasattr(framework, "EXPANSION_CANDIDATES")
