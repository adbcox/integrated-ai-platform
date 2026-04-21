"""LEDT-P8: Planner preference schema defaulting to local_first with explicit Claude conditions."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class PlannerPreferenceRecord:
    preference_id: str
    campaign_id: str
    default_executor_preference: str
    claude_execution_allowed: bool
    claude_execution_conditions: List[str]
    rationale: str
    upstream_evidence_ids: List[str]
    issued_at: str


class PlannerPreferenceBuilder:
    """Builds planner preference records defaulting to local_first."""

    def build(
        self,
        campaign_id: str,
        rationale: str,
        upstream_evidence_ids: List[str],
        claude_allowed: bool = False,
        claude_conditions: Optional[List[str]] = None,
    ) -> PlannerPreferenceRecord:
        if claude_allowed and (not claude_conditions):
            raise ValueError(
                "claude_execution_conditions must be non-empty when claude_allowed=True"
            )
        if not upstream_evidence_ids:
            raise ValueError("upstream_evidence_ids must be non-empty")

        return PlannerPreferenceRecord(
            preference_id=f"PREF-{_ts()}-{campaign_id[:16].replace(' ', '_')}",
            campaign_id=campaign_id,
            default_executor_preference="local_first",
            claude_execution_allowed=claude_allowed,
            claude_execution_conditions=claude_conditions or [],
            rationale=rationale,
            upstream_evidence_ids=upstream_evidence_ids,
            issued_at=_iso_now(),
        )

    def emit(self, record: PlannerPreferenceRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "planner_preference_proof.json"
        out_path.write_text(
            json.dumps(asdict(record), indent=2),
            encoding="utf-8",
        )
        return str(out_path)

    def emit_batch(self, records: List[PlannerPreferenceRecord], artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "planner_preference_proof.json"
        local_first_rate = sum(
            1 for r in records if r.default_executor_preference == "local_first"
        ) / len(records) if records else 0.0
        out_path.write_text(
            json.dumps({
                "sample_count": len(records),
                "local_first_rate": round(local_first_rate, 4),
                "claude_allowed_count": sum(1 for r in records if r.claude_execution_allowed),
                "records": [asdict(r) for r in records],
                "proved_at": _iso_now(),
            }, indent=2),
            encoding="utf-8",
        )
        return str(out_path)


__all__ = ["PlannerPreferenceRecord", "PlannerPreferenceBuilder"]
