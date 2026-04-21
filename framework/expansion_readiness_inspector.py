"""ExpansionReadinessInspector — machine-readable expansion gate for LAEC1.

Inspects consumed evidence surfaces and emits ExpansionReadinessReport
capturing per-item readiness status. Missing inputs become 'unknown' items.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.readiness_ratifier import RatificationArtifact
from framework.adapter_campaign_pre_authorizer import PreAuthorizationArtifact
from framework.first_pass_metric import FirstPassReport

assert hasattr(RatificationArtifact, "__dataclass_fields__"), "INTERFACE MISMATCH: RatificationArtifact"
assert hasattr(PreAuthorizationArtifact, "__dataclass_fields__"), "INTERFACE MISMATCH: PreAuthorizationArtifact"
assert hasattr(FirstPassReport, "__dataclass_fields__"), "INTERFACE MISMATCH: FirstPassReport"

_POST_LARAC1_MODULES = [
    "framework/search_aware_inspect.py",
    "framework/listdir_inspect_helper.py",
    "framework/diff_result_packager.py",
    "framework/bounded_result_publisher.py",
]

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "expansion_readiness"

READINESS_EXPANSION_READY = "expansion_ready"
READINESS_EXPANSION_PARTIAL = "expansion_partial"
READINESS_EXPANSION_BLOCKED = "expansion_blocked"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ExpansionReadinessItem:
    name: str
    status: str  # "present", "missing", "unknown", "blocked"
    detail: str

    def to_dict(self) -> dict:
        return {"name": self.name, "status": self.status, "detail": self.detail}


@dataclass
class ExpansionReadinessReport:
    overall_status: str
    items: list
    inspected_at: str
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "overall_status": self.overall_status,
            "inspected_at": self.inspected_at,
            "artifact_path": self.artifact_path,
            "items": [i.to_dict() for i in self.items],
        }


def inspect_expansion_readiness(
    *,
    ratification_artifact: Optional[RatificationArtifact] = None,
    pre_auth_artifact: Optional[PreAuthorizationArtifact] = None,
    first_pass_report: Optional[FirstPassReport] = None,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> ExpansionReadinessReport:
    items: list[ExpansionReadinessItem] = []

    # Evidence surface items
    if ratification_artifact is not None:
        items.append(ExpansionReadinessItem(
            name="ratification_artifact",
            status="present",
            detail=f"decision={ratification_artifact.decision}",
        ))
    else:
        items.append(ExpansionReadinessItem(
            name="ratification_artifact",
            status="unknown",
            detail="not provided",
        ))

    if pre_auth_artifact is not None:
        items.append(ExpansionReadinessItem(
            name="pre_auth_artifact",
            status="present",
            detail=f"decision={pre_auth_artifact.decision}",
        ))
    else:
        items.append(ExpansionReadinessItem(
            name="pre_auth_artifact",
            status="unknown",
            detail="not provided",
        ))

    if first_pass_report is not None:
        items.append(ExpansionReadinessItem(
            name="first_pass_report",
            status="present",
            detail=f"attempts={first_pass_report.overall_attempts}",
        ))
    else:
        items.append(ExpansionReadinessItem(
            name="first_pass_report",
            status="unknown",
            detail="not provided",
        ))

    # Post-LARAC1 module file existence
    for mod_path in _POST_LARAC1_MODULES:
        if Path(mod_path).exists():
            items.append(ExpansionReadinessItem(
                name=mod_path,
                status="present",
                detail="file exists on disk",
            ))
        else:
            items.append(ExpansionReadinessItem(
                name=mod_path,
                status="missing",
                detail="file not found on disk",
            ))

    # Derive overall status
    statuses = {i.status for i in items}
    if "blocked" in statuses:
        overall_status = READINESS_EXPANSION_BLOCKED
    elif "missing" in statuses or "unknown" in statuses:
        overall_status = READINESS_EXPANSION_PARTIAL
    else:
        overall_status = READINESS_EXPANSION_READY

    report = ExpansionReadinessReport(
        overall_status=overall_status,
        items=items,
        inspected_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "LAEC1_expansion_readiness.json"
        out_path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        report.artifact_path = str(out_path)

    return report


__all__ = [
    "ExpansionReadinessItem",
    "ExpansionReadinessReport",
    "READINESS_EXPANSION_READY",
    "READINESS_EXPANSION_PARTIAL",
    "READINESS_EXPANSION_BLOCKED",
    "inspect_expansion_readiness",
]
