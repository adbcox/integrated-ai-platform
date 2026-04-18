"""Phase 2 entry: canonical session object for a run."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CanonicalSession:
    session_id: str
    task_id: str
    repo_id: str = ""
    branch: str = ""
    requester: str = ""
    created_at: str = ""
    updated_at: str = ""
    task_class: str = ""
    objective: str = ""
    constraints: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    risk_tier: str = "standard"
    stop_conditions: list[str] = field(default_factory=list)
    selected_model_profile: str = ""
    selected_runtime: str = "local"
    critique_model: str = ""
    retry_budget: int = 0
    token_budget: int = 0
    workspace_id: str = ""
    source_mount: str = ""
    scratch_mount: str = ""
    artifact_root: str = ""
    network_policy: str = "disabled"
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    permission_decisions: list[dict[str, Any]] = field(default_factory=list)
    patch_sets: list[dict[str, Any]] = field(default_factory=list)
    command_results: list[dict[str, Any]] = field(default_factory=list)
    test_results: list[dict[str, Any]] = field(default_factory=list)
    benchmark_linkage: dict[str, Any] = field(default_factory=dict)
    promotion_linkage: dict[str, Any] = field(default_factory=dict)
    escalation_history: list[dict[str, Any]] = field(default_factory=list)
    final_outcome: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = ["CanonicalSession"]
