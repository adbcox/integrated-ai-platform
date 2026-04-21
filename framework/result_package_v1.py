"""Result package for the Phase 3 developer-assistant MVP (P3-01)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional

from framework.repo_intake_v1 import RepoIntakeV1
from framework.developer_task_v1 import DeveloperTaskV1


@dataclass
class ResultPackageV1:
    intake: RepoIntakeV1
    task: DeveloperTaskV1
    tools_used: List[str]
    validations_run: List[str]
    artifacts_produced: List[str]
    final_outcome: str          # success | failure | escalated
    escalation_status: str
    validation_results: dict = field(default_factory=dict)
    residual_notes: List[str] = field(default_factory=list)
    generated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
