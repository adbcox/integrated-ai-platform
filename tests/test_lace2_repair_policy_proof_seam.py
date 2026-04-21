"""Seam tests for LACE2-P4-LIVE-REPAIR-POLICY-PROOF-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.repair_policy_proof import RepairPolicyProofRunner, RepairPolicyProofRecord


def test_import_runner():
    from framework.repair_policy_proof import RepairPolicyProofRunner
    assert callable(RepairPolicyProofRunner)


def test_run_returns_record():
    r = RepairPolicyProofRunner().run()
    assert isinstance(r, RepairPolicyProofRecord)


def test_six_rows():
    r = RepairPolicyProofRunner().run()
    assert r.rows_total == 6


def test_all_rows_have_actual_action():
    r = RepairPolicyProofRunner().run()
    valid = {"retry", "escalate_critique", "hard_stop"}
    assert all(row.actual_action in valid for row in r.rows)


def test_decision_accuracy_field():
    r = RepairPolicyProofRunner().run()
    assert 0.0 <= r.decision_accuracy <= 1.0


def test_emit_artifact(tmp_path):
    runner = RepairPolicyProofRunner()
    r = runner.run()
    path = runner.emit(r, tmp_path)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert "proof_id" in data
    assert "rows" in data
    assert "decision_accuracy" in data
    assert len(data["rows"]) == 6
