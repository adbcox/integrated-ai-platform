#!/usr/bin/env python3
"""LACE1-P15: Ratify LACE1 campaign closeout and emit LACE1_closeout.json."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.lace1_benchmark_runner import Lace1BenchmarkRunner
from framework.failure_pattern_miner import FailurePatternMiner
from framework.autonomy_uplift_ratifier import AutonomyUpliftRatifier
from framework.grouped_package_expansion_selector import GroupedPackageExpansionSelector
from framework.lace1_expansion_closeout_ratifier import Lace1ExpansionCloseoutRatifier

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE1"
RAG4_USAGE = REPO_ROOT / "artifacts" / "stage_rag4" / "usage.jsonl"


def main() -> None:
    bench = Lace1BenchmarkRunner().run()
    fp = FailurePatternMiner().mine(bench, rag4_usage_path=RAG4_USAGE)
    uplift = AutonomyUpliftRatifier().ratify(bench, fp)
    selection = GroupedPackageExpansionSelector().select()

    ratifier = Lace1ExpansionCloseoutRatifier()
    closeout = ratifier.ratify(uplift, selection, packets_completed=15)
    path = ratifier.emit(closeout, ARTIFACT_DIR)

    print(f"campaign_id:              {closeout.campaign_id}")
    print(f"campaign_verdict:         {closeout.campaign_verdict}")
    print(f"packets_completed:        {closeout.packets_completed}/{closeout.packets_expected}")
    print(f"uplift_verdict:           {closeout.uplift_verdict}")
    print(f"selected_expansion_pkg:   {closeout.selected_expansion_package}")
    print(f"known_limitations:        {len(closeout.known_limitations)}")
    print(f"artifact:                 {path}")


if __name__ == "__main__":
    main()
