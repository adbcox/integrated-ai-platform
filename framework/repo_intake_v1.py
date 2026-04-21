"""Repo intake surface for the Phase 3 developer-assistant MVP (P3-01)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class RepoIntakeV1:
    repo_root: str
    task_id: str
    package_id: str
    package_label: str          # SUBSTRATE | LOCAL-FIRST | ESCALATION
    objective: str
    allowed_files: List[str]
    forbidden_files: List[str]
    session_id: Optional[str] = None
    generated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
