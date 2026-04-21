"""CMDB-OPERATING-CONTEXT-INTEGRATION-SEAM-1: local subsystem and host operating context."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.cmdb_authority_contract import CmdbAuthorityContract, CmdbServiceRecord

# Import-time assertion
assert "service_name" in CmdbServiceRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: CmdbServiceRecord missing service_name"
assert "adapter_status" in CmdbServiceRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: CmdbServiceRecord missing adapter_status"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class SubsystemEntry:
    subsystem_name: str
    runtime_adapter: str
    adapter_active: bool
    owner: str


@dataclass(frozen=True)
class HostSlot:
    slot_name: str
    environment: str  # "local" | "ci" | "unknown"
    subsystems: tuple  # tuple of subsystem_name strings


@dataclass
class CmdbOperatingContext:
    subsystems: List[SubsystemEntry]
    host_slots: List[HostSlot]
    linked_contract_version: str
    context_complete: bool
    produced_at: str
    artifact_path: Optional[str]


def build_local_operating_context(
    *,
    contract: CmdbAuthorityContract,
) -> CmdbOperatingContext:
    subsystems: List[SubsystemEntry] = []

    for rec in contract.service_records:
        runtime_adapter = rec.runtime_binding or ("unknown" if rec.adapter_status == "unknown" else rec.service_name)
        adapter_active = rec.adapter_status == "active"
        subsystems.append(SubsystemEntry(
            subsystem_name=rec.subsystem or rec.service_name,
            runtime_adapter=runtime_adapter,
            adapter_active=adapter_active,
            owner=rec.owner,
        ))

    subsystem_names = tuple(s.subsystem_name for s in subsystems)
    default_slot = HostSlot(
        slot_name="local_dev",
        environment="local",
        subsystems=subsystem_names,
    )

    # context_complete = vacuously True if no subsystems;
    # False if any subsystem has unknown runtime_adapter or empty owner
    if subsystems:
        context_complete = all(
            s.runtime_adapter != "unknown" and s.owner != ""
            for s in subsystems
        )
    else:
        context_complete = True

    return CmdbOperatingContext(
        subsystems=subsystems,
        host_slots=[default_slot],
        linked_contract_version=contract.contract_version,
        context_complete=context_complete,
        produced_at=_iso_now(),
        artifact_path=None,
    )


def emit_cmdb_operating_context(
    ctx: CmdbOperatingContext,
    *,
    artifact_dir: Path = Path("artifacts") / "cmdb_authoritative_adoption",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "operating_context.json"
    out_path.write_text(
        json.dumps(
            {
                "context_complete": ctx.context_complete,
                "linked_contract_version": ctx.linked_contract_version,
                "produced_at": ctx.produced_at,
                "subsystems": [
                    {
                        "subsystem_name": s.subsystem_name,
                        "runtime_adapter": s.runtime_adapter,
                        "adapter_active": s.adapter_active,
                        "owner": s.owner,
                    }
                    for s in ctx.subsystems
                ],
                "host_slots": [
                    {
                        "slot_name": h.slot_name,
                        "environment": h.environment,
                        "subsystems": list(h.subsystems),
                    }
                    for h in ctx.host_slots
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    ctx.artifact_path = str(out_path)
    return str(out_path)


__all__ = [
    "SubsystemEntry",
    "HostSlot",
    "CmdbOperatingContext",
    "build_local_operating_context",
    "emit_cmdb_operating_context",
]
