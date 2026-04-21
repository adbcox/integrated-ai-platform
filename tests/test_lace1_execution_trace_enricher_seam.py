"""Seam tests for LACE1-P6-EXECUTION-TRACE-ENRICHMENT-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.execution_trace_enricher import ExecutionTraceEnricher, EnrichedTrace
from framework.execution_trace_result_schema import ExecutionTraceResult


def _result(state="complete", items=None):
    return ExecutionTraceResult(result_id="r1", result_state=state,
                                completed_trace_items=items or ["f.py"])


def test_import_enricher():
    from framework.execution_trace_enricher import ExecutionTraceEnricher
    assert callable(ExecutionTraceEnricher)


def test_first_pass_success():
    e = ExecutionTraceEnricher().enrich(_result("complete"), retry_count=0)
    assert e.outcome_class == "first_pass_success"


def test_retry_success():
    e = ExecutionTraceEnricher().enrich(_result("complete"), retry_count=2)
    assert e.outcome_class == "retry_success"


def test_failure_class():
    e = ExecutionTraceEnricher().enrich(_result("failed"), retry_count=0)
    assert e.outcome_class == "failure"


def test_partial_class():
    e = ExecutionTraceEnricher().enrich(_result("partial"), retry_count=0)
    assert e.outcome_class == "partial"


def test_file_change_count():
    e = ExecutionTraceEnricher().enrich(_result("complete", items=["a.py","b.py","c.py"]))
    assert e.file_change_count == 3
