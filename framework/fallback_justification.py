"""LEDT-P5: Typed fallback justification artifact requiring evidence and class."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from framework.exec_route_decision import ExecRouteDecision

assert "route" in ExecRouteDecision.__dataclass_fields__, \
    "INTERFACE MISMATCH: ExecRouteDecision.route"
assert "fallback_authorization_reason" in ExecRouteDecision.__dataclass_fields__, \
    "INTERFACE MISMATCH: ExecRouteDecision.fallback_authorization_reason"

VALID_JUSTIFICATION_CLASSES = frozenset({
    "tool_unavailable",
    "scope_exceeded",
    "validation_failure",
    "preflight_failed",
    "manual_override",
})


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class FallbackJustificationRecord:
    justification_id: str
    packet_id: str
    route_decision_id: str
    justification_class: str
    evidence: str
    avoidable_in_future: bool
    mitigation_hint: str
    recorded_at: str


class FallbackJustificationWriter:
    """Records why Claude fallback was used; requires non-narrative evidence."""

    def record(
        self,
        decision: ExecRouteDecision,
        justification_class: str,
        evidence: str,
        avoidable: bool,
        hint: str,
    ) -> FallbackJustificationRecord:
        if decision.route != "claude_fallback":
            raise ValueError(
                f"FallbackJustificationWriter.record() requires route='claude_fallback', "
                f"got route={decision.route!r}"
            )
        if justification_class not in VALID_JUSTIFICATION_CLASSES:
            raise ValueError(
                f"justification_class={justification_class!r} not in {sorted(VALID_JUSTIFICATION_CLASSES)}"
            )
        if not evidence or not evidence.strip():
            raise ValueError("evidence must be non-empty")

        return FallbackJustificationRecord(
            justification_id=f"JUST-{_ts()}-{decision.packet_id[:12].replace(' ', '_')}",
            packet_id=decision.packet_id,
            route_decision_id=decision.decision_id,
            justification_class=justification_class,
            evidence=evidence,
            avoidable_in_future=avoidable,
            mitigation_hint=hint,
            recorded_at=_iso_now(),
        )

    def emit(self, records: List[FallbackJustificationRecord], artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "fallback_justification_proof.json"
        class_dist: Dict[str, int] = {}
        for r in records:
            class_dist[r.justification_class] = class_dist.get(r.justification_class, 0) + 1
        avoidable_count = sum(1 for r in records if r.avoidable_in_future)
        out_path.write_text(
            json.dumps({
                "sample_count": len(records),
                "avoidable_count": avoidable_count,
                "class_distribution": class_dist,
                "records": [asdict(r) for r in records],
                "proved_at": _iso_now(),
            }, indent=2),
            encoding="utf-8",
        )
        return str(out_path)


__all__ = ["FallbackJustificationRecord", "FallbackJustificationWriter", "VALID_JUSTIFICATION_CLASSES"]
