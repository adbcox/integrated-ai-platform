"""Bounded developer task shape for the Phase 3 developer-assistant MVP (P3-01)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class DeveloperTaskV1:
    task_id: str
    objective: str
    task_kind: str              # inspect | patch | validate | benchmark
    target_paths: List[str]
    validation_sequence: List[str]
    retry_budget: int = 1
    final_outcome: Optional[str] = None   # success | failure | escalated | pending
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
