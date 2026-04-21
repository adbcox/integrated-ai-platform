"""LACE2-P4-LIVE-REPAIR-POLICY-PROOF-SEAM-1: prove RepairPolicyGate decision table on bounded failure scenarios."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.repair_policy_gate import RepairPolicyGate, RepairDecision, FailureRecord
from framework.retry_policy_schema import RetryPolicy

assert "max_attempts" in RetryPolicy.__dataclass_fields__, "INTERFACE MISMATCH: RetryPolicy.max_attempts"
assert "retry_on_validation_failure" in RetryPolicy.__dataclass_fields__, \
    "INTERFACE MISMATCH: RetryPolicy.retry_on_validation_failure"
assert "retry_on_execution_failure" in RetryPolicy.__dataclass_fields__, \
    "INTERFACE MISMATCH: RetryPolicy.retry_on_execution_failure"
assert "failure_id" in FailureRecord.__dataclass_fields__, "INTERFACE MISMATCH: FailureRecord.failure_id"
assert "failure_kind" in FailureRecord.__dataclass_fields__, "INTERFACE MISMATCH: FailureRecord.failure_kind"
assert "attempt_number" in FailureRecord.__dataclass_fields__, "INTERFACE MISMATCH: FailureRecord.attempt_number"
assert "action" in RepairDecision.__dataclass_fields__, "INTERFACE MISMATCH: RepairDecision.action"

_SCENARIO_DEFS = [
    # (row_id, failure_kind, attempt, max_attempts, retry_val, retry_exec, expected_action)
    ("ROW-01", "validation_failure", 1, 3, True,  False, "retry"),
    ("ROW-02", "validation_failure", 1, 3, False, False, "escalate_critique"),
    ("ROW-03", "execution_failure",  1, 3, False, True,  "retry"),
    ("ROW-04", "execution_failure",  1, 3, False, False, "hard_stop"),
    ("ROW-05", "validation_failure", 3, 3, True,  False, "hard_stop"),
    ("ROW-06", "unknown",            1, 3, False, False, "hard_stop"),
]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass(frozen=True)
class DecisionProofRow:
    row_id: str
    failure_kind: str
    attempt_number: int
    max_attempts: int
    retry_on_validation_failure: bool
    retry_on_execution_failure: bool
    expected_action: str
    actual_action: str
    matches_expected: bool


@dataclass
class RepairPolicyProofRecord:
    proof_id: str
    rows_total: int
    rows_correct: int
    decision_accuracy: float
    rows: List[DecisionProofRow]
    proved_at: str
    artifact_path: Optional[str] = None


class RepairPolicyProofRunner:
    """Drives RepairPolicyGate across a bounded decision table and records results honestly."""

    def run(self) -> RepairPolicyProofRecord:
        rows: List[DecisionProofRow] = []
        for (row_id, fkind, attempt, max_att, rv, re_, expected) in _SCENARIO_DEFS:
            policy = RetryPolicy(
                policy_id=f"P-{row_id}",
                max_attempts=max_att,
                retry_on_validation_failure=rv,
                retry_on_execution_failure=re_,
            )
            failure = FailureRecord(
                failure_id=f"F-{row_id}",
                failure_kind=fkind,
                attempt_number=attempt,
                error_summary="test scenario",
            )
            decision: RepairDecision = RepairPolicyGate(policy).decide(failure)
            rows.append(DecisionProofRow(
                row_id=row_id,
                failure_kind=fkind,
                attempt_number=attempt,
                max_attempts=max_att,
                retry_on_validation_failure=rv,
                retry_on_execution_failure=re_,
                expected_action=expected,
                actual_action=decision.action,
                matches_expected=(decision.action == expected),
            ))

        correct = sum(1 for r in rows if r.matches_expected)
        total = len(rows)
        return RepairPolicyProofRecord(
            proof_id=f"RPP-LACE2-{_ts()}",
            rows_total=total,
            rows_correct=correct,
            decision_accuracy=round(correct / total, 4) if total > 0 else 0.0,
            rows=rows,
            proved_at=_iso_now(),
        )

    def emit(self, record: RepairPolicyProofRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "repair_policy_proof.json"
        out_path.write_text(
            json.dumps({
                "proof_id": record.proof_id,
                "rows_total": record.rows_total,
                "rows_correct": record.rows_correct,
                "decision_accuracy": record.decision_accuracy,
                "proved_at": record.proved_at,
                "rows": [asdict(r) for r in record.rows],
            }, indent=2),
            encoding="utf-8",
        )
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["DecisionProofRow", "RepairPolicyProofRecord", "RepairPolicyProofRunner"]
