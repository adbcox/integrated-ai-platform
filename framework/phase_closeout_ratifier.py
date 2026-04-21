"""PhaseCloseoutRatifier — terminal evidence record for LOCAL-AUTONOMY-RUNTIME-ADOPTION-CAMPAIGN-1.

Inspection gate output:
  PreAuthorizationArtifact, ThresholdTuningResult, FirstPassReport, RoutingAdoptionResult — all importable.
  PreAuthorizationArtifact fields: campaign_id, decision, gates, all_gates_passed,
    defer_reasons, next_steps, generated_at, artifact_path

NO adapter implementation in this module.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.adapter_campaign_pre_authorizer import PreAuthorizationArtifact
from framework.first_pass_metric import FirstPassReport
from framework.routing_config_adopter import RoutingAdoptionResult
from framework.threshold_tuner import ThresholdTuningResult

assert hasattr(PreAuthorizationArtifact, "__dataclass_fields__"), "INTERFACE MISMATCH: PreAuthorizationArtifact"
assert hasattr(ThresholdTuningResult, "__dataclass_fields__"), "INTERFACE MISMATCH: ThresholdTuningResult"
assert hasattr(FirstPassReport, "__dataclass_fields__"), "INTERFACE MISMATCH: FirstPassReport"
assert hasattr(RoutingAdoptionResult, "__dataclass_fields__"), "INTERFACE MISMATCH: RoutingAdoptionResult"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "phase_closeout"

PHASE_COMPLETE = "phase_complete"
PHASE_PARTIAL = "phase_partial"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class CloseoutComponent:
    name: str
    present: bool
    summary: str

    def to_dict(self) -> dict:
        return {"name": self.name, "present": self.present, "summary": self.summary}


@dataclass
class PhaseCloseoutArtifact:
    campaign_id: str
    decision: str
    components: list
    all_components_present: bool
    packet_count: int
    notes: str
    generated_at: str
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "campaign_id": self.campaign_id,
            "decision": self.decision,
            "all_components_present": self.all_components_present,
            "packet_count": self.packet_count,
            "notes": self.notes,
            "generated_at": self.generated_at,
            "components": [c.to_dict() for c in self.components],
        }


def ratify_phase_closeout(
    *,
    pre_auth_artifact: Optional[PreAuthorizationArtifact] = None,
    tuning_result: Optional[ThresholdTuningResult] = None,
    first_pass_report: Optional[FirstPassReport] = None,
    routing_adoption_result: Optional[RoutingAdoptionResult] = None,
    campaign_id: str = "LOCAL-AUTONOMY-RUNTIME-ADOPTION-CAMPAIGN-1",
    packet_count: int = 15,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> PhaseCloseoutArtifact:
    components = [
        CloseoutComponent(
            name="pre_authorization",
            present=pre_auth_artifact is not None,
            summary=pre_auth_artifact.decision if pre_auth_artifact else "not provided",
        ),
        CloseoutComponent(
            name="threshold_tuning",
            present=tuning_result is not None,
            summary=f"classes={tuning_result.total_classes}" if tuning_result else "not provided",
        ),
        CloseoutComponent(
            name="first_pass_metrics",
            present=first_pass_report is not None,
            summary=f"attempts={first_pass_report.overall_attempts}" if first_pass_report else "not provided",
        ),
        CloseoutComponent(
            name="routing_adoption",
            present=routing_adoption_result is not None,
            summary=f"classes_considered={routing_adoption_result.total_classes_considered}" if routing_adoption_result else "not provided",
        ),
    ]

    all_present = all(c.present for c in components)
    decision = PHASE_COMPLETE if all_present else PHASE_PARTIAL

    notes = (
        f"Terminal record for {campaign_id}. "
        f"Packets executed: {packet_count}. "
        "No adapter implementation code produced in this campaign. "
        "All seam surfaces are available for future adoption."
    )

    artifact = PhaseCloseoutArtifact(
        campaign_id=campaign_id,
        decision=decision,
        components=components,
        all_components_present=all_present,
        packet_count=packet_count,
        notes=notes,
        generated_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "LARAC1_phase_closeout.json"
        out_path.write_text(
            json.dumps(artifact.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        artifact.artifact_path = str(out_path)

    return artifact


__all__ = [
    "CloseoutComponent",
    "PhaseCloseoutArtifact",
    "PHASE_COMPLETE",
    "PHASE_PARTIAL",
    "ratify_phase_closeout",
]
