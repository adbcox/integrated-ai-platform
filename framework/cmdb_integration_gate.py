"""CMDB integration gate for LAEC1 — evaluative only, no governance writes.

Inspection gate output:
  CmdbAuthorityRecord fields: current_phase, current_phase_status,
    next_package_class, contract_version, gates_summary, phases_count, read_at
  current_phase: 0
  next_package_class: capability_session
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from framework.cmdb_authority_pilot import CmdbAuthorityPilot, CmdbAuthorityRecord

assert hasattr(CmdbAuthorityRecord, "__dataclass_fields__"), "INTERFACE MISMATCH: CmdbAuthorityRecord"
_CONFIRMED_FIELDS = {
    "current_phase", "current_phase_status", "next_package_class",
    "contract_version", "gates_summary", "phases_count", "read_at"
}
assert _CONFIRMED_FIELDS.issubset(set(CmdbAuthorityRecord.__dataclass_fields__.keys())), \
    "INTERFACE MISMATCH: CmdbAuthorityRecord fields changed"

GATE_PASS = "gate_pass"
GATE_BLOCK = "gate_block"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class CmdbGateDecision:
    result: str
    allowed_class: str
    current_phase: str
    reason: str
    evaluated_at: str

    @property
    def passed(self) -> bool:
        return self.result == GATE_PASS

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "result": self.result,
            "allowed_class": self.allowed_class,
            "current_phase": self.current_phase,
            "reason": self.reason,
            "evaluated_at": self.evaluated_at,
            "passed": self.passed,
        }


class CmdbIntegrationGate:
    def __init__(self, governance_dir: Path = Path("governance")) -> None:
        self._governance_dir = Path(governance_dir)

    def evaluate(self, requested_class: str = "") -> CmdbGateDecision:
        try:
            rec = CmdbAuthorityPilot(governance_dir=self._governance_dir).read_authority()
        except FileNotFoundError as exc:
            return CmdbGateDecision(
                result=GATE_BLOCK,
                allowed_class="unknown",
                current_phase="unknown",
                reason=f"governance/current_phase.json not found: {exc}",
                evaluated_at=_iso_now(),
            )

        allowed_class = rec.next_package_class
        current_phase = rec.current_phase

        if not requested_class:
            # No specific class requested; pass if authority is readable
            return CmdbGateDecision(
                result=GATE_PASS,
                allowed_class=allowed_class,
                current_phase=current_phase,
                reason="authority readable; no specific class requested",
                evaluated_at=_iso_now(),
            )

        if requested_class == allowed_class:
            return CmdbGateDecision(
                result=GATE_PASS,
                allowed_class=allowed_class,
                current_phase=current_phase,
                reason=f"requested class {requested_class!r} matches permitted class",
                evaluated_at=_iso_now(),
            )

        return CmdbGateDecision(
            result=GATE_BLOCK,
            allowed_class=allowed_class,
            current_phase=current_phase,
            reason=f"requested {requested_class!r} but authority permits {allowed_class!r}",
            evaluated_at=_iso_now(),
        )


def evaluate_cmdb_gate(
    requested_class: str = "",
    governance_dir: Path = Path("governance"),
) -> CmdbGateDecision:
    return CmdbIntegrationGate(governance_dir=governance_dir).evaluate(requested_class=requested_class)


__all__ = [
    "GATE_PASS",
    "GATE_BLOCK",
    "CmdbGateDecision",
    "CmdbIntegrationGate",
    "evaluate_cmdb_gate",
]
