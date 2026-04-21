#!/usr/bin/env python3
"""LACE2-P12: Ratify real local autonomy proof from LACE2 real-file evidence."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace2_autonomy_proof_ratifier import Lace2AutonomyProofRatifier

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE2"


def main() -> None:
    ratifier = Lace2AutonomyProofRatifier()
    record = ratifier.ratify()
    path = ratifier.emit(record, ARTIFACT_DIR)
    print(f"ratification_id:  {record.ratification_id}")
    print(f"criteria_passed:  {record.criteria_passed}/{record.criteria_total}")
    print(f"verdict:          {record.verdict}")
    print(f"limitations:      {len(record.limitations)}")
    print(f"artifact:         {path}")


if __name__ == "__main__":
    main()
