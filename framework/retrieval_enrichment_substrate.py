"""LACE1-P14-MINI-TRANCHE-IMPLEMENTATION-SEAM-1: MT-RETRIEVAL-ENRICHMENT substrate.

Enriches stage_rag4 retrieval candidates with additional entity definition signals
and domain-aware bonuses, surfaced as a typed substrate for downstream consumers.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set
import json

# Resolve repo root so we can read candidate files
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "bin"))

# Import entity helpers from stage_rag4; assert interface presence
try:
    from stage_rag4_plan_probe import _extract_entities, _entity_definition_score  # type: ignore[import]
    assert callable(_extract_entities), "INTERFACE MISMATCH: _extract_entities not callable"
    assert callable(_entity_definition_score), "INTERFACE MISMATCH: _entity_definition_score not callable"
    _RAG4_AVAILABLE = True
except ImportError:
    _RAG4_AVAILABLE = False

_DOMAIN_BONUS_TABLE: Dict[str, float] = {
    "framework": 0.5,
    "bin": 0.3,
    "tests": 0.2,
    "docs": -1.0,
    "artifacts": -2.0,
    "governance": -0.5,
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass(frozen=True)
class EntitySignal:
    entity_name: str
    signal_type: str      # "class_definition" | "function_definition" | "variable_assignment" | "none"
    score_contribution: float


@dataclass(frozen=True)
class EnrichedCandidate:
    path: str
    base_score: float
    entity_signals: List[EntitySignal]
    entity_boost: float
    domain_bonus: float
    enriched_score: float


@dataclass
class RetrievalEnrichmentRecord:
    record_id: str
    query_tokens: List[str]
    entity_names: List[str]
    enriched_candidates: List[EnrichedCandidate]
    enriched_at: str
    artifact_path: Optional[str] = None


class RetrievalEnrichmentSubstrate:
    """Enrich a set of candidate paths with entity signals and domain bonuses."""

    def enrich(
        self,
        query_tokens: List[str],
        candidate_paths: List[str],
        *,
        base_scores: Optional[Dict[str, float]] = None,
    ) -> RetrievalEnrichmentRecord:
        if base_scores is None:
            base_scores = {}

        entity_names: Set[str] = set()
        if _RAG4_AVAILABLE and query_tokens:
            entity_names = _extract_entities(query_tokens)

        enriched: List[EnrichedCandidate] = []
        for path in candidate_paths:
            base = base_scores.get(path, 0.0)
            signals = self._compute_entity_signals(path, entity_names)
            entity_boost = sum(s.score_contribution for s in signals)
            domain_bonus = self._domain_bonus(path)
            enriched_score = round(base + entity_boost + domain_bonus, 4)
            enriched.append(EnrichedCandidate(
                path=path,
                base_score=base,
                entity_signals=signals,
                entity_boost=round(entity_boost, 4),
                domain_bonus=round(domain_bonus, 4),
                enriched_score=enriched_score,
            ))

        enriched.sort(key=lambda c: c.enriched_score, reverse=True)

        return RetrievalEnrichmentRecord(
            record_id=f"RE-{_ts()}",
            query_tokens=list(query_tokens),
            entity_names=sorted(entity_names),
            enriched_candidates=enriched,
            enriched_at=_iso_now(),
        )

    def _compute_entity_signals(
        self,
        path: str,
        entity_names: Set[str],
    ) -> List[EntitySignal]:
        if not entity_names:
            return []

        full_path = _REPO_ROOT / path
        if not full_path.exists():
            return [EntitySignal(e, "none", 0.0) for e in entity_names]

        try:
            text = full_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return [EntitySignal(e, "none", 0.0) for e in entity_names]

        signals: List[EntitySignal] = []
        lines = text.splitlines()
        for entity in entity_names:
            el = entity.lower()
            signal_type = "none"
            contrib = 0.0
            for line in lines:
                s = line.lstrip().lower()
                if s.startswith(f"class {el}"):
                    signal_type = "class_definition"
                    contrib = 2.5
                    break
                if s.startswith(f"def {el}"):
                    signal_type = "function_definition"
                    contrib = 2.5
                    break
                if s.startswith(f"{el} ="):
                    signal_type = "variable_assignment"
                    contrib = 1.0
            signals.append(EntitySignal(entity, signal_type, contrib))
        return signals

    def _domain_bonus(self, path: str) -> float:
        first_segment = path.split("/")[0] if "/" in path else path
        return _DOMAIN_BONUS_TABLE.get(first_segment, 0.0)

    def emit(self, record: RetrievalEnrichmentRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / f"{record.record_id}.json"
        payload = {
            "record_id": record.record_id,
            "query_tokens": record.query_tokens,
            "entity_names": record.entity_names,
            "enriched_at": record.enriched_at,
            "enriched_candidates": [asdict(c) for c in record.enriched_candidates],
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = [
    "EntitySignal",
    "EnrichedCandidate",
    "RetrievalEnrichmentRecord",
    "RetrievalEnrichmentSubstrate",
]
