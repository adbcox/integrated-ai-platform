"""RM-GOV-TERMINAL-CLOSEOUT-SEAM-1: emit committed closeout artifact for RM-GOV-001/002/003."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class RmGovCloseoutEntry:
    item_id: str
    decision: str                        # "complete" | "partial" | "deferred"
    complete_vs_resolved: str            # "complete" | "resolved_not_complete" | "deferred"
    evidenced_subclaims: List[str]
    unevidenced_subclaims: List[str]
    evidence_summary: str
    blocker_summary: Optional[str]       # None only if complete
    decided_at: str


@dataclass
class RmGovTerminalCloseout:
    closeout_id: str
    campaign_id: str
    items: List[RmGovCloseoutEntry]
    overall_status: str  # "all_complete" | "mixed" | "all_deferred"
    closed_at: str
    artifact_path: Optional[str]


_COMPLETE_VS_RESOLVED = {
    "complete": "complete",
    "partial": "resolved_not_complete",
    "deferred": "deferred",
}

_EVIDENCE_SUMMARIES = {
    "RM-GOV-001": (
        "roadmap_to_development_tracking: docs/roadmap/items/*.yaml has last_execution_commit "
        "field but all values null — schema exists, links absent. "
        "cmdb_linkage: framework/cmdb_authority_boundary.py, cmdb_authority_contract.py, "
        "cmdb_authoritative_promotion_ratifier.py present and importable. "
        "standardized_metrics: framework/run_metrics_schema.py RunMetrics dataclass "
        "registered in framework/schema_registry.py. "
        "enforced_naming: bin/preflight_normalization_guard.sh + Makefile target. "
        "impact_transparency: CmdbTerminalDecision.matrix_impact field in "
        "framework/cmdb_terminal_authoritative_reratifier.py."
    ),
    "RM-GOV-002": (
        "integrity_review_capability: bin/rgc.py integrity run backed by "
        "roadmap_governance/integrity.py run_integrity_review(). "
        "naming_consistency_checks: roadmap_governance/integrity.py VALID_PRIORITIES, "
        "VALID_ITEM_TYPES, VALID_CATEGORIES frozensets enforced. "
        "duplicate_detection: near-duplicate title detection via difflib + "
        "duplicate_id findings during sync. "
        "mismatch_synchronization_hygiene: bin/governance_reconcile.py cross-references "
        "canonical_roadmap.json, current_phase.json, phase_gate_status.json. "
        "recurrence: 25+ timestamped artifacts in artifacts/governance/integrity/ "
        "across dates 20260420 and 20260421."
    ),
    "RM-GOV-003": (
        "grouped_feature_block_planning: bin/rgc.py planner refresh backed by "
        "roadmap_governance/planner_service.py run_planner_refresh(); "
        "system capability, not conversation habit. "
        "package_grouping_outputs_machine_readable: PKG-*.json artifacts in "
        "artifacts/governance/packages/ with package_id and members array. "
        "shared_touch_loe_optimization: docs/roadmap/items/*.yaml has "
        "shared_touch_surfaces metadata but no computed LOE output in planner — "
        "planner scores by priority/CMDB/findings, not shared-touch aggregation. "
        "planner_outputs_reusable: FeatureBlockPackage consumed by "
        "roadmap_governance/metrics_service.py and router.py."
    ),
}

_BLOCKER_SUMMARIES = {
    "RM-GOV-001": (
        "roadmap_to_development_tracking unresolved: all last_execution_commit fields "
        "in docs/roadmap/items/*.yaml are null. Closing requires populating commit SHAs "
        "or campaign refs in each executed item's YAML file."
    ),
    "RM-GOV-003": (
        "shared_touch_loe_optimization unresolved: roadmap_governance/planner_service.py "
        "does not compute shared-touch or LOE aggregation as a structured output field. "
        "Closing requires adding shared-touch grouping logic to the planner service."
    ),
}


class RmGovTerminalCloseoutEmitter:
    """Converts P6 promotion decision into a terminal closeout record."""

    def close(self, *, promotion_decision: dict) -> RmGovTerminalCloseout:
        items_data = promotion_decision.get("items", {})
        entries: List[RmGovCloseoutEntry] = []

        for item_id in ("RM-GOV-001", "RM-GOV-002", "RM-GOV-003"):
            item = items_data.get(item_id, {})
            decision = item.get("decision", "deferred")
            cvr = _COMPLETE_VS_RESOLVED.get(decision, "deferred")

            subclaims = item.get("subclaims", [])
            evidenced = [s["subclaim_name"] for s in subclaims if s.get("evidenced")]
            unevidenced = [s["subclaim_name"] for s in subclaims if not s.get("evidenced")]

            blocker = None if decision == "complete" else _BLOCKER_SUMMARIES.get(item_id, "")

            entries.append(RmGovCloseoutEntry(
                item_id=item_id,
                decision=decision,
                complete_vs_resolved=cvr,
                evidenced_subclaims=evidenced,
                unevidenced_subclaims=unevidenced,
                evidence_summary=_EVIDENCE_SUMMARIES.get(item_id, ""),
                blocker_summary=blocker,
                decided_at=item.get("decided_at", _iso_now()),
            ))

        all_decisions = [e.decision for e in entries]
        if all(d == "complete" for d in all_decisions):
            overall = "all_complete"
        elif all(d == "deferred" for d in all_decisions):
            overall = "all_deferred"
        else:
            overall = "mixed"

        return RmGovTerminalCloseout(
            closeout_id="RM-GOV-TERMINAL-CLOSEOUT-SEAM-1",
            campaign_id="RM-GOV-VERIFICATION-CLOSEOUT-1",
            items=entries,
            overall_status=overall,
            closed_at=_iso_now(),
            artifact_path=None,
        )


def emit_rm_gov_terminal_closeout(
    closeout: RmGovTerminalCloseout,
    *,
    artifact_dir: Path = Path("governance"),
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "rm_gov_closeout.json"
    out_path.write_text(
        json.dumps(
            {
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
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    closeout.artifact_path = str(out_path)
    return str(out_path)


__all__ = [
    "RmGovCloseoutEntry",
    "RmGovTerminalCloseout",
    "RmGovTerminalCloseoutEmitter",
    "emit_rm_gov_terminal_closeout",
]
