"""LEDT-P4: Typed execution route decision surface."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.local_exec_eligibility_contract import LocalExecEligibilityRecord
from framework.local_exec_preflight import LocalExecPreflightReport

assert "eligible" in LocalExecEligibilityRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: LocalExecEligibilityRecord.eligible"
assert "disqualifiers" in LocalExecEligibilityRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: LocalExecEligibilityRecord.disqualifiers"
assert "overall_ready" in LocalExecPreflightReport.__dataclass_fields__, \
    "INTERFACE MISMATCH: LocalExecPreflightReport.overall_ready"

VALID_ROUTES = {"local_execute", "claude_fallback", "hard_stop"}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class ExecRouteDecision:
    decision_id: str
    packet_id: str
    route: str
    eligibility_passed: bool
    preflight_passed: bool
    decision_reason: str
    fallback_authorized: bool
    fallback_authorization_reason: Optional[str]
    decided_at: str


class ExecRouteDecider:
    """Chooses local_execute / claude_fallback / hard_stop from eligibility + preflight."""

    def decide(
        self,
        eligibility: LocalExecEligibilityRecord,
        preflight: LocalExecPreflightReport,
    ) -> ExecRouteDecision:
        hard_stop_disqs = [d for d in eligibility.disqualifiers if "hard_stop" in d.lower()]

        if not eligibility.eligible and hard_stop_disqs:
            route = "hard_stop"
            reason = f"disqualifier forces hard stop: {hard_stop_disqs[0]}"
            fallback_auth = False
            fallback_reason = None
        elif eligibility.eligible and preflight.overall_ready:
            route = "local_execute"
            reason = "eligibility passed and preflight ready"
            fallback_auth = False
            fallback_reason = None
        else:
            route = "claude_fallback"
            fallback_auth = True
            if not eligibility.eligible:
                fallback_reason = f"eligibility failed: {eligibility.disqualifiers[0] if eligibility.disqualifiers else 'unknown'}"
            else:
                fallback_reason = "preflight not ready: code_executor or validation commands missing"
            reason = f"local execution not viable; {fallback_reason}"

        return ExecRouteDecision(
            decision_id=f"ROUTE-{_ts()}-{eligibility.packet_id[:12].replace(' ', '_')}",
            packet_id=eligibility.packet_id,
            route=route,
            eligibility_passed=eligibility.eligible,
            preflight_passed=preflight.overall_ready,
            decision_reason=reason,
            fallback_authorized=fallback_auth,
            fallback_authorization_reason=fallback_reason,
            decided_at=_iso_now(),
        )

    def emit(self, decisions: List[ExecRouteDecision], artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "route_decision_proof.json"
        local_count = sum(1 for d in decisions if d.route == "local_execute")
        fallback_count = sum(1 for d in decisions if d.route == "claude_fallback")
        hard_count = sum(1 for d in decisions if d.route == "hard_stop")
        total = len(decisions)
        out_path.write_text(
            json.dumps({
                "sample_count": total,
                "local_execute_count": local_count,
                "claude_fallback_count": fallback_count,
                "hard_stop_count": hard_count,
                "local_execute_rate": round(local_count / total, 4) if total else 0.0,
                "sample_decisions": [asdict(d) for d in decisions],
                "proved_at": _iso_now(),
            }, indent=2),
            encoding="utf-8",
        )
        return str(out_path)


__all__ = ["ExecRouteDecision", "ExecRouteDecider"]
