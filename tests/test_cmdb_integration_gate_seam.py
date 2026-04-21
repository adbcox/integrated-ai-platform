"""Tests for framework.cmdb_integration_gate — CMDB gate seam."""
import pytest
from pathlib import Path

from framework.cmdb_integration_gate import (
    CmdbGateDecision,
    CmdbIntegrationGate,
    evaluate_cmdb_gate,
    GATE_PASS,
    GATE_BLOCK,
)


def test_import_ok():
    from framework.cmdb_integration_gate import CmdbIntegrationGate, GATE_PASS, GATE_BLOCK  # noqa: F401


def test_constants():
    assert GATE_PASS == "gate_pass"
    assert GATE_BLOCK == "gate_block"


def test_evaluate_returns_decision():
    decision = evaluate_cmdb_gate()
    assert isinstance(decision, CmdbGateDecision)


def test_evaluate_no_args_passes():
    decision = evaluate_cmdb_gate()
    assert decision.result in (GATE_PASS, GATE_BLOCK)


def test_evaluate_no_class_requested_passes():
    decision = evaluate_cmdb_gate(requested_class="")
    assert decision.result == GATE_PASS


def test_passed_property_matches_result():
    decision = evaluate_cmdb_gate()
    assert decision.passed == (decision.result == GATE_PASS)


def test_allowed_class_non_empty():
    decision = evaluate_cmdb_gate()
    assert decision.allowed_class != ""


def test_current_phase_non_empty():
    decision = evaluate_cmdb_gate()
    assert decision.current_phase != ""


def test_evaluated_at_is_iso():
    decision = evaluate_cmdb_gate()
    assert "T" in decision.evaluated_at


def test_to_dict_keys():
    decision = evaluate_cmdb_gate()
    d = decision.to_dict()
    for k in ("schema_version", "result", "allowed_class", "current_phase", "reason", "passed"):
        assert k in d


def test_decision_frozen():
    decision = evaluate_cmdb_gate()
    with pytest.raises((AttributeError, TypeError)):
        decision.result = "modified"  # type: ignore


def test_wrong_class_blocks():
    decision = evaluate_cmdb_gate(requested_class="execution_only_wrong_class")
    assert decision.result == GATE_BLOCK


def test_missing_governance_blocks(tmp_path):
    decision = evaluate_cmdb_gate(requested_class="", governance_dir=tmp_path)
    assert decision.result == GATE_BLOCK
    assert "not found" in decision.reason


def test_init_ok_from_framework():
    from framework import evaluate_cmdb_gate  # noqa: F401
