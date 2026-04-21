"""LEDT-P11: Ratify whether local-exec-default transition is confirmed."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.local_exec_eligibility_contract import LocalExecEligibilityRecord
from framework.local_exec_preflight import LocalExecPreflightReport
from framework.local_first_proof_harness import LocalFirstProofRecord
from framework.fallback_audit import FallbackAuditorReport
from framework.packet_routing_metadata import PacketRoutingMetadata

assert "eligible" in LocalExecEligibilityRecord.__dataclass_fields__, "INTERFACE MISMATCH"
assert "overall_ready" in LocalExecPreflightReport.__dataclass_fields__, "INTERFACE MISMATCH"
assert "local_first_rate" in LocalFirstProofRecord.__dataclass_fields__, "INTERFACE MISMATCH"
assert "avoidable_count" in FallbackAuditorReport.__dataclass_fields__, "INTERFACE MISMATCH"
assert "preferred_executor" in PacketRoutingMetadata.__dataclass_fields__, "INTERFACE MISMATCH"

VERDICTS = {
    "confirmed": "local_exec_default_confirmed",
    "partial": "partial_local_exec_default",
    "not_confirmed": "local_exec_default_not_confirmed",
}

LIMITATIONS = [
    "No live execution loop tested; routing is decision-surface proof only",
    "Proof harness uses synthetic packet descriptions, not live campaign packets",
    "Fallback audit uses constructed receipts, not production execution history",
    "Planner preference schema is not yet wired into any live campaign plan emitter",
]

ARTIFACT_BASE = Path("artifacts/expansion/LEDT")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class LEDTTransitionCriterion:
    criterion_id: str
    description: str
    passed: bool
    evidence: str


@dataclass
class LEDTTransitionRatificationRecord:
    ratification_id: str
    criteria: List[LEDTTransitionCriterion]
    criteria_passed: int
    criteria_total: int
    verdict: str
    limitations: List[str]
    ratified_at: str
    artifact_path: Optional[str] = None


class LEDTTransitionRatifier:
    """Ratifies local-exec-default transition from evidence artifacts."""

    def ratify(self) -> LEDTTransitionRatificationRecord:
        criteria: List[LEDTTransitionCriterion] = []

        # C1: Eligibility contract defined
        try:
            from framework.local_exec_eligibility_contract import LocalExecEligibilityEvaluator, LocalExecEligibilityInput
            test_rec = LocalExecEligibilityEvaluator().evaluate(
                LocalExecEligibilityInput("test", 2, False, False, False, ["make check"])
            )
            c1_passed = "eligible" in test_rec.__dataclass_fields__
            c1_evidence = f"LocalExecEligibilityRecord has 'eligible' field; evaluate() works"
        except Exception as exc:
            c1_passed = False
            c1_evidence = f"eligibility contract error: {exc}"
        criteria.append(LEDTTransitionCriterion("C1", "Eligibility contract defined and evaluable", c1_passed, c1_evidence))

        # C2: Route decision defaults to local_execute (from proof artifact)
        proof_path = ARTIFACT_BASE / "local_first_proof.json"
        if proof_path.exists():
            proof_data = json.loads(proof_path.read_text(encoding="utf-8"))
            rate = proof_data.get("local_first_rate", 0.0)
            c2_passed = rate >= 0.8
            c2_evidence = f"local_first_rate={rate} from local_first_proof.json"
        else:
            c2_passed = False
            c2_evidence = "local_first_proof.json not found"
        criteria.append(LEDTTransitionCriterion("C2", "Route decision defaults to local_execute", c2_passed, c2_evidence))

        # C3: Packet routing metadata defaults to local_first
        meta_path = ARTIFACT_BASE / "packet_routing_metadata_proof.json"
        if meta_path.exists():
            meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
            meta_rate = meta_data.get("local_first_rate", 0.0)
            c3_passed = meta_rate >= 0.8
            c3_evidence = f"local_first_rate={meta_rate} from packet_routing_metadata_proof.json"
        else:
            c3_passed = False
            c3_evidence = "packet_routing_metadata_proof.json not found"
        criteria.append(LEDTTransitionCriterion("C3", "Packet routing metadata defaults to local_first", c3_passed, c3_evidence))

        # C4: Run receipt captures route and fallback status
        try:
            from framework.local_run_receipt import LocalRunReceipt
            c4_passed = ("route_chosen" in LocalRunReceipt.__dataclass_fields__
                         and "fallback_used" in LocalRunReceipt.__dataclass_fields__)
            c4_evidence = "LocalRunReceipt has route_chosen and fallback_used fields"
        except Exception as exc:
            c4_passed = False
            c4_evidence = f"LocalRunReceipt error: {exc}"
        criteria.append(LEDTTransitionCriterion("C4", "Run receipt captures route and fallback status", c4_passed, c4_evidence))

        # C5: Fallback audit operational with at least 1 avoidable classification
        audit_path = ARTIFACT_BASE / "fallback_audit.json"
        if audit_path.exists():
            audit_data = json.loads(audit_path.read_text(encoding="utf-8"))
            c5_passed = audit_data.get("avoidable_count", 0) >= 1
            c5_evidence = f"avoidable_count={audit_data.get('avoidable_count', 0)} from fallback_audit.json"
        else:
            c5_passed = False
            c5_evidence = "fallback_audit.json not found"
        criteria.append(LEDTTransitionCriterion("C5", "Fallback audit operational with >= 1 avoidable", c5_passed, c5_evidence))

        passed_count = sum(1 for c in criteria if c.passed)

        if passed_count == 5:
            verdict = VERDICTS["confirmed"]
        elif passed_count >= 3:
            verdict = VERDICTS["partial"]
        else:
            verdict = VERDICTS["not_confirmed"]

        return LEDTTransitionRatificationRecord(
            ratification_id=f"LEDT-RAT-{_ts()}",
            criteria=criteria,
            criteria_passed=passed_count,
            criteria_total=5,
            verdict=verdict,
            limitations=LIMITATIONS,
            ratified_at=_iso_now(),
        )

    def emit(self, record: LEDTTransitionRatificationRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "ledt_transition_ratification.json"
        out_path.write_text(
            json.dumps({
                "ratification_id": record.ratification_id,
                "criteria": [asdict(c) for c in record.criteria],
                "criteria_passed": record.criteria_passed,
                "criteria_total": record.criteria_total,
                "verdict": record.verdict,
                "limitations": record.limitations,
                "ratified_at": record.ratified_at,
            }, indent=2),
            encoding="utf-8",
        )
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["LEDTTransitionCriterion", "LEDTTransitionRatificationRecord", "LEDTTransitionRatifier"]
