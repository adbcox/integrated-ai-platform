#!/usr/bin/env python3
"""LEDT-P9: Run fallback audit on sample receipts."""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.local_run_receipt import LocalRunReceipt, LocalRunReceiptWriter
from framework.fallback_justification import FallbackJustificationRecord
from framework.fallback_audit import FallbackAuditor
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LEDT"

def _now(): return datetime.now(timezone.utc).isoformat()

def _rcpt(pid, route, fallback, jid=None):
    return LocalRunReceipt(
        receipt_id=f"RCPT-TEST-{pid}", packet_id=pid, route_chosen=route,
        executor_used="aider" if route=="local_execute" else "claude",
        validations_run=["make check"], validation_passed=True,
        fallback_used=fallback, fallback_justification_id=jid,
        result="success", elapsed_seconds=3.0, recorded_at=_now(),
    )

def _just(jid, cls, evidence, avoidable):
    return FallbackJustificationRecord(
        justification_id=jid, packet_id="test", route_decision_id="ROUTE-TEST",
        justification_class=cls, evidence=evidence,
        avoidable_in_future=avoidable, mitigation_hint="fix it", recorded_at=_now(),
    )

def main():
    receipts = [
        _rcpt("p1", "local_execute", False),
        _rcpt("p2", "local_execute", False),
        _rcpt("p3", "local_execute", False),
        _rcpt("p4-avoidable", "claude_fallback", True, "JUST-AVOID"),
        _rcpt("p5-justified", "claude_fallback", True, "JUST-JUSTI"),
        _rcpt("p6-justified2", "claude_fallback", True, "JUST-JUS2"),
    ]
    justifications = {
        "JUST-AVOID": _just("JUST-AVOID", "scope_exceeded", "file_scope_count=12 > 5 limit", True),
        "JUST-JUSTI": _just("JUST-JUSTI", "tool_unavailable", "aider not found on sys.path; C1=False", False),
        "JUST-JUS2":  _just("JUST-JUS2",  "preflight_failed", "code_executor not importable; overall_ready=False", False),
    }
    auditor = FallbackAuditor()
    report = auditor.audit(receipts, justifications)
    path = auditor.emit(report, ARTIFACT_DIR)
    print(f"total_receipts:      {report.total_receipts}")
    print(f"fallback_used_count: {report.fallback_used_count}")
    print(f"justified:           {report.justified_count}")
    print(f"avoidable:           {report.avoidable_count}")
    print(f"invalid:             {report.invalid_count}")
    print(f"artifact:            {path}")

if __name__ == "__main__":
    main()
