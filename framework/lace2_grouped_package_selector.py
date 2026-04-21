"""LACE2-P13: Evidence-adjusted LACE2 mini-tranche selector via RM-GOV-003 scoring."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from roadmap_governance.planner_service import _collect_shared_touch_surfaces

assert callable(_collect_shared_touch_surfaces), "INTERFACE MISMATCH: _collect_shared_touch_surfaces"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


CANDIDATES = [
    {
        "tranche_id": "MT2-RETRY-LOOP-WIRING",
        "description": "Wire retry loop around real benchmark runner; prove first vs retry delta",
        "base_score": 0.85,
        "replay_failure_boost": True,
        "ratification_boost": False,
    },
    {
        "tranche_id": "MT2-RETRIEVAL-STAGE4-WIRING",
        "description": "Wire live retrieval enrichment into stage_rag4 bounded proof path",
        "base_score": 0.88,
        "replay_failure_boost": False,
        "ratification_boost": True,
    },
    {
        "tranche_id": "MT2-TRACE-REPLAY-PIPELINE",
        "description": "Connect enriched traces to replay gate with bounded pipeline proof",
        "base_score": 0.87,
        "replay_failure_boost": True,
        "ratification_boost": False,
    },
]


@dataclass
class CandidateScore:
    tranche_id: str
    description: str
    base_score: float
    shared_touch_count: int
    replay_failure_boost: float
    ratification_boost: float
    final_score: float


@dataclass
class Lace2GroupedPackageSelection:
    selection_id: str
    candidates: List[CandidateScore]
    selected_tranche: str
    selection_rationale: str
    lace2_verdict: str
    total_failures: int
    scored_at: str
    artifact_path: Optional[str] = None


class Lace2GroupedPackageSelector:
    """Scores three LACE2 mini-tranche candidates using RM-GOV-003 shared-touch + evidence boosts."""

    def _load_evidence(self) -> Dict:
        base = Path("artifacts/expansion/LACE2")
        rat_path = base / "lace2_autonomy_proof_ratification.json"
        mine_path = base / "real_run_failure_patterns.json"

        rat = json.loads(rat_path.read_text(encoding="utf-8")) if rat_path.exists() else {}
        mine = json.loads(mine_path.read_text(encoding="utf-8")) if mine_path.exists() else {}

        return {
            "verdict": rat.get("verdict", "unknown"),
            "total_failures": mine.get("total_failures", 0),
            "replay_not_replayable": mine.get("replay_not_replayable", 0),
        }

    def select(self) -> Lace2GroupedPackageSelection:
        evidence = self._load_evidence()
        verdict = evidence["verdict"]
        replay_failures = evidence["replay_not_replayable"]
        total_failures = evidence["total_failures"]

        confirmed = verdict == "real_local_autonomy_uplift_confirmed"
        has_replay_failures = replay_failures > 0

        scored: List[CandidateScore] = []
        for c in CANDIDATES:
            shared_count = len(_collect_shared_touch_surfaces([c["tranche_id"]]))
            replay_boost = 0.05 if (c["replay_failure_boost"] and has_replay_failures) else 0.0
            rat_boost = 0.03 if (c["ratification_boost"] and confirmed) else 0.0
            final = round(c["base_score"] + 0.05 * shared_count + replay_boost + rat_boost, 4)
            scored.append(CandidateScore(
                tranche_id=c["tranche_id"],
                description=c["description"],
                base_score=c["base_score"],
                shared_touch_count=shared_count,
                replay_failure_boost=replay_boost,
                ratification_boost=rat_boost,
                final_score=final,
            ))

        scored.sort(key=lambda x: x.final_score, reverse=True)
        winner = scored[0]

        return Lace2GroupedPackageSelection(
            selection_id=f"LACE2-PKG-SEL-{_ts()}",
            candidates=scored,
            selected_tranche=winner.tranche_id,
            selection_rationale=(
                f"{winner.tranche_id} selected with final_score={winner.final_score}; "
                f"replay_failure_boost={winner.replay_failure_boost}, "
                f"ratification_boost={winner.ratification_boost}"
            ),
            lace2_verdict=verdict,
            total_failures=total_failures,
            scored_at=_iso_now(),
        )

    def emit(self, record: Lace2GroupedPackageSelection, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "lace2_grouped_package_selection.json"
        out_path.write_text(
            json.dumps({
                "selection_id": record.selection_id,
                "candidates": [asdict(c) for c in record.candidates],
                "selected_tranche": record.selected_tranche,
                "selection_rationale": record.selection_rationale,
                "lace2_verdict": record.lace2_verdict,
                "total_failures": record.total_failures,
                "scored_at": record.scored_at,
            }, indent=2),
            encoding="utf-8",
        )
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["CandidateScore", "Lace2GroupedPackageSelection", "Lace2GroupedPackageSelector"]
