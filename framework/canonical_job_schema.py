"""Phase 2 entry: canonical job object derived from a session.

Identity contract
-----------------
``job_id`` is the authoritative identity of a single discrete execution unit
(one scheduled or dispatched job lifecycle). It must not be used as, confused
with, or substituted for any of the following sibling identity types:

* ``session_id``         — groups one or more jobs sharing an intent boundary
* ``telemetry_run_id``   — identifies a Phase 1 runtime telemetry bundle
* ``plan_id``            — identifies an execution route or orchestration plan

Observed canonical format: ``job-{12-char-lowercase-hex}``
Example:                    ``job-5c5d1529af6c``
Generation:                 ``f"job-{uuid4().hex[:12]}"``  (see framework/job_schema.py)

Authoritative format contract: governance/canonical_id_spec.json
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from framework.canonical_session_schema import CanonicalSession


@dataclass
class CanonicalJob:
    job_id: str
    session_id: str
    task_class: str
    objective: str = ""
    constraints: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    risk_tier: str = "standard"
    stop_conditions: list[str] = field(default_factory=list)
    selected_model_profile: str = ""
    selected_runtime: str = "local"
    workspace_id: str = ""
    artifact_root: str = ""
    retry_budget: int = 0
    token_budget: int = 0
    status: str = "planned"
    final_outcome: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_session(cls, session: CanonicalSession, job_id: str) -> "CanonicalJob":
        return cls(
            job_id=job_id,
            session_id=session.session_id,
            task_class=session.task_class,
            objective=session.objective,
            constraints=list(session.constraints),
            allowed_tools=list(session.allowed_tools),
            risk_tier=session.risk_tier,
            stop_conditions=list(session.stop_conditions),
            selected_model_profile=session.selected_model_profile,
            selected_runtime=session.selected_runtime,
            workspace_id=session.workspace_id,
            artifact_root=session.artifact_root,
            retry_budget=session.retry_budget,
            token_budget=session.token_budget,
            status="planned",
            final_outcome="",
        )


__all__ = ["CanonicalJob"]
