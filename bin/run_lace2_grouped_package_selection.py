#!/usr/bin/env python3
"""LACE2-P13: Score LACE2 mini-tranche candidates and select one winner."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace2_grouped_package_selector import Lace2GroupedPackageSelector

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE2"


def main() -> None:
    selector = Lace2GroupedPackageSelector()
    record = selector.select()
    path = selector.emit(record, ARTIFACT_DIR)
    print(f"selection_id:      {record.selection_id}")
    print(f"selected_tranche:  {record.selected_tranche}")
    print(f"lace2_verdict:     {record.lace2_verdict}")
    print(f"total_failures:    {record.total_failures}")
    for c in record.candidates:
        marker = " <-- WINNER" if c.tranche_id == record.selected_tranche else ""
        print(f"  {c.tranche_id}: {c.final_score}{marker}")
    print(f"artifact:          {path}")


if __name__ == "__main__":
    main()
