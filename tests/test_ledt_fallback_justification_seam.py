"""Seam tests for LEDT-P5-FALLBACK-JUSTIFICATION-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.exec_route_decision import ExecRouteDecision
from framework.fallback_justification import (
    FallbackJustificationWriter, FallbackJustificationRecord, VALID_JUSTIFICATION_CLASSES,
)
from datetime import datetime, timezone

def _fallback_decision(pid="test-fallback"):
    from datetime import datetime, timezone
    return ExecRouteDecision(
        decision_id=f"ROUTE-TEST-{pid}",
        packet_id=pid,
        route="claude_fallback",
        eligibility_passed=False,
        preflight_passed=True,
        decision_reason="eligibility failed: test",
        fallback_authorized=True,
        fallback_authorization_reason="eligibility failed: test",
        decided_at=datetime.now(timezone.utc).isoformat(),
    )

def _local_decision(pid="test-local"):
    return ExecRouteDecision(
        decision_id=f"ROUTE-TEST-{pid}",
        packet_id=pid,
        route="local_execute",
        eligibility_passed=True,
        preflight_passed=True,
        decision_reason="ok",
        fallback_authorized=False,
        fallback_authorization_reason=None,
        decided_at=datetime.now(timezone.utc).isoformat(),
    )

def test_import_writer():
    assert callable(FallbackJustificationWriter)

def test_record_returns_record():
    r = FallbackJustificationWriter().record(
        _fallback_decision(), "tool_unavailable", "aider not found on sys.path", True, "install aider"
    )
    assert isinstance(r, FallbackJustificationRecord)

def test_record_raises_on_non_fallback_route():
    import pytest
    with pytest.raises(ValueError, match="claude_fallback"):
        FallbackJustificationWriter().record(
            _local_decision(), "tool_unavailable", "some evidence", False, "hint"
        )

def test_record_raises_on_empty_evidence():
    import pytest
    with pytest.raises(ValueError, match="evidence"):
        FallbackJustificationWriter().record(
            _fallback_decision(), "tool_unavailable", "", False, "hint"
        )

def test_valid_classes_enforced():
    import pytest
    with pytest.raises(ValueError):
        FallbackJustificationWriter().record(
            _fallback_decision(), "made_up_class", "some evidence", False, "hint"
        )

def test_emit_artifact(tmp_path):
    w = FallbackJustificationWriter()
    records = [
        w.record(_fallback_decision("a"), "tool_unavailable", "aider not found C1=False", True, "install aider"),
        w.record(_fallback_decision("b"), "scope_exceeded", "fsc=12 > 5 limit", True, "split packet"),
        w.record(_fallback_decision("c"), "validation_failure", "no validation commands supplied", False, "add make check"),
    ]
    path = w.emit(records, tmp_path)
    d = json.loads(Path(path).read_text())
    assert d["sample_count"] >= 3
    assert len(d["class_distribution"]) >= 3
    assert all(r["evidence"] for r in d["records"])
