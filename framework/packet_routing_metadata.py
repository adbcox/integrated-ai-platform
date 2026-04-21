"""LEDT-P6: Packet routing metadata schema defaulting to local_first execution."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


VALID_EXECUTORS = frozenset({"local_first", "claude_only", "hard_stop_only"})
ROUTING_POLICY_VERSION = "ledt-v1"


@dataclass
class PacketRoutingMetadata:
    metadata_id: str
    packet_id: str
    preferred_executor: str = "local_first"
    eligibility_id: Optional[str] = None
    route_decision_id: Optional[str] = None
    local_exec_allowed: bool = True
    claude_fallback_allowed: bool = False
    routing_policy_version: str = ROUTING_POLICY_VERSION
    created_at: str = ""

    def __post_init__(self):
        if self.preferred_executor not in VALID_EXECUTORS:
            raise ValueError(f"preferred_executor={self.preferred_executor!r} not in {sorted(VALID_EXECUTORS)}")
        if not self.created_at:
            object.__setattr__(self, "created_at", _iso_now())


class PacketRoutingMetadataBuilder:
    """Builds PacketRoutingMetadata records defaulting to local_first."""

    def build(
        self,
        packet_id: str,
        eligibility_id: Optional[str] = None,
        route_decision_id: Optional[str] = None,
        override_executor: Optional[str] = None,
    ) -> PacketRoutingMetadata:
        executor = override_executor if override_executor else "local_first"
        claude_allowed = executor == "claude_only"
        local_allowed = executor != "hard_stop_only"
        return PacketRoutingMetadata(
            metadata_id=f"META-{_ts()}-{packet_id[:16].replace(' ', '_')}",
            packet_id=packet_id,
            preferred_executor=executor,
            eligibility_id=eligibility_id,
            route_decision_id=route_decision_id,
            local_exec_allowed=local_allowed,
            claude_fallback_allowed=claude_allowed,
            routing_policy_version=ROUTING_POLICY_VERSION,
            created_at=_iso_now(),
        )

    def emit(self, records: List[PacketRoutingMetadata], artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "packet_routing_metadata_proof.json"
        local_first_count = sum(1 for r in records if r.preferred_executor == "local_first")
        claude_only_count = sum(1 for r in records if r.preferred_executor == "claude_only")
        total = len(records)
        out_path.write_text(
            json.dumps({
                "sample_count": total,
                "local_first_count": local_first_count,
                "claude_only_count": claude_only_count,
                "local_first_rate": round(local_first_count / total, 4) if total else 0.0,
                "records": [asdict(r) for r in records],
                "proved_at": _iso_now(),
            }, indent=2),
            encoding="utf-8",
        )
        return str(out_path)


__all__ = ["PacketRoutingMetadata", "PacketRoutingMetadataBuilder", "ROUTING_POLICY_VERSION"]
