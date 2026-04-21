"""ControlledAdapterScaffold: produces a governance scaffold for controlled adapter introduction."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.adapter_readiness_stress import StressHarnessResult
from framework.adapter_campaign_pre_authorizer import PreAuthorizationArtifact

# -- import-time assertions --
assert "verdict" in StressHarnessResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: StressHarnessResult.verdict"
assert "blocking_failures" in StressHarnessResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: StressHarnessResult.blocking_failures"
assert "decision" in PreAuthorizationArtifact.__dataclass_fields__, \
    "INTERFACE MISMATCH: PreAuthorizationArtifact.decision"
assert "all_gates_passed" in PreAuthorizationArtifact.__dataclass_fields__, \
    "INTERFACE MISMATCH: PreAuthorizationArtifact.all_gates_passed"

_PRE_AUTH_AUTHORIZED = "authorized"
_STRESS_STABLE = "stable"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class ScaffoldGate:
    gate_name: str
    passed: bool
    detail: str


@dataclass
class AdapterScaffoldPlan:
    scaffold_decision: str  # "proceed" | "defer" | "blocked"
    gates: List[ScaffoldGate]
    gates_passed: int
    gates_total: int
    defer_reasons: List[str]
    campaign_id: Optional[str]
    scaffolded_at: str
    artifact_path: Optional[str]


class ControlledAdapterScaffold:
    """Evidence gate: verdict=stable + decision=authorized → proceed; else defer/blocked."""

    def build(
        self,
        *,
        stress_result: Optional[StressHarnessResult] = None,
        pre_auth: Optional[PreAuthorizationArtifact] = None,
    ) -> AdapterScaffoldPlan:
        gates: List[ScaffoldGate] = []
        defer_reasons: List[str] = []

        # Gate 1: stress verdict stable
        if stress_result is not None:
            passed = stress_result.verdict == _STRESS_STABLE
            detail = f"stress_verdict={stress_result.verdict} blocking_failures={stress_result.blocking_failures}"
            if not passed:
                defer_reasons.append(f"stress not stable: {stress_result.verdict}")
        else:
            passed = False
            detail = "stress_result not provided"
            defer_reasons.append("stress_result absent")
        gates.append(ScaffoldGate(gate_name="stress_stable", passed=passed, detail=detail))

        # Gate 2: pre-authorization granted
        if pre_auth is not None:
            passed = pre_auth.decision == _PRE_AUTH_AUTHORIZED and pre_auth.all_gates_passed
            detail = f"decision={pre_auth.decision} all_gates_passed={pre_auth.all_gates_passed}"
            if not passed:
                for r in (pre_auth.defer_reasons or []):
                    defer_reasons.append(r)
                if pre_auth.decision != _PRE_AUTH_AUTHORIZED:
                    defer_reasons.append(f"pre_auth decision={pre_auth.decision}")
        else:
            passed = False
            detail = "pre_auth not provided"
            defer_reasons.append("pre_auth absent")
        gates.append(ScaffoldGate(gate_name="pre_auth_authorized", passed=passed, detail=detail))

        gates_passed = sum(1 for g in gates if g.passed)
        gates_total = len(gates)

        if gates_passed == gates_total:
            scaffold_decision = "proceed"
        elif stress_result is None and pre_auth is None:
            scaffold_decision = "blocked"
        else:
            scaffold_decision = "defer"

        campaign_id = pre_auth.campaign_id if pre_auth is not None else None

        return AdapterScaffoldPlan(
            scaffold_decision=scaffold_decision,
            gates=gates,
            gates_passed=gates_passed,
            gates_total=gates_total,
            defer_reasons=defer_reasons,
            campaign_id=campaign_id,
            scaffolded_at=_iso_now(),
            artifact_path=None,
        )


def emit_scaffold_plan(
    plan: AdapterScaffoldPlan,
    *,
    artifact_dir: Path = Path("artifacts") / "controlled_adapter_scaffold",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "scaffold_plan.json"
    out_path.write_text(
        json.dumps(
            {
                "scaffold_decision": plan.scaffold_decision,
                "gates_passed": plan.gates_passed,
                "gates_total": plan.gates_total,
                "campaign_id": plan.campaign_id,
                "defer_reasons": plan.defer_reasons,
                "scaffolded_at": plan.scaffolded_at,
                "gates": [
                    {"gate_name": g.gate_name, "passed": g.passed, "detail": g.detail}
                    for g in plan.gates
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    plan.artifact_path = str(out_path)
    return str(out_path)


__all__ = [
    "ScaffoldGate",
    "AdapterScaffoldPlan",
    "ControlledAdapterScaffold",
    "emit_scaffold_plan",
]
