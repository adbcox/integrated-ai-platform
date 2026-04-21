"""Seam tests for LEDT-P2-LOCAL-EXEC-ELIGIBILITY-CONTRACT-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.local_exec_eligibility_contract import (
    LocalExecEligibilityEvaluator, LocalExecEligibilityRecord, LocalExecEligibilityInput,
)

def _bounded():
    return LocalExecEligibilityInput("test-pkg", 2, False, False, False, ["make check"])

def _over_scope():
    return LocalExecEligibilityInput("over-scope", 10, False, False, False, ["make check"])

def _ext_api():
    return LocalExecEligibilityInput("ext-api", 1, True, False, False, ["make check"])

def test_import_evaluator():
    assert callable(LocalExecEligibilityEvaluator)

def test_evaluate_returns_record():
    r = LocalExecEligibilityEvaluator().evaluate(_bounded())
    assert isinstance(r, LocalExecEligibilityRecord)

def test_bounded_packet_eligible():
    r = LocalExecEligibilityEvaluator().evaluate(_bounded())
    assert r.eligible is True
    assert r.disqualifiers == []

def test_over_scope_disqualified():
    r = LocalExecEligibilityEvaluator().evaluate(_over_scope())
    assert r.eligible is False
    assert len(r.disqualifiers) >= 1

def test_external_api_disqualified():
    r = LocalExecEligibilityEvaluator().evaluate(_ext_api())
    assert r.eligible is False
    assert any("external_api" in d or "has_external" in d for d in r.disqualifiers)

def test_emit_artifact(tmp_path):
    ev = LocalExecEligibilityEvaluator()
    records = [ev.evaluate(i) for i in [
        _bounded(),
        LocalExecEligibilityInput("test-pkg-b", 3, False, False, False, ["make check", "pytest"]),
        _over_scope(), _ext_api(),
        LocalExecEligibilityInput("broad", 2, False, True, False, ["make check"]),
    ]]
    path = ev.emit(records, tmp_path)
    d = json.loads(Path(path).read_text())
    assert d["sample_count"] >= 4
    assert d["disqualified_count"] >= 1
    assert d["eligible_count"] >= 2
