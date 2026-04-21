#!/usr/bin/env python3
"""LACE2-P11: Mine real LACE2 failure patterns across surfaces."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.real_run_failure_miner import RealRunFailureMiner

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE2"


def main() -> None:
    miner = RealRunFailureMiner()
    record = miner.mine()
    path = miner.emit(record, ARTIFACT_DIR)

    # emit canonical campaign name
    canonical = ARTIFACT_DIR / "real_run_failure_patterns.json"
    canonical.write_text(Path(path).read_text(encoding="utf-8"), encoding="utf-8")

    print(f"miner_id:             {record.miner_id}")
    print(f"benchmark_failures:   {record.benchmark_failures}")
    print(f"repair_mismatches:    {record.repair_mismatches}")
    print(f"replay_not_replayable:{record.replay_not_replayable}")
    print(f"total_failures:       {record.total_failures}")
    print(f"artifact:             {canonical}")


if __name__ == "__main__":
    main()
