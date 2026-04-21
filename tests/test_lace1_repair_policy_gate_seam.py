"""Seam tests for LACE1-P4-RETRY-REPAIR-POLICY-SEAM-1."""
from __future__ import annotations
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.repair_policy_gate import RepairPolicyGate, FailureRecord, RepairDecision
from framework.retry_policy_schema import RetryPolicy


def _policy(max_attempts=3, val_retry=True, exec_retry=False):
    return RetryPolicy(policy_id="test", max_attempts=max_attempts,
                       retry_on_validation_failure=val_retry, retry_on_execution_failure=exec_retry)


def test_import_gate():
    from framework.repair_policy_gate import RepairPolicyGate
    assert callable(RepairPolicyGate)


def test_validation_failure_retries():
    r = RepairPolicyGate(_policy(val_retry=True)).decide(FailureRecord("f1","validation_failure",1,""))
    assert r.action == "retry"
    assert r.max_attempts_reached is False


def test_validation_failure_no_retry_escalates():
    r = RepairPolicyGate(_policy(val_retry=False)).decide(FailureRecord("f1","validation_failure",1,""))
    assert r.action == "escalate_critique"


def test_execution_failure_with_retry():
    r = RepairPolicyGate(_policy(exec_retry=True)).decide(FailureRecord("f1","execution_failure",1,""))
    assert r.action == "retry"


def test_max_attempts_hard_stop():
    r = RepairPolicyGate(_policy(max_attempts=3)).decide(FailureRecord("f1","validation_failure",3,""))
    assert r.action == "hard_stop"
    assert r.max_attempts_reached is True


def test_action_always_valid():
    gate = RepairPolicyGate(_policy())
    for kind in ("validation_failure","execution_failure","timeout","unknown"):
        r = gate.decide(FailureRecord("f1", kind, 1, ""))
        assert r.action in {"retry", "escalate_critique", "hard_stop"}
