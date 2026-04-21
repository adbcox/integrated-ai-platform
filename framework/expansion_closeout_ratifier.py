"""ExpansionCloseoutRatifier — terminal evidence record for LAEC1.

Six components: aider adapter seam, codex defer seam, cmdb authority pilot,
cmdb integration gate, first-wave branches, second-wave branches.
EXPANSION_COMPLETE when all six present; EXPANSION_PARTIAL otherwise.

Inspection gate — all six surfaces confirmed importable:
  AiderRuntimeAdapter: ok
  CodexDeferArtifact: ok
  CmdbAuthorityRecord: ok
  CmdbGateDecision: ok
  FIRST_WAVE_MANIFEST.branch_count: 3
  SECOND_WAVE_MANIFEST.branch_count: 2

NO adapter execution code in this module.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.aider_runtime_adapter import AiderRuntimeAdapter as _AiderRuntimeAdapter  # noqa: F401
from framework.codex_defer_adapter import CodexDeferArtifact as _CodexDeferArtifact  # noqa: F401
from framework.cmdb_authority_pilot import CmdbAuthorityRecord as _CmdbAuthorityRecord  # noqa: F401
from framework.cmdb_integration_gate import CmdbGateDecision as _CmdbGateDecision  # noqa: F401
from framework.domain_branch_first_wave import FIRST_WAVE_MANIFEST as _FIRST_WAVE_MANIFEST  # noqa: F401
from framework.domain_branch_second_wave import SECOND_WAVE_MANIFEST as _SECOND_WAVE_MANIFEST  # noqa: F401

assert hasattr(_AiderRuntimeAdapter, "run"), "INTERFACE MISMATCH: AiderRuntimeAdapter.run"
assert hasattr(_CodexDeferArtifact, "__dataclass_fields__"), "INTERFACE MISMATCH: CodexDeferArtifact"
assert hasattr(_CmdbAuthorityRecord, "__dataclass_fields__"), "INTERFACE MISMATCH: CmdbAuthorityRecord"
assert hasattr(_CmdbGateDecision, "__dataclass_fields__"), "INTERFACE MISMATCH: CmdbGateDecision"
assert _FIRST_WAVE_MANIFEST.branch_count == 3, "INTERFACE MISMATCH: FIRST_WAVE_MANIFEST.branch_count"
assert _SECOND_WAVE_MANIFEST.branch_count == 2, "INTERFACE MISMATCH: SECOND_WAVE_MANIFEST.branch_count"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "expansion_closeout"

EXPANSION_COMPLETE = "expansion_complete"
EXPANSION_PARTIAL = "expansion_partial"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ExpansionCloseoutComponent:
    name: str
    present: bool
    summary: str

    def to_dict(self) -> dict:
        return {"name": self.name, "present": self.present, "summary": self.summary}


@dataclass
class ExpansionCloseoutArtifact:
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


def ratify_expansion_closeout(
    *,
    aider_adapter_present: Optional[object] = None,
    codex_defer_present: Optional[object] = None,
    cmdb_authority_present: Optional[_CmdbAuthorityRecord] = None,
    cmdb_gate_present: Optional[_CmdbGateDecision] = None,
    first_wave_present: Optional[object] = None,
    second_wave_present: Optional[object] = None,
    campaign_id: str = "LOCAL-AUTONOMY-EXPANSION-CLOSEOUT-CAMPAIGN-1",
    packet_count: int = 12,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> ExpansionCloseoutArtifact:
    components = [
        ExpansionCloseoutComponent(
            name="aider_adapter_seam",
            present=aider_adapter_present is not None,
            summary="AiderRuntimeAdapter seam present" if aider_adapter_present is not None else "not provided",
        ),
        ExpansionCloseoutComponent(
            name="codex_defer_seam",
            present=codex_defer_present is not None,
            summary="CodexDeferArtifact seam present" if codex_defer_present is not None else "not provided",
        ),
        ExpansionCloseoutComponent(
            name="cmdb_authority_pilot",
            present=cmdb_authority_present is not None,
            summary=(
                f"phase={cmdb_authority_present.current_phase}"
                if cmdb_authority_present is not None else "not provided"
            ),
        ),
        ExpansionCloseoutComponent(
            name="cmdb_integration_gate",
            present=cmdb_gate_present is not None,
            summary=(
                f"result={cmdb_gate_present.result}"
                if cmdb_gate_present is not None else "not provided"
            ),
        ),
        ExpansionCloseoutComponent(
            name="first_wave_branches",
            present=first_wave_present is not None,
            summary=(
                f"branches={first_wave_present.branch_count}"  # type: ignore[union-attr]
                if first_wave_present is not None else "not provided"
            ),
        ),
        ExpansionCloseoutComponent(
            name="second_wave_branches",
            present=second_wave_present is not None,
            summary=(
                f"branches={second_wave_present.branch_count}"  # type: ignore[union-attr]
                if second_wave_present is not None else "not provided"
            ),
        ),
    ]

    all_present = all(c.present for c in components)
    decision = EXPANSION_COMPLETE if all_present else EXPANSION_PARTIAL

    notes = (
        f"Terminal record for {campaign_id}. "
        f"Packets executed: {packet_count}. "
        "Expansion seam surfaces available for live execution. "
        "No live adapter execution in this campaign."
    )

    artifact = ExpansionCloseoutArtifact(
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
        out_path = out_dir / "LAEC1_expansion_closeout.json"
        out_path.write_text(
            json.dumps(artifact.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        artifact.artifact_path = str(out_path)

    return artifact


__all__ = [
    "EXPANSION_COMPLETE",
    "EXPANSION_PARTIAL",
    "ExpansionCloseoutComponent",
    "ExpansionCloseoutArtifact",
    "ratify_expansion_closeout",
]
