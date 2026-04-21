"""RM-GOV-TERMINAL-CLOSEOUT-RERATIFIER-SEAM-1: update governance/rm_gov_closeout.json to all_complete."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

_CLOSEOUT_PATH = REPO_ROOT / "governance" / "rm_gov_closeout.json"


def _load_verifier(name: str):
    path = REPO_ROOT / "bin" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _evidence_dict(verifier_result: dict) -> dict:
    subclaims_raw = verifier_result.get("subclaims", {})
    return {
        "subclaims": {
            k: {"evidenced": v.get("evidenced", False), "evidence_source": v.get("evidence_source")}
            for k, v in subclaims_raw.items()
        }
    }


def _verifier_subclaim_list(verifier_result: dict) -> list[dict]:
    """Convert verifier subclaims to the list format used by closeout emitter."""
    return [
        {"subclaim_name": k, "evidenced": v.get("evidenced", False)}
        for k, v in verifier_result.get("subclaims", {}).items()
    ]


def run_closeout_reratification() -> dict:
    v001 = _load_verifier("run_rm_gov_001_verifier").run()
    v002 = _load_verifier("run_rm_gov_002_verifier").run()
    v003 = _load_verifier("run_rm_gov_003_verifier").run()

    from framework.rm_gov_promotion_ratifier import RmGovPromotionRatifier
    from framework.rm_gov_terminal_closeout import (
        RmGovTerminalCloseoutEmitter,
        emit_rm_gov_terminal_closeout,
    )

    ratifier = RmGovPromotionRatifier()
    decision = ratifier.ratify(
        evidence_001=_evidence_dict(v001),
        evidence_002=_evidence_dict(v002),
        evidence_003=_evidence_dict(v003),
    )

    # Build promotion_decision dict in the format closeout emitter expects
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    promotion_decision = {
        "items": {
            "RM-GOV-001": {
                "item_id": "RM-GOV-001",
                "decision": decision.rm_gov_001.decision,
                "subclaims": _verifier_subclaim_list(v001),
                "decided_at": now_iso,
            },
            "RM-GOV-002": {
                "item_id": "RM-GOV-002",
                "decision": decision.rm_gov_002.decision,
                "subclaims": _verifier_subclaim_list(v002),
                "decided_at": now_iso,
            },
            "RM-GOV-003": {
                "item_id": "RM-GOV-003",
                "decision": decision.rm_gov_003.decision,
                "subclaims": _verifier_subclaim_list(v003),
                "decided_at": now_iso,
            },
        }
    }

    emitter = RmGovTerminalCloseoutEmitter()
    closeout = emitter.close(promotion_decision=promotion_decision)

    # Update campaign_id to reflect this is the closeout reratification
    closeout.campaign_id = "RM-GOV-CLOSEOUT-GAPS-1"

    # Write to governance/ (the canonical closeout location)
    art_dir = REPO_ROOT / "governance"
    art_dir.mkdir(parents=True, exist_ok=True)
    out_path = art_dir / "rm_gov_closeout.json"

    from datetime import datetime, timezone as tz
    out_data = {
        "closeout_id": closeout.closeout_id,
        "campaign_id": closeout.campaign_id,
        "items": [
            {
                "item_id": e.item_id,
                "decision": e.decision,
                "complete_vs_resolved": e.complete_vs_resolved,
                "evidenced_subclaims": e.evidenced_subclaims,
                "unevidenced_subclaims": e.unevidenced_subclaims,
                "evidence_summary": e.evidence_summary,
                "blocker_summary": e.blocker_summary,
                "decided_at": e.decided_at,
            }
            for e in closeout.items
        ],
        "overall_status": closeout.overall_status,
        "closed_at": closeout.closed_at,
    }
    out_path.write_text(json.dumps(out_data, indent=2), encoding="utf-8")

    return {
        "reratification_id": "RM-GOV-TERMINAL-CLOSEOUT-RERATIFIER-SEAM-1",
        "closeout_path": str(out_path),
        "overall_status": closeout.overall_status,
        "items": {
            e.item_id: {
                "decision": e.decision,
                "complete_vs_resolved": e.complete_vs_resolved,
                "unevidenced_subclaims": e.unevidenced_subclaims,
            }
            for e in closeout.items
        },
        "all_complete": closeout.overall_status == "all_complete",
    }


if __name__ == "__main__":
    result = run_closeout_reratification()
    print(json.dumps(result, indent=2))
