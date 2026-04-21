"""Typed permission decision model for the minimum substrate (Phase 2, P2-01)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Decision(Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


@dataclass
class PermissionDecisionV1:
    tool_name: str
    target_scope: str
    decision: Decision
    rationale: str

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "target_scope": self.target_scope,
            "decision": self.decision.value,
            "rationale": self.rationale,
        }
