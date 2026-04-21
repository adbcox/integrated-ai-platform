"""Minimal artifact bundle for the minimum substrate (Phase 2, P2-01)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional

from framework.session_job_schema_v1 import SessionRecord, JobRecord


@dataclass
class ArtifactBundleV1:
    session: SessionRecord
    job: JobRecord
    tools_used: List[str]
    validations_run: List[str]
    artifacts_produced: List[str]
    escalation_status: str
    final_outcome: Optional[str] = None
    residual_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d
