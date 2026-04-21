#!/usr/bin/env python3
"""LACE1-P13: Select next expansion package using RM-GOV-003 shared-touch scoring."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.grouped_package_expansion_selector import GroupedPackageExpansionSelector

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE1"


def main() -> None:
    selector = GroupedPackageExpansionSelector()
    record = selector.select()
    path = selector.emit(record, ARTIFACT_DIR)

    print(f"selected_package_id: {record.selected_package_id}")
    print(f"scoring_method:      {record.scoring_method}")
    print(f"artifact:            {path}")
    print("\nRanked candidates:")
    for c in record.candidates:
        marker = " <-- SELECTED" if c.package_id == record.selected_package_id else ""
        print(f"  {c.package_id}: shared_touch={c.shared_touch_count}, final_score={c.final_score}{marker}")


if __name__ == "__main__":
    main()
