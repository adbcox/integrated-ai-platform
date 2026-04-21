"""RM-GOV-PROMOTION-RATIFIER-SEAM-1: ratify complete/partial/deferred for RM-GOV-001/002/003."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class RmGovSubclaimResult:
    subclaim_name: str
    evidenced: bool
    evidence_source: Optional[str]


@dataclass
class RmGovItemDecision:
    item_id: str
    decision: str  # "complete" | "partial" | "deferred"
    evidenced_count: int
    total_subclaims: int
    subclaims: List[RmGovSubclaimResult]
    blocking_subclaims: List[str]
    decided_at: str
    artifact_path: Optional[str]


@dataclass
class RmGovPromotionDecision:
    rm_gov_001: RmGovItemDecision
    rm_gov_002: RmGovItemDecision
    rm_gov_003: RmGovItemDecision
    decided_at: str
    artifact_path: Optional[str]


def _decide_item(
    item_id: str,
    evidence: dict,
    *,
    cap_false_subclaim: Optional[str] = None,
    deferred_if_both_false: Optional[tuple] = None,
) -> RmGovItemDecision:
    subclaims_raw = evidence.get("subclaims", {})
    subclaims = [
        RmGovSubclaimResult(
            subclaim_name=k,
            evidenced=v.get("evidenced", False),
            evidence_source=v.get("evidence_source"),
        )
        for k, v in subclaims_raw.items()
    ]
    total = len(subclaims)
    evidenced_count = sum(1 for s in subclaims if s.evidenced)
    blocking = [s.subclaim_name for s in subclaims if not s.evidenced]

    if evidenced_count == total:
        decision = "complete"
    elif deferred_if_both_false and all(
        not subclaims_raw.get(k, {}).get("evidenced", False)
        for k in deferred_if_both_false
    ):
        decision = "deferred"
    elif evidenced_count == 0:
        decision = "deferred"
    else:
        decision = "partial"

    # Cap: specific subclaim must be true for complete (only if the subclaim is present)
    if cap_false_subclaim and cap_false_subclaim in subclaims_raw:
        if not subclaims_raw[cap_false_subclaim].get("evidenced", False):
            if decision == "complete":
                decision = "partial"

    return RmGovItemDecision(
        item_id=item_id,
        decision=decision,
        evidenced_count=evidenced_count,
        total_subclaims=total,
        subclaims=subclaims,
        blocking_subclaims=blocking if decision != "complete" else [],
        decided_at=_iso_now(),
        artifact_path=None,
    )


class RmGovPromotionRatifier:
    """Converts P2-P4 evidence artifacts into explicit decisions for RM-GOV-001/002/003."""

    def ratify(
        self,
        *,
        evidence_001: dict,
        evidence_002: dict,
        evidence_003: dict,
    ) -> RmGovPromotionDecision:
        item_001 = _decide_item(
            "RM-GOV-001",
            evidence_001,
        )
        item_002 = _decide_item(
            "RM-GOV-002",
            evidence_002,
            cap_false_subclaim="recurrence",  # RM-GOV-002 cannot be complete if recurrence false
        )
        item_003 = _decide_item(
            "RM-GOV-003",
            evidence_003,
            cap_false_subclaim="grouped_feature_block_planning",
            deferred_if_both_false=("grouped_feature_block_planning", "shared_touch_loe_optimization"),
        )

        return RmGovPromotionDecision(
            rm_gov_001=item_001,
            rm_gov_002=item_002,
            rm_gov_003=item_003,
            decided_at=_iso_now(),
            artifact_path=None,
        )


def emit_rm_gov_promotion_decision(
    decision: RmGovPromotionDecision,
    *,
    artifact_dir: Path = Path("artifacts") / "rm_gov_verification",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "rm_gov_promotion_decision.json"

    def _item_dict(item: RmGovItemDecision) -> dict:
        return {
            "item_id": item.item_id,
            "decision": item.decision,
            "evidenced_count": item.evidenced_count,
            "total_subclaims": item.total_subclaims,
            "blocking_subclaims": item.blocking_subclaims,
            "subclaims": [
                {
                    "subclaim_name": s.subclaim_name,
                    "evidenced": s.evidenced,
                    "evidence_source": s.evidence_source,
                }
                for s in item.subclaims
            ],
            "decided_at": item.decided_at,
        }

    out_path.write_text(
        json.dumps(
            {
                "rm_gov_001_decision": decision.rm_gov_001.decision,
                "rm_gov_002_decision": decision.rm_gov_002.decision,
                "rm_gov_003_decision": decision.rm_gov_003.decision,
                "items": {
                    "RM-GOV-001": _item_dict(decision.rm_gov_001),
                    "RM-GOV-002": _item_dict(decision.rm_gov_002),
                    "RM-GOV-003": _item_dict(decision.rm_gov_003),
                },
                "decided_at": decision.decided_at,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    decision.artifact_path = str(out_path)
    return str(out_path)


__all__ = [
    "RmGovSubclaimResult",
    "RmGovItemDecision",
    "RmGovPromotionDecision",
    "RmGovPromotionRatifier",
    "emit_rm_gov_promotion_decision",
]
