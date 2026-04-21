#!/usr/bin/env python3
"""LACE2-P1-EXPANSION-TRANCHE-SELECTOR-SEAM-1: freeze LACE2 feature-block tranche via RM-GOV-003 scoring."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from roadmap_governance.planner_service import _collect_shared_touch_surfaces

assert callable(_collect_shared_touch_surfaces), "INTERFACE MISMATCH: _collect_shared_touch_surfaces not callable"

LACE1_CLOSEOUT = REPO_ROOT / "artifacts" / "expansion" / "LACE1" / "LACE1_closeout.json"
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE2"

_CANDIDATE_BLOCKS = (
    {
        "block_id": "FB-LIVE-RETRIEVAL-WIRING",
        "description": "Wire RepoUnderstandingSubstrate and RetrievalEnrichmentSubstrate into live bounded proof path",
        "item_ids": ["RM-GOV-001", "RM-GOV-003"],
        "base_score": 0.80,
        "packets": ["P2"],
    },
    {
        "block_id": "FB-LIVE-DECOMP-HANDOFF-PROOF",
        "description": "End-to-end TaskDecompositionSubstrate → PlannerExecutorHandoff proof on real repo files",
        "item_ids": ["RM-GOV-002", "RM-GOV-003"],
        "base_score": 0.75,
        "packets": ["P3"],
    },
    {
        "block_id": "FB-LIVE-REPAIR-TRACE-REPLAY-PROOF",
        "description": "Drive RepairPolicyGate, ExecutionTraceEnricher, ReplayGate on real bounded proof records",
        "item_ids": ["RM-GOV-001", "RM-GOV-002"],
        "base_score": 0.72,
        "packets": ["P4", "P5", "P6"],
    },
    {
        "block_id": "FB-REAL-FILE-BENCHMARK",
        "description": "Real-file benchmark pack and runner with actual tmp-file writes and verification",
        "item_ids": ["RM-GOV-001", "RM-GOV-002", "RM-GOV-003"],
        "base_score": 0.70,
        "packets": ["P7", "P8", "P9"],
    },
    {
        "block_id": "FB-EVIDENCE-RATIFICATION",
        "description": "Regime comparator, failure miner, autonomy proof ratifier, mini-tranche selection, closeout",
        "item_ids": ["RM-GOV-002", "RM-GOV-003"],
        "base_score": 0.65,
        "packets": ["P10", "P11", "P12", "P13", "P14", "P15"],
    },
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    if not LACE1_CLOSEOUT.exists():
        print(f"ERROR: LACE1_closeout.json not found at {LACE1_CLOSEOUT}", file=sys.stderr)
        sys.exit(1)

    lace1 = json.loads(LACE1_CLOSEOUT.read_text(encoding="utf-8"))
    lace1_upstream_verdict = lace1.get("campaign_verdict", "unknown")
    lace1_selected_package = lace1.get("selected_expansion_package", "unknown")

    scored_blocks = []
    for block in _CANDIDATE_BLOCKS:
        surfaces = _collect_shared_touch_surfaces(list(block["item_ids"]))
        shared_touch_count = len(surfaces)
        final_score = round(block["base_score"] + 0.05 * shared_touch_count, 4)
        scored_blocks.append({
            "block_id": block["block_id"],
            "description": block["description"],
            "item_ids": block["item_ids"],
            "base_score": block["base_score"],
            "shared_touch_surfaces": surfaces,
            "shared_touch_count": shared_touch_count,
            "final_score": final_score,
            "packets": block["packets"],
        })

    scored_blocks.sort(key=lambda x: (x["shared_touch_count"], x["final_score"]), reverse=True)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    out = ARTIFACT_DIR / "tranche_selection.json"
    payload = {
        "campaign_id": "LACE2",
        "tranche_id": "LACE2-TRANCHE-1",
        "lace1_upstream_verdict": lace1_upstream_verdict,
        "upstream_selected_mini_tranche": lace1_selected_package,
        "selected_blocks": scored_blocks,
        "scoring_method": "rm_gov_003_shared_touch_count",
        "total_blocks": len(scored_blocks),
        "selected_at": _now(),
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"tranche_selection emitted: {out}")
    print(f"  lace1_upstream_verdict: {lace1_upstream_verdict}")
    for b in scored_blocks:
        print(f"  {b['block_id']}: shared_touch={b['shared_touch_count']}, final_score={b['final_score']}")


if __name__ == "__main__":
    main()
