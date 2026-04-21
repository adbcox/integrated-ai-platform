#!/usr/bin/env python3
"""LEDT-P7: Emit local run receipt samples."""
from __future__ import annotations
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.local_run_receipt import LocalRunReceiptWriter
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LEDT"

def main():
    w = LocalRunReceiptWriter()
    receipts = [
        w.write("LEDT-P2-eligibility", "local_execute", "aider", ["make check", "pytest tests/test_ledt_eligibility_contract_seam.py -v"], True, False, "success", 4.1),
        w.write("LEDT-P3-preflight",   "local_execute", "aider", ["make check", "pytest tests/test_ledt_preflight_seam.py -v"], True, False, "success", 3.8),
        w.write("LEDT-P4-route",       "local_execute", "aider", ["make check", "pytest tests/test_ledt_exec_route_decision_seam.py -v"], True, False, "success", 5.2),
        w.write("LEDT-P5-fallback",    "claude_fallback", "claude", ["make check"], False, True, "success", 22.0, fallback_justification_id="JUST-TEST-scope_exceeded"),
        w.write("LEDT-P6-routing",     "local_execute", "aider", ["make check", "pytest tests/test_ledt_packet_routing_metadata_seam.py -v"], True, False, "success", 3.5),
    ]
    path = w.emit(receipts, ARTIFACT_DIR)
    lc = sum(1 for r in receipts if r.route_chosen == "local_execute")
    print(f"sample_count:        {len(receipts)}")
    print(f"local_execute_count: {lc}")
    for r in receipts:
        print(f"  {r.packet_id}: route={r.route_chosen} fallback_used={r.fallback_used}")
    print(f"artifact:            {path}")

if __name__ == "__main__":
    main()
