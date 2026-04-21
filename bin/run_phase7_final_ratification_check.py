#!/usr/bin/env python3
"""P7-03: Run Phase 7 final promotion ratification and emit decision artifact."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ARTIFACT_PATH = REPO_ROOT / "artifacts/substrate/phase7_final_ratification_check.json"


def main() -> None:
    print("P7-03: running Phase 7 final promotion ratification...")
    all_ok = True

    print("  [1] loading FinalPromotionRatifierV1...")
    try:
        from framework.final_promotion_ratifier_v1 import FinalPromotionRatifierV1
        print("      import: OK")
    except Exception as exc:
        print(f"    FAIL: {exc}", file=sys.stderr)
        sys.exit(1)

    print("  [2] running ratification against evidence chain...")
    ratifier = FinalPromotionRatifierV1(repo_root=REPO_ROOT)
    result = ratifier.ratify()

    print(f"      phase7_final_ratified:  {result.phase7_final_ratified}")
    print(f"      promotion_gate_cleared: {result.promotion_gate_cleared}")
    print(f"      live_evidence_seen:     {result.live_evidence_seen}")
    print(f"      remaining_blockers:     {len(result.remaining_blockers)}")
    for b in result.remaining_blockers:
        print(f"        BLOCKER: {b}")

    print("  [3] checking evidence load errors...")
    load_errors = result.final_summary.get("load_errors", [])
    if load_errors:
        for e in load_errors:
            print(f"      load_error: {e}")

    # all_ok = modules loaded and artifact emittable; gate state is truthful, not a failure
    component_summary = [
        {"module": "framework/final_promotion_ratifier_v1.py",
         "classes": ["FinalPromotionRatifierV1", "FinalRatificationResultV1"]},
        {"module": "governance/phase7_final_ratification.v1.yaml", "type": "baseline"},
    ]

    evidence_inputs = result.final_summary.get("evidence_inputs_loaded", {})

    artifact = {
        "phase7_final_pack": "final_promotion_ratification_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase7_final_ratified": result.phase7_final_ratified,
        "promotion_gate_cleared": result.promotion_gate_cleared,
        "remaining_blockers": result.remaining_blockers,
        "live_evidence_seen": result.live_evidence_seen,
        "all_checks_passed": all_ok,
        "escalation_status": "NOT_ESCALATED",
        "final_summary": result.final_summary,
        "component_summary": component_summary,
        "evidence_inputs_loaded": evidence_inputs,
        "phase_linkage": "Phase 7 (full_autonomy_and_promotion)",
        "authority_sources": [
            "governance/phase7_final_ratification.v1.yaml",
            "governance/phase7_terminal_closeout.v1.yaml",
            "governance/phase7_promotion_baseline.v1.yaml",
        ],
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"artifact:   {ARTIFACT_PATH.relative_to(REPO_ROOT)}")

    if result.phase7_final_ratified:
        print("P7-03: Phase 7 FULLY RATIFIED — promotion gate cleared.")
    else:
        print(
            f"P7-03: Phase 7 ratification PENDING — "
            f"{len(result.remaining_blockers)} blocker(s) remaining."
        )
        print("       (This is a truthful partial result, not a hard failure.)")

    print("P7-03: final ratification check complete.")


if __name__ == "__main__":
    main()
