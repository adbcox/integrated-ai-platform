"""Canonical session and job schema for the minimum substrate (Phase 2, P2-01)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class SessionRecord:
    session_id: str
    package_id: str
    package_label: str          # SUBSTRATE | LOCAL-FIRST | ESCALATION
    objective: str
    allowed_files: List[str]
    forbidden_files: List[str]
    selected_profile: Optional[str]
    selected_backend: str       # ollama | remote_api | substrate | none
    workspace_root: str
    artifact_root: str
    escalation_status: str      # NOT_ESCALATED | ESCALATED | ESCALATION_CANDIDATE
    final_outcome: Optional[str] = None   # success | failure | escalated | pending
    generated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class JobRecord:
    job_id: str
    package_id: str
    package_label: str
    objective: str
    allowed_files: List[str]
    forbidden_files: List[str]
    selected_profile: Optional[str]
    selected_backend: str
    workspace_root: str
    artifact_root: str
    escalation_status: str
    final_outcome: Optional[str] = None
    session_id: Optional[str] = None
    generated_at: Optional[str] = None
    validations_run: List[str] = field(default_factory=list)
    validation_results: dict = field(default_factory=dict)
    artifacts_produced: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
