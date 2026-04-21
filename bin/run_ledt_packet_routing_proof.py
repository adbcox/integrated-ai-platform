#!/usr/bin/env python3
"""LEDT-P6: Prove packet routing metadata defaults to local_first."""
from __future__ import annotations
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.packet_routing_metadata import PacketRoutingMetadataBuilder
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LEDT"

def main():
    b = PacketRoutingMetadataBuilder()
    records = [
        b.build("LEDT-P2-eligibility"),
        b.build("LEDT-P3-preflight"),
        b.build("LEDT-P4-route-decision"),
        b.build("LEDT-P5-fallback-justification"),
        b.build("LEDT-P12-closeout", override_executor="claude_only"),
    ]
    path = b.emit(records, ARTIFACT_DIR)
    lf = sum(1 for r in records if r.preferred_executor == "local_first")
    print(f"sample_count:      {len(records)}")
    print(f"local_first_count: {lf}")
    print(f"local_first_rate:  {round(lf/len(records),4)}")
    for r in records:
        print(f"  {r.packet_id}: {r.preferred_executor} claude_allowed={r.claude_fallback_allowed}")
    print(f"artifact:          {path}")

if __name__ == "__main__":
    main()
