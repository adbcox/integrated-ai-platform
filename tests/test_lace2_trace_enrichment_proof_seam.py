"""Seam tests for LACE2-P5-LIVE-TRACE-ENRICHMENT-WIRING-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.trace_enrichment_proof import TraceEnrichmentProofRunner, TraceEnrichmentProofRecord


def test_import_runner():
    from framework.trace_enrichment_proof import TraceEnrichmentProofRunner
    assert callable(TraceEnrichmentProofRunner)


def test_run_returns_record():
    r = TraceEnrichmentProofRunner().run()
    assert isinstance(r, TraceEnrichmentProofRecord)


def test_input_trace_count_5():
    r = TraceEnrichmentProofRunner().run()
    assert r.input_trace_count == 5


def test_enriched_traces_5():
    r = TraceEnrichmentProofRunner().run()
    assert len(r.enriched_traces) == 5


def test_outcome_distribution_keys():
    r = TraceEnrichmentProofRunner().run()
    valid = {"first_pass_success", "retry_success", "failure", "partial"}
    assert all(k in valid for k in r.outcome_class_distribution)
    assert len(r.outcome_class_distribution) >= 2


def test_emit_artifact(tmp_path):
    runner = TraceEnrichmentProofRunner()
    r = runner.run()
    path = runner.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "outcome_class_distribution" in data
    assert "enriched_traces" in data
    assert len(data["enriched_traces"]) == 5
