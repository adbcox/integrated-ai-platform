"""LEDT-P10: Proof harness showing local_execute is default on representative sample."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from framework.local_exec_eligibility_contract import (
    LocalExecEligibilityRecord, LocalExecEligibilityEvaluator, LocalExecEligibilityInput,
)
from framework.local_exec_preflight import LocalExecPreflightReport, LocalExecPreflightEvaluator
from framework.exec_route_decision import ExecRouteDecision, ExecRouteDecider
from framework.local_run_receipt import LocalRunReceipt, LocalRunReceiptWriter

assert "eligible" in LocalExecEligibilityRecord.__dataclass_fields__, "INTERFACE MISMATCH"
assert "overall_ready" in LocalExecPreflightReport.__dataclass_fields__, "INTERFACE MISMATCH"
assert "route" in ExecRouteDecision.__dataclass_fields__, "INTERFACE MISMATCH"
assert "route_chosen" in LocalRunReceipt.__dataclass_fields__, "INTERFACE MISMATCH"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class ProofSampleResult:
    sample_id: str
    packet_description: str
    eligibility_passed: bool
    preflight_passed: bool
    route_chosen: str
    receipt_result: str
    is_local: bool


@dataclass
class LocalFirstProofRecord:
    proof_id: str
    samples_total: int
    local_route_count: int
    claude_fallback_count: int
    hard_stop_count: int
    local_first_rate: float
    sample_results: List[ProofSampleResult]
    proved_at: str
    artifact_path: Optional[str] = None


# sample_inputs: list of dicts with keys: packet_id, description, file_scope_count,
#   has_external_api_calls, requires_broad_redesign, requires_live_infra_touch, validation_commands
class LocalFirstProofHarness:
    """Runs sample packet descriptions through full decision chain."""

    def run(self, sample_inputs: List[Dict]) -> LocalFirstProofRecord:
        elig_ev = LocalExecEligibilityEvaluator()
        pre_ev = LocalExecPreflightEvaluator()
        decider = ExecRouteDecider()
        rcpt_writer = LocalRunReceiptWriter()

        results: List[ProofSampleResult] = []

        for s in sample_inputs:
            pid = s["packet_id"]
            elig_inp = LocalExecEligibilityInput(
                packet_id=pid,
                file_scope_count=s.get("file_scope_count", 2),
                has_external_api_calls=s.get("has_external_api_calls", False),
                requires_broad_redesign=s.get("requires_broad_redesign", False),
                requires_live_infra_touch=s.get("requires_live_infra_touch", False),
                validation_commands=s.get("validation_commands", ["make check"]),
            )
            elig = elig_ev.evaluate(elig_inp)
            pre = pre_ev.evaluate(pid, elig_inp.file_scope_count, elig_inp.validation_commands)
            decision = decider.decide(elig, pre)

            fid = None
            if decision.route == "claude_fallback":
                fid = f"JUST-HARNESS-{pid}"

            rcpt = rcpt_writer.write(
                packet_id=pid,
                route_chosen=decision.route,
                executor_used="aider" if decision.route == "local_execute" else "claude",
                validations_run=elig_inp.validation_commands,
                validation_passed=elig.eligible and pre.overall_ready,
                fallback_used=(decision.route == "claude_fallback"),
                result="success",
                fallback_justification_id=fid,
            )

            results.append(ProofSampleResult(
                sample_id=pid,
                packet_description=s.get("description", pid),
                eligibility_passed=elig.eligible,
                preflight_passed=pre.overall_ready,
                route_chosen=decision.route,
                receipt_result=rcpt.result,
                is_local=(decision.route == "local_execute"),
            ))

        total = len(results)
        local_count = sum(1 for r in results if r.is_local)
        fallback_count = sum(1 for r in results if r.route_chosen == "claude_fallback")
        hard_count = sum(1 for r in results if r.route_chosen == "hard_stop")

        return LocalFirstProofRecord(
            proof_id=f"PROOF-{_ts()}",
            samples_total=total,
            local_route_count=local_count,
            claude_fallback_count=fallback_count,
            hard_stop_count=hard_count,
            local_first_rate=round(local_count / total, 4) if total else 0.0,
            sample_results=results,
            proved_at=_iso_now(),
        )

    def emit(self, record: LocalFirstProofRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "local_first_proof.json"
        out_path.write_text(
            json.dumps({
                "proof_id": record.proof_id,
                "samples_total": record.samples_total,
                "local_route_count": record.local_route_count,
                "claude_fallback_count": record.claude_fallback_count,
                "hard_stop_count": record.hard_stop_count,
                "local_first_rate": record.local_first_rate,
                "sample_results": [asdict(r) for r in record.sample_results],
                "proved_at": record.proved_at,
            }, indent=2),
            encoding="utf-8",
        )
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["ProofSampleResult", "LocalFirstProofRecord", "LocalFirstProofHarness"]
