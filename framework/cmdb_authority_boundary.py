"""CMDB-AUTHORITY-BOUNDARY-SEAM-1: non-overlapping authority domain definitions."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class AuthorityDomain:
    domain_name: str
    owns: List[str]
    does_not_own: List[str]
    source_of_truth_path: Optional[str]


PROMOTION_AUTHORITY = AuthorityDomain(
    domain_name="promotion_release",
    owns=["promotion_manifest", "release_gate", "campaign_ratification"],
    does_not_own=["service_inventory", "runtime_contract", "subsystem_mapping"],
    source_of_truth_path="config/promotion_manifest.json",
)

RUNTIME_AUTHORITY = AuthorityDomain(
    domain_name="architecture_runtime",
    owns=["runtime_contract", "worker_schema", "job_schema", "executor_routing"],
    does_not_own=["service_inventory", "promotion_gate", "cmdb_records"],
    source_of_truth_path="governance/runtime_contract_version.json",
)

CMDB_AUTHORITY = AuthorityDomain(
    domain_name="service_inventory",
    owns=["service_records", "subsystem_mapping", "host_slots", "adapter_status"],
    does_not_own=["promotion_gate", "release_decision", "worker_schema"],
    source_of_truth_path=None,
)

ALL_AUTHORITIES: List[AuthorityDomain] = [
    PROMOTION_AUTHORITY,
    RUNTIME_AUTHORITY,
    CMDB_AUTHORITY,
]


def validate_boundary_non_overlap() -> List[str]:
    """Return list of overlap violations; empty list means no overlaps."""
    violations = []
    domains = ALL_AUTHORITIES
    for i, a in enumerate(domains):
        for j, b in enumerate(domains):
            if i >= j:
                continue
            overlap = set(a.owns) & set(b.owns)
            if overlap:
                violations.append(
                    f"{a.domain_name} and {b.domain_name} both own: {sorted(overlap)}"
                )
    return violations


def emit_authority_boundary(
    artifact_dir: Path = Path("artifacts") / "cmdb_authoritative_adoption",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "authority_boundary.json"
    out_path.write_text(
        json.dumps(
            {
                "domains": [
                    {
                        "domain_name": d.domain_name,
                        "owns": d.owns,
                        "does_not_own": d.does_not_own,
                        "source_of_truth_path": d.source_of_truth_path,
                    }
                    for d in ALL_AUTHORITIES
                ],
                "overlap_violations": validate_boundary_non_overlap(),
                "emitted_at": _iso_now(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(out_path)


__all__ = [
    "AuthorityDomain",
    "PROMOTION_AUTHORITY",
    "RUNTIME_AUTHORITY",
    "CMDB_AUTHORITY",
    "ALL_AUTHORITIES",
    "validate_boundary_non_overlap",
    "emit_authority_boundary",
]
