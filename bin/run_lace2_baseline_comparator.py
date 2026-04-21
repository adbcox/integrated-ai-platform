#!/usr/bin/env python3
"""LACE2-P10: Compare LACE1 synthetic vs LACE2 real-file benchmark regimes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.benchmark_regime_comparator import BenchmarkRegimeComparator

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE2"


def main() -> None:
    cmp = BenchmarkRegimeComparator()
    record = cmp.compare()
    path = cmp.emit(record, ARTIFACT_DIR)

    # also emit canonical campaign name
    canonical = ARTIFACT_DIR / "benchmark_comparison.json"
    canonical.write_text(Path(path).read_text(encoding="utf-8"), encoding="utf-8")

    print(f"comparison_id:          {record.comparison_id}")
    print(f"lace1_kind:             {record.lace1_benchmark_kind}")
    print(f"lace2_kind:             {record.lace2_benchmark_kind}")
    print(f"regime_upgrade:         {record.regime_upgrade_confirmed}")
    print(f"artifact:               {canonical}")


if __name__ == "__main__":
    main()
