"""RealTelemetryIngestionV1: ingest real produced artifacts into a telemetry summary."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from framework.persistent_execution_ledger_v1 import PersistentExecutionLedgerV1


@dataclass
class TelemetryIngestionResultV1:
    ledger_entries_seen: int
    real_artifacts_seen: int
    synthetic_only: bool
    telemetry_complete: bool
    evidence_gaps: List[str]
    ingested_at: str = field(
        default_factory=lambda: __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat()
    )
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ledger_entries_seen": self.ledger_entries_seen,
            "real_artifacts_seen": self.real_artifacts_seen,
            "synthetic_only": self.synthetic_only,
            "telemetry_complete": self.telemetry_complete,
            "evidence_gaps": self.evidence_gaps,
            "ingested_at": self.ingested_at,
            "detail": self.detail,
        }


class RealTelemetryIngestionV1:
    """Ingest real produced artifacts from the persistent ledger and artifact paths."""

    # Artifact paths produced by prior packages
    KNOWN_ARTIFACT_PATHS = [
        Path("artifacts/substrate/phase7_promotion_pack_check.json"),
        Path("artifacts/substrate/phase5_closeout_pack_check.json"),
        Path("artifacts/substrate/phase4_uplift_pack_check.json"),
        Path("artifacts/substrate/phase3_mvp_pack_check.json"),
    ]

    def ingest(
        self,
        ledger: PersistentExecutionLedgerV1,
        local_artifact_paths: Optional[List[Path]] = None,
        repo_root: Optional[Path] = None,
    ) -> TelemetryIngestionResultV1:
        evidence_gaps: List[str] = []
        base = repo_root or Path(".")

        # 1. Count ledger entries
        entries = ledger.load_records()
        ledger_count = len(entries)
        if ledger_count == 0:
            evidence_gaps.append("ledger: no entries found in persistent execution ledger")

        # 2. Scan real artifact paths
        candidate_paths = list(local_artifact_paths or []) + [
            base / p for p in self.KNOWN_ARTIFACT_PATHS
        ]
        seen_artifacts: List[str] = []
        for path in candidate_paths:
            if Path(path).exists():
                seen_artifacts.append(str(path))
        real_artifacts_seen = len(seen_artifacts)

        if real_artifacts_seen == 0:
            evidence_gaps.append("no real artifact files found at known paths")

        # 3. Determine if evidence is synthetic-only
        # Synthetic-only if all ledger entries use synthetic run IDs (contain "p7-" prefix)
        synthetic_only = True
        if entries:
            non_synthetic = [e for e in entries if not e.run_id.startswith(("p7-", "r0", "r1", "r2", "r3"))]
            # Ledger has entries — even synthetic entries are real persisted evidence
            synthetic_only = len(non_synthetic) == 0

        # 4. Telemetry is complete if we have ledger entries AND at least one real artifact
        telemetry_complete = ledger_count > 0 and real_artifacts_seen > 0

        detail: Dict[str, Any] = {
            "ledger_entries_seen": ledger_count,
            "real_artifacts_seen": real_artifacts_seen,
            "seen_artifact_paths": seen_artifacts,
            "executor_breakdown": {},
        }
        for e in entries:
            detail["executor_breakdown"][e.executor] = (
                detail["executor_breakdown"].get(e.executor, 0) + 1
            )

        return TelemetryIngestionResultV1(
            ledger_entries_seen=ledger_count,
            real_artifacts_seen=real_artifacts_seen,
            synthetic_only=synthetic_only,
            telemetry_complete=telemetry_complete,
            evidence_gaps=evidence_gaps,
            detail=detail,
        )
