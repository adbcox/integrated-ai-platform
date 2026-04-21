#!/usr/bin/env python3
"""LEDT-P1: Freeze LEDT transition feature-block tranche via RM-GOV-003 scoring."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roadmap_governance.planner_service import _collect_shared_touch_surfaces

import inspect
_sig = str(inspect.signature(_collect_shared_touch_surfaces))
assert "item_ids" in _sig, f"INTERFACE MISMATCH: expected item_ids in signature, got {_sig}"

LACE2_CLOSEOUT = "artifacts/expansion/LACE2/LACE2_closeout.json"
OUTPUT = "artifacts/expansion/LEDT/tranche_selection.json"

TRANSITION_BLOCKS = [
    {
        "block_id": "FB-EXEC-ELIGIBILITY-AND-PREFLIGHT",
        "description": "Typed eligibility contract and preflight evaluator for local execution readiness",
        "base_score": 0.92,
        "touch_surfaces": ["local_exec_eligibility", "preflight_evaluator", "disqualifier_model"],
    },
    {
        "block_id": "FB-ROUTE-DECISION-AND-FALLBACK-GATE",
        "description": "Typed route decision surface (local/fallback/hard_stop) and fallback justification model",
        "base_score": 0.91,
        "touch_surfaces": ["exec_route_decision", "fallback_justification", "fallback_gate"],
    },
    {
        "block_id": "FB-PACKET-ROUTING-METADATA-AND-RECEIPT",
        "description": "Packet routing metadata defaulting to local_first and local run receipt model",
        "base_score": 0.89,
        "touch_surfaces": ["packet_routing_metadata", "local_run_receipt", "routing_policy"],
    },
    {
        "block_id": "FB-PLANNER-PREFERENCE-SCHEMA",
        "description": "Planner preference schema defaulting to local_first with explicit Claude conditions",
        "base_score": 0.87,
        "touch_surfaces": ["planner_preference", "claude_condition_model"],
    },
    {
        "block_id": "FB-AUDIT-PROOF-AND-RATIFICATION",
        "description": "Fallback audit surface, local-first proof harness, transition ratification, and closeout",
        "base_score": 0.90,
        "touch_surfaces": ["fallback_audit", "local_first_proof", "transition_ratifier", "closeout"],
    },
]


def score_blocks(blocks):
    scored = []
    for block in blocks:
        shared_count = len(_collect_shared_touch_surfaces([block["block_id"]]))
        final_score = round(block["base_score"] + 0.05 * shared_count, 4)
        scored.append({
            "block_id": block["block_id"],
            "description": block["description"],
            "base_score": block["base_score"],
            "shared_touch_count": shared_count,
            "final_score": final_score,
        })
    return sorted(scored, key=lambda x: x["final_score"], reverse=True)


def main():
    if not os.path.exists(LACE2_CLOSEOUT):
        raise SystemExit(f"HARD STOP: {LACE2_CLOSEOUT} not found")

    with open(LACE2_CLOSEOUT) as f:
        lace2_closeout = json.load(f)

    verdict = lace2_closeout.get("campaign_verdict")
    if verdict != "lace2_campaign_complete":
        raise SystemExit(f"HARD STOP: lace2 campaign_verdict={verdict!r}, expected lace2_campaign_complete")

    scored_blocks = score_blocks(TRANSITION_BLOCKS)

    tranche_selection = {
        "campaign_id": "LEDT",
        "tranche_id": "LEDT-TRANCHE-1",
        "lace2_upstream_verdict": verdict,
        "selected_blocks": scored_blocks,
        "scoring_method": "rm_gov_003_shared_touch_count",
        "selected_at": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(tranche_selection, f, indent=2)

    print(f"tranche_id:         LEDT-TRANCHE-1")
    print(f"lace2_verdict:      {verdict}")
    print(f"blocks_selected:    {len(scored_blocks)}")
    for b in scored_blocks:
        print(f"  {b['block_id']}: {b['final_score']}")
    print(f"artifact:           {OUTPUT}")


if __name__ == "__main__":
    main()
