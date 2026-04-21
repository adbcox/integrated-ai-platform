"""Seam tests for LACE1-P14-MINI-TRANCHE-IMPLEMENTATION-SEAM-1 (MT-RETRIEVAL-ENRICHMENT)."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.retrieval_enrichment_substrate import (
    RetrievalEnrichmentSubstrate,
    RetrievalEnrichmentRecord,
    EnrichedCandidate,
    EntitySignal,
)


def _enrich(tokens=None, paths=None, scores=None):
    tokens = tokens or ["improve", "ExecutorFactory"]
    paths = paths or ["framework/code_executor.py", "docs/roadmap/items/RM-GOV-001.yaml"]
    return RetrievalEnrichmentSubstrate().enrich(tokens, paths, base_scores=scores or {})


def test_import_substrate():
    from framework.retrieval_enrichment_substrate import RetrievalEnrichmentSubstrate
    assert callable(RetrievalEnrichmentSubstrate)


def test_enrich_returns_record():
    r = _enrich()
    assert isinstance(r, RetrievalEnrichmentRecord)


def test_enriched_candidates_count():
    r = _enrich(paths=["framework/scheduler.py", "framework/worker_runtime.py", "docs/x.md"])
    assert len(r.enriched_candidates) == 3
    assert all(isinstance(c, EnrichedCandidate) for c in r.enriched_candidates)


def test_domain_bonus_docs_negative():
    r = _enrich(paths=["docs/roadmap/items/RM-GOV-001.yaml"])
    assert r.enriched_candidates[0].domain_bonus < 0


def test_domain_bonus_framework_positive():
    r = _enrich(paths=["framework/scheduler.py"])
    assert r.enriched_candidates[0].domain_bonus > 0


def test_emit_writes_json(tmp_path):
    substrate = RetrievalEnrichmentSubstrate()
    r = substrate.enrich(["improve", "WorkerRuntime"], ["framework/worker_runtime.py"])
    path = substrate.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "record_id" in data
    assert "enriched_candidates" in data
    assert len(data["enriched_candidates"]) == 1
