#!/usr/bin/env python3
"""LEDT-P11: Ratify LEDT transition verdict."""
from __future__ import annotations
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.ledt_transition_ratifier import LEDTTransitionRatifier
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LEDT"

def main():
    ratifier = LEDTTransitionRatifier()
    record = ratifier.ratify()
    path = ratifier.emit(record, ARTIFACT_DIR)
    print(f"ratification_id:  {record.ratification_id}")
    print(f"criteria_passed:  {record.criteria_passed}/{record.criteria_total}")
    print(f"verdict:          {record.verdict}")
    print(f"limitations:      {len(record.limitations)}")
    for c in record.criteria:
        mark = "PASS" if c.passed else "FAIL"
        print(f"  {c.criterion_id} [{mark}] {c.description}: {c.evidence[:60]}")
    print(f"artifact:         {path}")

if __name__ == "__main__":
    main()
