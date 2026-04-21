"""LACE2-P2-LIVE-RETRIEVAL-WIRING-SEAM-1: wire repo understanding and retrieval enrichment into live proof path."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from framework.repo_understanding_substrate import RepoUnderstandingSubstrate, RepoUnderstandingSummary
from framework.retrieval_enrichment_substrate import RetrievalEnrichmentSubstrate, RetrievalEnrichmentRecord

assert "total_files_scanned" in RepoUnderstandingSummary.__dataclass_fields__, \
    "INTERFACE MISMATCH: RepoUnderstandingSummary.total_files_scanned"
assert "top_files_by_symbol_count" in RepoUnderstandingSummary.__dataclass_fields__, \
    "INTERFACE MISMATCH: RepoUnderstandingSummary.top_files_by_symbol_count"
assert callable(RetrievalEnrichmentSubstrate), "INTERFACE MISMATCH: RetrievalEnrichmentSubstrate not callable"
assert "enriched_candidates" in RetrievalEnrichmentRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: RetrievalEnrichmentRecord.enriched_candidates"

_TOKEN_SPLIT_RE = re.compile(r"[^a-zA-Z0-9]+")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class LiveRetrievalProofRecord:
    proof_id: str
    task_description: str
    query_tokens: List[str]
    total_files_scanned: int
    total_symbols: int
    top_candidate_paths: List[str]
    entity_names: List[str]
    enriched_top_paths: List[str]
    enriched_at: str
    artifact_path: Optional[str] = None


class LiveRetrievalProofRunner:
    """Wires RepoUnderstandingSubstrate + RetrievalEnrichmentSubstrate into a live bounded proof."""

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = Path(repo_root)

    def run(
        self,
        task_description: str,
        *,
        max_files: int = 200,
        top_n: int = 10,
    ) -> LiveRetrievalProofRecord:
        summary: RepoUnderstandingSummary = RepoUnderstandingSubstrate(self._repo_root).scan(
            max_files=max_files
        )

        top_candidate_paths: List[str] = [
            entry["path"] if isinstance(entry, dict) else entry.path
            for entry in summary.top_files_by_symbol_count[:top_n]
        ]

        tokens = [t for t in _TOKEN_SPLIT_RE.split(task_description) if len(t) > 2]

        enrich_record: RetrievalEnrichmentRecord = RetrievalEnrichmentSubstrate().enrich(
            tokens,
            top_candidate_paths,
        )

        enriched_top_paths: List[str] = [
            c.path if hasattr(c, "path") else c["path"]
            for c in enrich_record.enriched_candidates[:top_n]
        ]

        return LiveRetrievalProofRecord(
            proof_id=f"LRP-LACE2-{_ts()}",
            task_description=task_description,
            query_tokens=tokens,
            total_files_scanned=summary.total_files_scanned,
            total_symbols=summary.total_symbols,
            top_candidate_paths=top_candidate_paths,
            entity_names=enrich_record.entity_names,
            enriched_top_paths=enriched_top_paths,
            enriched_at=_iso_now(),
        )

    def emit(self, record: LiveRetrievalProofRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "live_retrieval_proof.json"
        payload = {
            "proof_id": record.proof_id,
            "task_description": record.task_description,
            "query_tokens": record.query_tokens,
            "total_files_scanned": record.total_files_scanned,
            "total_symbols": record.total_symbols,
            "top_candidate_paths": record.top_candidate_paths,
            "entity_names": record.entity_names,
            "enriched_top_paths": record.enriched_top_paths,
            "enriched_at": record.enriched_at,
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["LiveRetrievalProofRecord", "LiveRetrievalProofRunner"]
