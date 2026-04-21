"""RM-GOV-PROMOTION-RERATIFIER-SEAM-1: rerun verifiers and confirm complete/complete/complete."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _load_verifier(name: str):
    path = REPO_ROOT / "bin" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _evidence_dict(verifier_result: dict) -> dict:
    """Convert verifier output into the dict format expected by RmGovPromotionRatifier."""
    subclaims_raw = verifier_result.get("subclaims", {})
    subclaims_for_ratifier = {}
    for k, v in subclaims_raw.items():
        subclaims_for_ratifier[k] = {
            "evidenced": v.get("evidenced", False),
            "evidence_source": v.get("evidence_source"),
        }
    return {"subclaims": subclaims_for_ratifier}


def run_reratification() -> dict:
    v001 = _load_verifier("run_rm_gov_001_verifier").run()
    v002 = _load_verifier("run_rm_gov_002_verifier").run()
    v003 = _load_verifier("run_rm_gov_003_verifier").run()

    from framework.rm_gov_promotion_ratifier import RmGovPromotionRatifier

    ratifier = RmGovPromotionRatifier()
    decision = ratifier.ratify(
        evidence_001=_evidence_dict(v001),
        evidence_002=_evidence_dict(v002),
        evidence_003=_evidence_dict(v003),
    )

    items_summary = {
        "RM-GOV-001": {
            "verifier_verdict": v001.get("provisional_verdict"),
            "ratifier_decision": decision.rm_gov_001.decision,
            "evidenced_count": decision.rm_gov_001.evidenced_count,
            "total_subclaims": decision.rm_gov_001.total_subclaims,
            "blocking": decision.rm_gov_001.blocking_subclaims,
        },
        "RM-GOV-002": {
            "verifier_verdict": v002.get("provisional_verdict"),
            "ratifier_decision": decision.rm_gov_002.decision,
            "evidenced_count": decision.rm_gov_002.evidenced_count,
            "total_subclaims": decision.rm_gov_002.total_subclaims,
            "blocking": decision.rm_gov_002.blocking_subclaims,
        },
        "RM-GOV-003": {
            "verifier_verdict": v003.get("provisional_verdict"),
            "ratifier_decision": decision.rm_gov_003.decision,
            "evidenced_count": decision.rm_gov_003.evidenced_count,
            "total_subclaims": decision.rm_gov_003.total_subclaims,
            "blocking": decision.rm_gov_003.blocking_subclaims,
        },
    }

    all_complete = all(
        v["ratifier_decision"] == "complete" for v in items_summary.values()
    )

    return {
        "reratification_id": "RM-GOV-PROMOTION-RERATIFIER-SEAM-1",
        "items": items_summary,
        "all_complete": all_complete,
        "overall_status": "all_complete" if all_complete else "mixed",
    }


if __name__ == "__main__":
    result = run_reratification()
    print(json.dumps(result, indent=2))
