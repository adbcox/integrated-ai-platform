"""CMDB authority pilot for LAEC1 — read-only over local governance files.

Inspection gate output:
  governance/current_phase.json keys: as_of_commit, authority_owner,
    blocked_package_classes, blocked_tactical_families, current_phase_id,
    current_phase_name, current_phase_status, generated_at,
    next_allowed_package_class, notes
  governance/canonical_roadmap.json keys: authority_owner, generated_at,
    phases, schema_version, supersedes
  governance/phase_gate_status.json keys: authority_owner, followups,
    gates, generated_at, schema_version, supersedes
  governance/runtime_contract_version.json keys: authority_owner,
    contract_version, generated_at, notes, observed_adoption_paths,
    primitives, schema_version, supersedes
  governance/next_package_class.json keys: authority_owner, baseline_commit,
    current_allowed_class, generated_at, justification, ratified_by_adr,
    schema_version, supersedes, transitions

Binding only confirmed-present keys. No governance writes.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class CmdbAuthorityRecord:
    current_phase: str
    current_phase_status: str
    next_package_class: str
    contract_version: str
    gates_summary: dict
    phases_count: int
    read_at: str


class CmdbAuthorityPilot:
    def __init__(self, governance_dir: Path = Path("governance")) -> None:
        self._governance_dir = Path(governance_dir)

    def read_authority(self) -> CmdbAuthorityRecord:
        # current_phase.json is mandatory
        cp_path = self._governance_dir / "current_phase.json"
        cp = json.loads(cp_path.read_text())  # raises FileNotFoundError if missing

        current_phase = str(cp.get("current_phase_id", "unknown"))
        current_phase_status = str(cp.get("current_phase_status", "unknown"))

        # next_package_class: prefer next_package_class.json, fall back to current_phase.json
        npc_path = self._governance_dir / "next_package_class.json"
        if npc_path.exists():
            npc = json.loads(npc_path.read_text())
            next_package_class = str(npc.get("current_allowed_class", "unknown"))
        else:
            next_package_class = str(cp.get("next_allowed_package_class", "unknown"))

        # runtime_contract_version.json — optional
        rv_path = self._governance_dir / "runtime_contract_version.json"
        contract_version = "unknown"
        if rv_path.exists():
            rv = json.loads(rv_path.read_text())
            contract_version = str(rv.get("contract_version", "unknown"))

        # phase_gate_status.json — optional
        pgs_path = self._governance_dir / "phase_gate_status.json"
        gates_summary: dict = {}
        if pgs_path.exists():
            pgs = json.loads(pgs_path.read_text())
            gates_summary = pgs if isinstance(pgs, dict) else {}

        # canonical_roadmap.json — optional
        cr_path = self._governance_dir / "canonical_roadmap.json"
        phases_count = 0
        if cr_path.exists():
            cr = json.loads(cr_path.read_text())
            phases_raw = cr.get("phases", [])
            phases_count = len(phases_raw) if isinstance(phases_raw, list) else 0

        return CmdbAuthorityRecord(
            current_phase=current_phase,
            current_phase_status=current_phase_status,
            next_package_class=next_package_class,
            contract_version=contract_version,
            gates_summary=gates_summary,
            phases_count=phases_count,
            read_at=_iso_now(),
        )


def read_cmdb_authority(governance_dir: Path = Path("governance")) -> CmdbAuthorityRecord:
    return CmdbAuthorityPilot(governance_dir=governance_dir).read_authority()


__all__ = [
    "CmdbAuthorityRecord",
    "CmdbAuthorityPilot",
    "read_cmdb_authority",
]
