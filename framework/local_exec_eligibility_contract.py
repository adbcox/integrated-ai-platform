"""LEDT-P2: Typed local execution eligibility contract with explicit disqualifiers."""
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
class LocalExecEligibilityInput:
    packet_id: str
    file_scope_count: int
    has_external_api_calls: bool
    requires_broad_redesign: bool
    requires_live_infra_touch: bool
    validation_commands: List[str]


@dataclass
class LocalExecEligibilityRecord:
    eligibility_id: str
    packet_id: str
    file_scope_bounded: bool
    validation_scope_bounded: bool
    no_external_deps: bool
    no_broad_redesign: bool
    no_live_infra_touch: bool
    disqualifiers: List[str]
    eligible: bool
    evaluated_at: str


class LocalExecEligibilityEvaluator:
    """Evaluates whether a bounded packet is eligible for local execution."""

    def evaluate(self, inp: LocalExecEligibilityInput) -> LocalExecEligibilityRecord:
        disqualifiers: List[str] = []

        file_scope_bounded = inp.file_scope_count <= 5
        if not file_scope_bounded:
            disqualifiers.append(f"file_scope_count={inp.file_scope_count} exceeds limit of 5")

        validation_scope_bounded = len(inp.validation_commands) >= 1
        if not validation_scope_bounded:
            disqualifiers.append("no validation_commands specified")

        no_external_deps = not inp.has_external_api_calls
        if not no_external_deps:
            disqualifiers.append("has_external_api_calls=True disqualifies local execution")

        no_broad_redesign = not inp.requires_broad_redesign
        if not no_broad_redesign:
            disqualifiers.append("requires_broad_redesign=True disqualifies local execution")

        no_live_infra_touch = not inp.requires_live_infra_touch
        if not no_live_infra_touch:
            disqualifiers.append("requires_live_infra_touch=True disqualifies local execution")

        eligible = (
            file_scope_bounded
            and validation_scope_bounded
            and no_external_deps
            and no_broad_redesign
            and no_live_infra_touch
        )

        return LocalExecEligibilityRecord(
            eligibility_id=f"ELIG-{_ts()}-{inp.packet_id[:16].replace(' ', '_')}",
            packet_id=inp.packet_id,
            file_scope_bounded=file_scope_bounded,
            validation_scope_bounded=validation_scope_bounded,
            no_external_deps=no_external_deps,
            no_broad_redesign=no_broad_redesign,
            no_live_infra_touch=no_live_infra_touch,
            disqualifiers=disqualifiers,
            eligible=eligible,
            evaluated_at=_iso_now(),
        )

    def emit(self, records: List[LocalExecEligibilityRecord], artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "eligibility_contract_proof.json"
        eligible_count = sum(1 for r in records if r.eligible)
        out_path.write_text(
            json.dumps({
                "sample_count": len(records),
                "eligible_count": eligible_count,
                "disqualified_count": len(records) - eligible_count,
                "sample_records": [asdict(r) for r in records],
                "evaluated_at": _iso_now(),
            }, indent=2),
            encoding="utf-8",
        )
        return str(out_path)


__all__ = [
    "LocalExecEligibilityInput",
    "LocalExecEligibilityRecord",
    "LocalExecEligibilityEvaluator",
]
