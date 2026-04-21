"""AiderPromotionReratifier: decides aider_done or aider_partial from live gate proof (AIDER-FINAL-PROMOTION-RERATIFIER-1)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class AiderPromotionDecision:
    decision: str  # "aider_done" | "aider_partial"
    gate_passed: bool
    wired_checker_called: bool
    propagation_verified: bool
    subprocess_isolation_verified: bool
    blocking_reason: Optional[str]
    decided_at: str
    artifact_path: Optional[str]


class AiderPromotionReratifier:
    """Decides aider_done or aider_partial solely from live_gate_proof evidence."""

    def decide(self, *, live_gate_proof: dict) -> AiderPromotionDecision:
        gate_passed = bool(live_gate_proof.get("gate_passed", False))
        wired_checker_called = bool(live_gate_proof.get("wired_checker_called", False))
        propagation_verified = bool(live_gate_proof.get("propagation_verified", False))
        subprocess_isolation_verified = bool(live_gate_proof.get("subprocess_isolation_verified", False))
        blocking_reason = live_gate_proof.get("blocking_reason")

        all_proven = (
            gate_passed
            and wired_checker_called
            and propagation_verified
            and subprocess_isolation_verified
        )
        decision = "aider_done" if all_proven else "aider_partial"

        if not all_proven and not blocking_reason:
            failing = []
            if not gate_passed:
                failing.append("gate_passed=false")
            if not wired_checker_called:
                failing.append("wired_checker_called=false")
            if not propagation_verified:
                failing.append("propagation_verified=false")
            if not subprocess_isolation_verified:
                failing.append("subprocess_isolation_verified=false")
            blocking_reason = "; ".join(failing)

        return AiderPromotionDecision(
            decision=decision,
            gate_passed=gate_passed,
            wired_checker_called=wired_checker_called,
            propagation_verified=propagation_verified,
            subprocess_isolation_verified=subprocess_isolation_verified,
            blocking_reason=blocking_reason if decision == "aider_partial" else None,
            decided_at=_iso_now(),
            artifact_path=None,
        )


def emit_aider_promotion_decision(
    decision: AiderPromotionDecision,
    *,
    artifact_dir: Path = Path("artifacts") / "aider_promotion_reratification",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "aider_promotion_decision.json"
    out_path.write_text(
        json.dumps(
            {
                "decision": decision.decision,
                "gate_passed": decision.gate_passed,
                "wired_checker_called": decision.wired_checker_called,
                "propagation_verified": decision.propagation_verified,
                "subprocess_isolation_verified": decision.subprocess_isolation_verified,
                "blocking_reason": decision.blocking_reason,
                "decided_at": decision.decided_at,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    decision.artifact_path = str(out_path)
    return str(out_path)


__all__ = [
    "AiderPromotionDecision",
    "AiderPromotionReratifier",
    "emit_aider_promotion_decision",
]
