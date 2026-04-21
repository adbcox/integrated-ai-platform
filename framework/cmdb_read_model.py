"""CMDB-READ-MODEL-COMPLETION-SEAM-1: typed CMDB read model over authority contract."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.cmdb_authority_contract import CmdbAuthorityContract

# Import-time assertions
assert "contract_version" in CmdbAuthorityContract.__dataclass_fields__, \
    "INTERFACE MISMATCH: CmdbAuthorityContract missing contract_version"
assert "authority_domain" in CmdbAuthorityContract.__dataclass_fields__, \
    "INTERFACE MISMATCH: CmdbAuthorityContract missing authority_domain"
assert "service_records" in CmdbAuthorityContract.__dataclass_fields__, \
    "INTERFACE MISMATCH: CmdbAuthorityContract missing service_records"
assert "owned_resource_types" in CmdbAuthorityContract.__dataclass_fields__, \
    "INTERFACE MISMATCH: CmdbAuthorityContract missing owned_resource_types"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class CmdbReadModelEntry:
    entry_name: str
    resource_type: str
    readable: bool
    stable: bool
    detail: str


@dataclass
class CmdbReadModelOutput:
    entries: List[CmdbReadModelEntry]
    total_entries: int
    readable_count: int
    stable_count: int
    read_model_complete: bool
    produced_at: str
    artifact_path: Optional[str]


class CmdbReadModel:
    """Builds typed read model entries from a CmdbAuthorityContract."""

    def build(self, *, contract: CmdbAuthorityContract) -> CmdbReadModelOutput:
        entries: List[CmdbReadModelEntry] = []

        # One entry per owned resource type (local/structural = always readable+stable)
        for resource_type in contract.owned_resource_types:
            entries.append(CmdbReadModelEntry(
                entry_name=resource_type,
                resource_type=resource_type,
                readable=True,
                stable=True,
                detail="local repo-native resource type",
            ))

        # One entry per service record adapter_status
        for rec in contract.service_records:
            readable = rec.adapter_status != "unknown"
            entries.append(CmdbReadModelEntry(
                entry_name=f"{rec.service_name}:adapter_status",
                resource_type="adapter_status",
                readable=readable,
                stable=readable,
                detail=f"adapter_status={rec.adapter_status!r}",
            ))

        readable_count = sum(1 for e in entries if e.readable)
        stable_count = sum(1 for e in entries if e.stable)
        total_entries = len(entries)
        read_model_complete = (
            total_entries == 0 or (readable_count == total_entries and stable_count == total_entries)
        )

        return CmdbReadModelOutput(
            entries=entries,
            total_entries=total_entries,
            readable_count=readable_count,
            stable_count=stable_count,
            read_model_complete=read_model_complete,
            produced_at=_iso_now(),
            artifact_path=None,
        )


def emit_cmdb_read_model(
    output: CmdbReadModelOutput,
    *,
    artifact_dir: Path = Path("artifacts") / "cmdb_authoritative_adoption",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "read_model_output.json"
    out_path.write_text(
        json.dumps(
            {
                "read_model_complete": output.read_model_complete,
                "total_entries": output.total_entries,
                "readable_count": output.readable_count,
                "stable_count": output.stable_count,
                "produced_at": output.produced_at,
                "entries": [
                    {
                        "entry_name": e.entry_name,
                        "resource_type": e.resource_type,
                        "readable": e.readable,
                        "stable": e.stable,
                        "detail": e.detail,
                    }
                    for e in output.entries
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    output.artifact_path = str(out_path)
    return str(out_path)


__all__ = [
    "CmdbReadModelEntry",
    "CmdbReadModelOutput",
    "CmdbReadModel",
    "emit_cmdb_read_model",
]
