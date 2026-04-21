"""Seam tests for LEDT-P9-FALLBACK-AUDIT-SEAM-1."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.local_run_receipt import LocalRunReceipt
from framework.fallback_justification import FallbackJustificationRecord
from framework.fallback_audit import FallbackAuditor, FallbackAuditorReport, FallbackAuditEntry

def _now(): return datetime.now(timezone.utc).isoformat()

def _rcpt(pid, fallback=False, jid=None):
    return LocalRunReceipt(
        receipt_id=f"R-{pid}", packet_id=pid, route_chosen="local_execute" if not fallback else "claude_fallback",
        executor_used="aider", validations_run=["make check"], validation_passed=True,
        fallback_used=fallback, fallback_justification_id=jid, result="success",
        elapsed_seconds=1.0, recorded_at=_now(),
    )

def _just(jid, cls="tool_unavailable", evidence="aider not found C1=False", avoidable=False):
    return FallbackJustificationRecord(
        justification_id=jid, packet_id="t", route_decision_id="R",
        justification_class=cls, evidence=evidence,
        avoidable_in_future=avoidable, mitigation_hint="fix", recorded_at=_now(),
    )

def test_import_auditor():
    assert callable(FallbackAuditor)

def test_audit_returns_report():
    r = FallbackAuditor().audit([_rcpt("a")], {})
    assert isinstance(r, FallbackAuditorReport)

def test_non_fallback_has_no_audit_class():
    r = FallbackAuditor().audit([_rcpt("a", fallback=False)], {})
    assert r.entries[0].audit_class is None

def test_avoidable_classified():
    receipts = [_rcpt("a", True, "J1")]
    justs = {"J1": _just("J1", "scope_exceeded", "fsc=12 > 5", True)}
    r = FallbackAuditor().audit(receipts, justs)
    assert r.avoidable_count >= 1
    assert r.entries[0].audit_class == "avoidable"

def test_zero_fallback_runs_ok():
    r = FallbackAuditor().audit([_rcpt("a"), _rcpt("b"), _rcpt("c")], {})
    assert r.fallback_used_count == 0
    assert all(e.audit_class is None for e in r.entries)

def test_emit_artifact(tmp_path):
    receipts = [_rcpt(f"p{i}") for i in range(3)] + [
        _rcpt("fb1", True, "J1"), _rcpt("fb2", True, "J2"), _rcpt("fb3", True, "J3"),
    ]
    justs = {
        "J1": _just("J1", "scope_exceeded", "fsc=10 exceeds limit", True),
        "J2": _just("J2", "tool_unavailable", "aider not found C1", False),
        "J3": _just("J3", "preflight_failed", "code_executor missing C2", False),
    }
    auditor = FallbackAuditor()
    report = auditor.audit(receipts, justs)
    path = auditor.emit(report, tmp_path)
    d = json.loads(Path(path).read_text())
    assert d["total_receipts"] >= 6
    assert d["avoidable_count"] >= 1
    fb_entries = [e for e in d["entries"] if e["fallback_used"]]
    assert all(e["audit_class"] is not None for e in fb_entries)
    nonfb = [e for e in d["entries"] if not e["fallback_used"]]
    assert all(e["audit_class"] is None for e in nonfb)
