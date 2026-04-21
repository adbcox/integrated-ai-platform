"""Seam tests for LEDT-P7-LOCAL-RUN-RECEIPT-SEAM-1."""
from __future__ import annotations
import json, sys
import pytest
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.local_run_receipt import LocalRunReceipt, LocalRunReceiptWriter

def _local(pid="test"):
    return LocalRunReceiptWriter().write(pid, "local_execute", "aider", ["make check"], True, False, "success", 2.0)

def test_import_writer():
    assert callable(LocalRunReceiptWriter)

def test_write_returns_receipt():
    r = _local()
    assert isinstance(r, LocalRunReceipt)

def test_local_execute_no_fallback():
    r = _local()
    assert r.route_chosen == "local_execute"
    assert r.fallback_used is False
    assert r.fallback_justification_id is None

def test_fallback_requires_justification_id():
    with pytest.raises(ValueError, match="fallback_justification_id"):
        LocalRunReceiptWriter().write("t", "claude_fallback", "claude", ["make check"], False, True, "success")

def test_fallback_with_id_accepted():
    r = LocalRunReceiptWriter().write("t", "claude_fallback", "claude", ["make check"], False, True, "success",
                                       fallback_justification_id="JUST-XYZ")
    assert r.fallback_justification_id == "JUST-XYZ"

def test_emit_artifact(tmp_path):
    w = LocalRunReceiptWriter()
    receipts = [
        w.write(f"p{i}", "local_execute", "aider", ["make check"], True, False, "success") for i in range(3)
    ] + [
        w.write("fb", "claude_fallback", "claude", ["make check"], False, True, "success",
                fallback_justification_id="JUST-TEST")
    ]
    path = w.emit(receipts, tmp_path)
    d = json.loads(Path(path).read_text())
    assert d["local_execute_count"] >= 3
    assert all(r["fallback_justification_id"] is not None for r in d["receipts"] if r["fallback_used"])
