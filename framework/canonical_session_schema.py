"""Phase 2 entry: canonical session object for a run.

Identity contract
-----------------
``session_id`` groups one or more jobs that share a single intent boundary
(e.g. one user request, one planning cycle, one bounded campaign). It must not
be used as, confused with, or substituted for any of the following sibling
identity types:

* ``job_id``             — identifies a single discrete execution unit
* ``telemetry_run_id``   — identifies a Phase 1 runtime telemetry bundle
* ``plan_id``            — identifies an execution route or orchestration plan

Observed formats:

* Descriptive slug (control-plane canonical): ``{context-prefix}-{descriptor}``
  Example: ``cp-default-local``
* Full UUID (browser-operator and direct callers): ``{uuid4}``
  Example: ``3f2504e0-4f89-11d3-9a0c-0305e82c3301``
* Legacy fallback derivation: some call sites derive a sub-session id as
  ``{parent_session_id}-{suffix}`` when scoping to a parent session
  (observed in framework/runtime_validation_pack.py).

Authoritative format contract: governance/canonical_id_spec.json
"""

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
