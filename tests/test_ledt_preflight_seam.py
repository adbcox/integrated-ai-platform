"""Seam tests for LEDT-P3-LOCAL-EXEC-PREFLIGHT-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.local_exec_preflight import (
    LocalExecPreflightEvaluator, LocalExecPreflightReport, PreflightCheck,
)

def test_import_evaluator():
    assert callable(LocalExecPreflightEvaluator)

def test_evaluate_returns_report():
    r = LocalExecPreflightEvaluator().evaluate("test", 2, ["make check"])
    assert isinstance(r, LocalExecPreflightReport)

def test_checks_non_empty():
    r = LocalExecPreflightEvaluator().evaluate("test", 2, ["make check"])
    assert len(r.checks) >= 1
    assert all(isinstance(c, PreflightCheck) for c in r.checks)

def test_code_executor_importable():
    r = LocalExecPreflightEvaluator().evaluate("test", 2, ["make check"])
    assert r.code_executor_importable is True

def test_file_scope_risk_low():
    r = LocalExecPreflightEvaluator().evaluate("test", 2, ["make check"])
    assert r.file_scope_risk == "low"

def test_emit_artifact(tmp_path):
    ev = LocalExecPreflightEvaluator()
    reports = [
        ev.evaluate("p1", 2, ["make check"]),
        ev.evaluate("p2", 5, ["make check", "pytest"]),
        ev.evaluate("p3", 10, []),
    ]
    path = ev.emit(reports, tmp_path)
    d = json.loads(Path(path).read_text())
    assert d["sample_count"] >= 3
    assert d["ready_count"] >= 1
    assert all(len(r["checks"]) >= 1 for r in d["sample_reports"])
