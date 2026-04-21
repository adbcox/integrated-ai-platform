"""CMDB-AUTHORITY-CONTRACT-SEAM-1: typed local CMDB authority contract."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from framework.cmdb_authority_boundary import CMDB_AUTHORITY

# Import-time assertion: verify authority boundary is correctly defined
assert CMDB_AUTHORITY.domain_name == "service_inventory", (
    f"INTERFACE MISMATCH: CMDB_AUTHORITY.domain_name must be 'service_inventory', got {CMDB_AUTHORITY.domain_name!r}"
)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class CmdbServiceRecord:
    service_name: str
    subsystem: str
    owner: str
    adapter_status: str  # "active" | "inactive" | "unknown"
    runtime_binding: Optional[str]


@dataclass(frozen=True)
class CmdbOwnershipBoundary:
    boundary_name: str
    owned_by: str
    resource_types: List[str]
    non_overlapping_with: List[str]


@dataclass(frozen=True)
class CmdbAuthorityContract:
    contract_version: str
    authority_domain: str  # must equal "service_inventory"
    owned_resource_types: List[str]
    service_records: tuple  # tuple of CmdbServiceRecord
    ownership_boundaries: tuple  # tuple of CmdbOwnershipBoundary
    established_at: str


def build_cmdb_authority_contract(
    service_records: tuple = (),
    ownership_boundaries: tuple = (),
) -> CmdbAuthorityContract:
    return CmdbAuthorityContract(
        contract_version="1.0",
        authority_domain=CMDB_AUTHORITY.domain_name,
        owned_resource_types=list(CMDB_AUTHORITY.owns),
        service_records=tuple(service_records),
        ownership_boundaries=tuple(ownership_boundaries),
        established_at=_iso_now(),
    )


def emit_cmdb_authority_contract(
    contract: CmdbAuthorityContract,
    *,
    artifact_dir: Path = Path("artifacts") / "cmdb_authoritative_adoption",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "authority_contract.json"
    out_path.write_text(
        json.dumps(
            {
                "contract_version": contract.contract_version,
                "authority_domain": contract.authority_domain,
                "owned_resource_types": contract.owned_resource_types,
                "established_at": contract.established_at,
                "service_records": [
                    {
                        "service_name": r.service_name,
                        "subsystem": r.subsystem,
                        "owner": r.owner,
                        "adapter_status": r.adapter_status,
                        "runtime_binding": r.runtime_binding,
                    }
                    for r in contract.service_records
                ],
                "ownership_boundaries": [
                    {
                        "boundary_name": b.boundary_name,
                        "owned_by": b.owned_by,
                        "resource_types": b.resource_types,
                        "non_overlapping_with": b.non_overlapping_with,
                    }
                    for b in contract.ownership_boundaries
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(out_path)


__all__ = [
    "CmdbServiceRecord",
    "CmdbOwnershipBoundary",
    "CmdbAuthorityContract",
    "build_cmdb_authority_contract",
    "emit_cmdb_authority_contract",
]
